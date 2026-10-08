#!/usr/bin/env python3
"""Execute native load callsites and Harmony continuations with stubbed I/O.

The full port gate covers real bank/companion files. This gate isolates caller
identity, mask selection, stack cleanup, registers and native result branches.
"""
import struct
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import *
import verify_midi_harmony as h


def check():
    cases = 0
    sites = (
        (0x400852c8, 0x40090504, 16, 'ch_loaded_all', None),
        (0x40084d60, 0x400905d4, 16, 'ch_loaded_resume', 0xfffb),
        (0x400853d8, 0x400905d4, 28, 'ch_loaded_project', 0xffff),
        (0x40085452, 0x400905d4, 20, 'ch_loaded_bank', 0x8005),
    )
    for site, native, cleanup, entry, mask in sites:
        for result in (0, 1, 0xfffffff9):
            m = h.Machine(); u = m.uc
            assert bytes(u.mem_read(site, 6)) == b'\x4e\xb9' + struct.pack('>I', native)
            assert bytes(u.mem_read(site + 6, 6)) == b'\x4e\xf9' + struct.pack('>I', m.sym[entry])
            calls = []; banks = []
            def observe(u, address, size, data):
                if address == native:
                    sp = u.reg_read(UC_M68K_REG_A7)
                    calls.append(struct.unpack('>I', u.mem_read(sp, 4))[0])
                elif address == m.sym['ch_file_read']:
                    banks.append(u.reg_read(UC_M68K_REG_D0))
                    u.reg_write(UC_M68K_REG_D0, 0xdeadbeef)
            u.hook_add(UC_HOOK_CODE, observe)
            # Stub only the native operation and external helper effects;
            # the actual linked post-load dispatch and mask loops execute.
            for address in (native, m.sym['ch_lock_init'], m.sym['ch_file_read'], m.sym['ch_nv_save']):
                u.mem_write(address, b'\x4e\x75')
            args = struct.pack('>8I', 0x100b14f0, mask or 0, 3, 4, 5, 6, 7, 8)
            u.reg_write(UC_M68K_REG_SR, 0x2700)
            u.reg_write(UC_M68K_REG_A7, m.stack)
            u.mem_write(m.stack, args)
            u.reg_write(UC_M68K_REG_D0, result)
            u.reg_write(UC_M68K_REG_D2, 0x23456789)
            u.reg_write(UC_M68K_REG_D3, 0x3456789a)
            continuation = site + 12
            m.stops = {continuation}; m.arrival = None
            u.emu_start(site, 0, count=5000)
            assert m.arrival == continuation, (entry, hex(u.reg_read(UC_M68K_REG_PC)))
            assert calls == [site + 6], (entry, calls)
            assert banks == [b for b in range(16) if mask is None or mask & (1 << b)], (entry, banks)
            assert u.reg_read(UC_M68K_REG_A7) == m.stack + cleanup, entry
            assert bytes(u.mem_read(m.stack, len(args))) == args, entry
            assert u.reg_read(UC_M68K_REG_D0) == result, entry
            assert u.reg_read(UC_M68K_REG_D2) == 0x23456789, entry
            assert u.reg_read(UC_M68K_REG_D3) == 0x3456789a, entry
            # Execute stock's real conditional branch: Unicorn exposes lazy
            # condition flags through execution, not reliably via SR reads.
            if entry in ('ch_loaded_all', 'ch_loaded_project'):
                success, failure = continuation + 8, continuation + 2
            else:
                success, failure = continuation + 2, continuation + 4
            m.stops = {success, failure}; m.arrival = None
            u.emu_start(continuation, 0, count=10)
            assert m.arrival == (failure if result & 0x80000000 else success), entry
            cases += 1
    print(f'[ok] {cases} native load caller/continuation cases, including error results', flush=True)
    return cases


if __name__ == '__main__':
    check()
