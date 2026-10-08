#!/usr/bin/env python3
"""Execute the built Follow settings parser, resume record and UI write-through."""
from midi_machine import Machine
from unicorn import UC_HOOK_CODE
from unicorn.m68k_const import *

NV = 0x100f85e8


def packed(source=0, mode=0, fixed=3, offset=0):
    return source | mode << 4 | fixed << 5 | (offset + 2) << 9


def main():
    m = Machine(); u = m.uc; s = m.sym
    def state():
        return tuple(bytes(u.mem_read(s[n], 8)) for n in
                     ('bf_sources', 'bf_reg_modes', 'bf_reg_fixed', 'bf_reg_offsets'))
    def parse(line, dry=False):
        u.mem_write(m.scratch, line.encode() + b'\0')
        # Hook displaces the strlen argument pop. Incoming SP is four below
        # the project loader's normal frame; parse-only flag is normal SP+58.
        u.mem_write(m.stack + 62, int(dry).to_bytes(4, 'big'))
        m.call('bf_load', len(line), stop=0x400867a2,
               regs={UC_M68K_REG_D3: m.scratch})
    m.call('bf_defaults', stop=0x40025ad4)
    default = state()
    assert default == (bytes(8), bytes(8), bytes([3]*8), bytes(8))
    cases = 0
    for track in range(8):
        for mode in range(2):
            for fixed in range(11):
                for offset in range(-2, 3):
                    source = (track + 1) % 8 + 1
                    value = packed(source, mode, fixed, offset)
                    m.call('bf_reset')
                    parse(f'#MIDI_FOLLOW_V1_T{track+1}={value}\r\n')
                    assert m.call('bf_pack', track) == value
                    m.call('bf_restore')
                    assert m.call('bf_pack', track) == value
                    cases += 1
    print(f'[ok] {cases} track/mode/octave project roundtrips and CS1 restores')

    m.call('bf_defaults', stop=0x40025ad4)
    before = state(); nv = bytes(u.mem_read(NV, 24))
    invalid = ['T0=1120', 'T9=1120', 'T1=-1', 'T1=', 'T1=99999',
               'T1=4096', 'T1=1120x', 'T1=1120 ', 'T1=1121', # self-follow
               'T1=9', 'T1=352', 'T1=2560'] # source, fixed, offset bounds
    for suffix in invalid:
        parse('#MIDI_FOLLOW_V1_' + suffix)
        assert state() == before and bytes(u.mem_read(NV, 24)) == nv, suffix
    parse('#MIDI_FOLLOW_V2_T2=1137')
    parse('#MIDI_HARMONY_TYPE_V1_T1=2')
    parse('#MIDI_FOLLOW_V1_T2=1137', dry=True)
    assert state() == before and bytes(u.mem_read(NV, 24)) == nv
    # A valid chain loads in either order; an edge closing a cycle is rejected.
    for order in ((1, 2), (2, 1)):
        m.call('bf_reset')
        for track in order: parse(f'#MIDI_FOLLOW_V1_T{track+1}={packed(track)}')
        assert state()[0][:3] == bytes((0, 1, 2))
        parse(f'#MIDI_FOLLOW_V1_T1={packed(3)}')
        assert state()[0][:3] == bytes((0, 1, 2))
    print('[ok] malformed/versioned comments, parse-only isolation, chains and cycle rejection')

    # Real editor helpers must write through; restore must not retain roots.
    m.call('bf_reset')
    m.call('bf_select', 1, 1)
    m.call('bf_reg_change', 1, 0, regs={UC_M68K_REG_D2: 1})
    m.call('bf_reg_change', 1, 1, regs={UC_M68K_REG_D2: 0xffffffff})
    expected = state(); nv = bytes(u.mem_read(NV, 24))
    assert m.call('bf_pack', 1) == packed(1, 1, 3, -1)
    u.mem_write(s['bf_roots'], b'\x3c'*8)
    u.mem_write(s['bf_pitches'], b'\x3c'*8)
    m.call('bf_boot', stop=0x40010240)
    assert state() == expected
    assert bytes(u.mem_read(s['bf_roots'], 8)) == b'\xff'*8
    assert bytes(u.mem_read(s['bf_pitches'], 8)) == b'\xff'*8
    for index in range(24):
        damaged = bytearray(nv); damaged[index] ^= 1
        u.mem_write(NV, bytes(damaged))
        m.call('bf_restore')
        assert state() == default, index
    # Adjacent KITS and CHRD bytes are not part of the resume record.
    u.mem_write(NV-4, b'LEFT'); u.mem_write(NV+24, b'RGHT')
    m.call('bf_persist')
    assert u.mem_read(NV-4, 4) == b'LEFT' and u.mem_read(NV+24, 4) == b'RGHT'
    m.call('bf_defaults', stop=0x40025ad4)
    assert state() == default
    print('[ok] UI write-through, warm boot, transient-root reset, corruption rejection and bounded CS1 writes')

    # Exercise the real serializer, intercepting only libc/file operations.
    # Failed writes must take stock's error exit, not claim a successful SAVE.
    output = []; fail_at = None
    sprintf, strlen, write = 0x4700fe00, 0x4700fe10, 0x4700fe20
    def word(address): return int.from_bytes(u.mem_read(address, 4), 'big')
    def cstr(address):
        result = bytearray()
        while (b := u.mem_read(address + len(result), 1)[0]): result.append(b)
        return bytes(result)
    def io(cpu, pc, size, unused):
        if pc not in (sprintf, strlen, write): return
        sp = cpu.reg_read(UC_M68K_REG_A7)
        if pc == sprintf:
            text = cstr(word(sp+8)).decode() % (word(sp+12), word(sp+16))
            u.mem_write(word(sp+4), text.encode()+b'\0'); result = len(text)
        elif pc == strlen:
            result = len(cstr(word(sp+4)))
        else:
            text = bytes(u.mem_read(word(sp+8), word(sp+12)))
            output.append(text)
            result = 0xffffffff if len(output) == fail_at else len(text)
        cpu.reg_write(UC_M68K_REG_D0, result)
        cpu.reg_write(UC_M68K_REG_PC, word(sp))
        cpu.reg_write(UC_M68K_REG_A7, sp+4)
    hook = u.hook_add(UC_HOOK_CODE, io)
    for fail_at in (None, 1, 8):
        output.clear()
        m.call('bf_save', stop=0x40088860 if fail_at is None else 0x40089638,
               regs={UC_M68K_REG_A4:sprintf, UC_M68K_REG_A3:strlen, UC_M68K_REG_A2:write,
                     UC_M68K_REG_D2:m.scratch, UC_M68K_REG_D3:123, UC_M68K_REG_D7:765})
        assert len(output) == (fail_at or 8)
        assert u.reg_read(UC_M68K_REG_D7) == 765
        assert u.reg_read(UC_M68K_REG_A7) == m.stack
        assert output[0] == f'#MIDI_FOLLOW_V1_T1={packed()}\r\n'.encode()
    u.hook_del(hook)
    print('[ok] eight serialized settings, balanced stack and stock error exit on first/last write failure')


if __name__ == '__main__':
    main()
