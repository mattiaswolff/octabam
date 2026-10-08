#!/usr/bin/env python3
"""Check the native Part-copy interception ABI against the actual stock copier.

The callback is an observing C ABI fixture. The stock copier and interception
instructions execute unmodified; no Elektron bytes are stored in this test.
This checks the boundary, not the later pattern-provenance adapter.
"""
import json
import pathlib
import re
import subprocess
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import *

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENTRY = 0x40020898
EXPECTED = bytes.fromhex('2f02226f0008')


def main():
    stock = (ROOT/'out/raw/section_3_MAIN_OS.bin').read_bytes()
    assert stock[ENTRY-0x40000400:ENTRY-0x40000400+6] == EXPECTED
    with tempfile.TemporaryDirectory(prefix='harmony-degree-copy-') as tmp:
        out = pathlib.Path(tmp)
        (out/'observe.s').write_text('''
.text
.global hd_part_before_c,observed_pointer,observed_value,observed_count
hd_part_before_c:
 move.l 4(%sp),%a0
 move.l %a0,observed_pointer
 move.l (%a0),%d0
 move.l %d0,observed_value
 addq.l #1,observed_count
 /* A real C callee may reuse its argument slots and volatile registers. */
 move.l #0x11223344,%d0
 move.l %d0,4(%sp)
 move.l #0x76543210,%d0
 move.l %d0,%d1
 move.l %d0,%a0
 move.l %d0,%a1
 rts
.data
observed_pointer: .long 0
observed_value: .long 0
observed_count: .long 0
''')
        objs = []
        for name, path in (('copy', ROOT/'modules/harmony-degrees/part-copy.s'), ('observe', out/'observe.s')):
            obj = out/f'{name}.o'
            subprocess.run(['m68k-elf-as', '-mcpu=54455', '-o', str(obj), str(path)], check=True)
            objs.append(str(obj))
        subprocess.run(['m68k-elf-ld', '-Ttext=0x47000000', '-e', 'hd_native_copy', '-o', str(out/'copy.elf'), *objs], check=True)
        subprocess.run(['m68k-elf-objcopy', '-O', 'binary', str(out/'copy.elf'), str(out/'copy.bin')], check=True)
        nm = subprocess.check_output(['m68k-elf-nm', str(out/'copy.elf')], text=True)
        sym = {n: int(a, 16) for a, n in re.findall(r'^([0-9a-f]+) [TtDd] ((?:hd|observed)_\w+)$', nm, re.M)}
        u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
        u.mem_map(0x40000000, 0x200000)
        u.mem_map(0x47000000, 0x100000)
        u.mem_write(0x40000400, stock)
        u.mem_write(0x47000000, (out/'copy.bin').read_bytes())
        patch = bytes.fromhex('4ef9')+sym['hd_native_copy'].to_bytes(4, 'big')
        source, dest, stack, done = 0x47020000, 0x47040000, 0x470f0000, 0x470ffff0
        reached = []
        def stop(u, pc, size, data):
            if pc == done:
                reached.append(True)
                u.emu_stop()
        u.hook_add(UC_HOOK_CODE, stop)
        regs = (UC_M68K_REG_D0, UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_D3,
                UC_M68K_REG_D4, UC_M68K_REG_D5, UC_M68K_REG_D6, UC_M68K_REG_D7,
                UC_M68K_REG_A0, UC_M68K_REG_A1, UC_M68K_REG_A2, UC_M68K_REG_A3,
                UC_M68K_REG_A4, UC_M68K_REG_A5, UC_M68K_REG_A6)
        cases = 0
        for length in (0, 1, 3, 4, 15, 16, 17, 127, 6321, 6322, 6323, 0x8ed8):
            for offset in (0, 1):
                results = []
                original = bytes((n*7+3) % 256 for n in range(length+8))
                for patched in (False, True):
                    reached.clear()
                    u.mem_write(ENTRY, patch if patched else EXPECTED)
                    u.ctl_remove_cache(ENTRY, ENTRY+6)
                    u.mem_write(source, original)
                    u.mem_write(dest, b'\xa5'*(length+8))
                    u.mem_write(sym['observed_count'], bytes(4))
                    u.mem_write(stack, b''.join(n.to_bytes(4, 'big') for n in (done, dest+offset, source+offset, length)))
                    for reg in regs:
                        u.reg_write(reg, 0x12345678)
                    u.reg_write(UC_M68K_REG_SR, 0x2000)
                    u.reg_write(UC_M68K_REG_A7, stack)
                    u.emu_start(ENTRY, 0, count=50000)
                    assert reached, (length, offset, patched)
                    actual = bytes(u.mem_read(dest, length+8))
                    expected = b'\xa5'*offset+original[offset:offset+length]+b'\xa5'*(8-offset)
                    assert actual == expected
                    assert bytes(u.mem_read(source, length+8)) == original
                    assert u.reg_read(UC_M68K_REG_A7) == stack+4
                    assert bytes(u.mem_read(stack+4, 12)) == b''.join(n.to_bytes(4, 'big') for n in (dest+offset, source+offset, length))
                    count = int.from_bytes(u.mem_read(sym['observed_count'], 4), 'big')
                    assert count == int(patched and length == 6322), (length, offset, patched, count)
                    if count:
                        assert int.from_bytes(u.mem_read(sym['observed_pointer'], 4), 'big') == dest+offset
                        assert bytes(u.mem_read(sym['observed_value'], 4)) == b'\xa5'*4, 'capture ran after overwrite'
                    results.append(([u.reg_read(reg) for reg in regs], u.reg_read(UC_M68K_REG_SR)))
                assert results[0] == results[1], (length, offset, results)
                cases += 1
        print(json.dumps({'stock_vs_intercepted_copies': cases,
                          'callback_before_overwrite_callee_argument_reuse_registers_canaries': 'passed',
                          'evidence': 'native copy boundary', 'hardware_tested': False}))


if __name__ == '__main__':
    main()
