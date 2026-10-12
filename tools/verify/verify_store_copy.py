#!/usr/bin/env python3
"""Exercise the linked STORE copy wrapper with stubbed native I/O and clients.

This proves dispatch/ABI behavior, not card I/O or client persistence.
"""
import json
import pathlib
import struct
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import toolpath  # noqa: E402,F401
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import (UC_CPU_M68K_CFV4E, UC_M68K_REG_A0,
    UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_D1,
    UC_M68K_REG_D2, UC_M68K_REG_D7, UC_M68K_REG_PC, UC_M68K_REG_SR)


def main():
    runtime = ROOT / 'out/platform/runtime'
    nm = subprocess.check_output(['m68k-elf-nm', str(runtime / 'runtime.elf')], text=True)
    symbols = {f[2]: int(f[0], 16) for f in (line.split() for line in nm.splitlines())
               if len(f) == 3}
    base = json.loads((ROOT / 'out/platform/layout.json').read_text())['base']
    data = (runtime / 'runtime.bin').read_bytes()
    u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    u.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
    mapped = base & ~4095
    u.mem_map(mapped, (base - mapped + len(data) + 4095) & ~4095)
    u.mem_write(base, data)
    u.mem_map(0x10000, 0x20000)
    u.mem_map(0x40016000, 0x1000)  # native F_COPY, intercepted below
    done, stack, dst, src = 0x10000, 0x20000, 0x23000, 0x24000
    u.mem_write(dst, b'/SET/PROJECT/bank01.strd\0')
    u.mem_write(src, b'/SET/PROJECT/bank01.work\0')
    # Read the actual linked event table; an empty table is also valid.
    table = symbols['ev_bankcopy']
    handlers = []
    for i in range(64):
        address = int.from_bytes(u.mem_read(table + 4 * i, 4), 'big')
        if not address:
            break
        handlers.append(address)
    else:
        raise AssertionError('unterminated bankcopy event table')
    native, clients = [], []
    result = 0

    def io(uc, pc, size, opaque):
        if pc != 0x40016388 and pc not in handlers:
            return
        sp = uc.reg_read(UC_M68K_REG_A7)
        ret = int.from_bytes(uc.mem_read(sp, 4), 'big')
        if pc == 0x40016388:
            native.append(struct.unpack('>3I', uc.mem_read(sp + 4, 12)))
            value = result
        else:
            clients.append((pc, uc.reg_read(UC_M68K_REG_D0),
                            uc.reg_read(UC_M68K_REG_D1), uc.reg_read(UC_M68K_REG_D2)))
            value = 0
            # STORE promises to preserve the caller despite clobbering clients.
            for reg in (*range(UC_M68K_REG_D0, UC_M68K_REG_D7 + 1),
                        *range(UC_M68K_REG_A0, UC_M68K_REG_A6 + 1)):
                uc.reg_write(reg, 0xabcddcba)
        uc.reg_write(UC_M68K_REG_D0, value & 0xffffffff)
        uc.reg_write(UC_M68K_REG_A7, sp + 4)
        uc.reg_write(UC_M68K_REG_PC, ret)

    u.hook_add(UC_HOOK_CODE, io)
    for result in (-12, -1, 0, 1):
        native.clear()
        clients.clear()
        u.reg_write(UC_M68K_REG_SR, 0x2000)
        u.reg_write(UC_M68K_REG_A7, stack)
        u.mem_write(stack, struct.pack('>4I', done, dst, src, 7))
        u.emu_start(symbols['store_fcopy'], done, count=10000)
        assert u.reg_read(UC_M68K_REG_PC) == done, 'wrapper did not return'
        assert u.reg_read(UC_M68K_REG_D0) == result & 0xffffffff
        assert native == [(dst, src, 7)], native
        expected = [(p, dst, src, 0) for p in handlers] if result >= 0 else []
        assert clients == expected, (result, clients, expected)
        assert u.reg_read(UC_M68K_REG_A7) == stack + 4
        assert bytes(u.mem_read(stack + 4, 12)) == struct.pack('>3I', dst, src, 7)
    report = dict(native_copy_results=[-12, -1, 0, 1],
                  callbacks_in_linked_table=len(handlers),
                  native_copy_once=True, failure_skips_callbacks=True,
                  callback_order_and_arguments_preserved=True, stack_balanced=True,
                  native_io_and_client_bodies='stubbed')
    (ROOT / 'out/store-copy.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
