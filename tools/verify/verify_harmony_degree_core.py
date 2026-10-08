#!/usr/bin/env python3
"""Run the real degree-bank/transition code in ColdFire memory.

Independent host assertions cover native NOTE and retained mirrors, Part key
scope, inheritance and every byte outside the authorized root/dirty writes.
This is a component gate, not the later UI/file/port acceptance gate.
"""
import json
import pathlib
import re
import subprocess
import tempfile
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import *
from verify_harmony_degree_codec import MODES

ROOT = pathlib.Path(__file__).resolve().parents[2]
BANK = 0x9b340
PAT = 0x8ed8
PART = 0x18b2
BASE = 0x400e21e0
HDSIZE = 16528


def main():
    subprocess.run(['python3', str(ROOT/'modules/harmony-degrees/generate.py'), '--check'], check=True)
    with tempfile.TemporaryDirectory(prefix='harmony-degree-core-') as tmp:
        out = pathlib.Path(tmp)
        (out/'stub.s').write_text('''
.text
.global hd_type_c,hd_source_c,hd_test_modes,hd_test_sources
.global ch_lock_table,ch_nv_bank,ch_lock_status,ch_legacy7_mask
hd_type_c:
 move.l 4(%sp),%d0
 lea hd_test_modes,%a0
 move.b (%a0,%d0.l),%d0
 andi.l #255,%d0
 rts
hd_source_c:
 move.l 4(%sp),%d0
 lea hd_test_sources,%a0
 move.b (%a0,%d0.l),%d0
 andi.l #255,%d0
 rts
.data
hd_test_modes: .space 8
hd_test_sources: .byte 0,1,2,3,4,5,6,7
.balign 4
ch_nv_bank: .long -1
ch_legacy7_mask: .long 0
ch_lock_status: .space 16
.bss
ch_lock_table: .space 131072
''')
        objects = []
        for name, source in [('codec', ROOT/'modules/harmony-degrees/codec.s'),
                             ('core', ROOT/'modules/harmony-degrees/core.s'),
                             ('storage', ROOT/'modules/harmony-degrees/storage.s'),
                             ('stub', out/'stub.s')]:
            obj = out/f'{name}.o'
            subprocess.run(['m68k-elf-as', '-mcpu=54455', '-o', str(obj), str(source)], check=True)
            objects.append(str(obj))
        subprocess.run(['m68k-elf-ld', '-Ttext=0x47000000', '-e', 'hd_reset_c',
                        '-o', str(out/'core.elf'), *objects], check=True)
        subprocess.run(['m68k-elf-objcopy', '-O', 'binary', str(out/'core.elf'), str(out/'core.bin')], check=True)
        nm = subprocess.check_output(['m68k-elf-nm', str(out/'core.elf')], text=True)
        sym = {n: int(a, 16) for a, n in re.findall(r'^([0-9a-f]+) [TtBbDd] ((?:hd|ch)_\w+)$', nm, re.M)}
        u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
        for a, n in ((0x47000000, 0x100000), (0x40000000, 0x1000000),
                     (0x10000000, 0x100000), (0x80000000, 0x10000)):
            u.mem_map(a, n)
        u.mem_write(0x47000000, (out/'core.bin').read_bytes())
        stack, done = 0x470f0000, 0x470ffff0
        reached = []
        def hook(u, pc, n, data):
            if pc == done:
                reached.append(True)
                u.emu_stop()
        u.hook_add(UC_HOOK_CODE, hook)
        def call(name, *args):
            reached.clear()
            u.reg_write(UC_M68K_REG_SR, 0x2700)
            u.reg_write(UC_M68K_REG_A7, stack)
            u.mem_write(stack, b''.join((v & 0xffffffff).to_bytes(4, 'big') for v in (done, *args)))
            u.emu_start(sym[name], 0, count=30000000)
            assert reached, (name, args, hex(u.reg_read(UC_M68K_REG_PC)))
            return u.reg_read(UC_M68K_REG_D0)
        def byte(a): return u.mem_read(a, 1)[0]
        def put(a, v): u.mem_write(a, bytes((v,)))
        def po(part): return (0x8ed80 + part*PART) if part < 4 else (0x9504a+(part-4)*PART)
        def note(b, p, t, s): return BASE+b*BANK+p*PAT+0x4900+t*0x8b0+s*32
        def base(b, part, t): return BASE+b*BANK+po(part)+0x3e2+t*32
        def key(b, part, t): return BASE+b*BANK+po(part)+0x4e2+t*36+17
        def degree(b, p, t, s): return sym['hd_banks']+b*HDSIZE+(p*8+t)*64+s
        call('hd_reset_c')
        # Nonroot native fields are deliberately nonzero, to catch broad writes.
        before = []
        for b in range(16):
            data = bytearray(b'\x55'*BANK)
            for p in range(16):
                data[p*PAT+0x8e57] = p%4
                for t in range(8):
                    for s in range(64):
                        data[p*PAT+0x4900+t*0x8b0+s*32] = (48+(s%3)*5) if s%4 == 0 else 255
            for part in range(8):
                for t in range(8):
                    data[po(part)+0x3e2+t*32] = 48
                    data[po(part)+0x4e2+t*36+17] = 2 # C minor
            u.mem_write(BASE+b*BANK, bytes(data))
            before.append(bytes(data))
            call('hd_bank_loaded_c', b)
        call('hd_mode_c', 0, 2)
        for b in range(16):
            assert bytes(u.mem_read(BASE+b*BANK, BANK)) == before[b], 'enter must not rewrite stock'
            for p in range(16):
                for s in range(64):
                    value = byte(degree(b,p,0,s))
                    assert value == (35 if s%12 == 0 else 38 if s%12 == 4 else 41) if s%4 == 0 else value == 255
                assert call('hd_degree_c', b,p,0,1) == 35 # unlocked root -> Part tonic
        # Each Part receives a different current key. Exit must use each
        # pattern's assigned Part, including saved-Part defaults separately.
        expected = [bytearray(v) for v in before]
        for b in range(16):
            for part in range(8):
                tonic = part % 4
                put(key(b,part,0), 2+2*tonic)
                expected[b][po(part)+0x4e2+17] = 2+2*tonic
                expected[b][po(part)+0x3e2] = 48+tonic
            for p in range(16):
                tonic = p%4
                for s in range(0,64,4):
                    expected[b][p*PAT+0x4900+s*32] = 48+(s%3)*5+tonic
            expected[b][0x9b332:0x9b336] = (1).to_bytes(4,'big')
        assert call('hd_resolve_c', 0,2,0,0) == 50
        call('hd_mode_c', 0, 0)
        for b in range(16):
            actual = bytes(u.mem_read(BASE+b*BANK, BANK))
            assert actual == expected[b], (b, [(i,a,e) for i,(a,e) in enumerate(zip(actual,expected[b])) if a!=e][:12])
            assert call('hd_validate_c', sym['hd_banks']+b*HDSIZE) == 1
        assert byte(0x1001614e+2*PAT+0x4900) == 50
        assert byte(0x100a4ece+2*PART+0x3e2) == 50
        assert byte(0x100ab196+2*PART+0x3e2) == 50
        # OFF D3 -> C major -> HARM is degree 2:3, not the old tonic.
        put(note(0,0,0,0), 50)
        put(key(0,0,0), 1)
        call('hd_mode_c', 0, 1)
        assert call('hd_degree_c',0,0,0,0) == 36
        assert call('hd_resolve_c',0,0,0,0) == 50
        before_degree = byte(degree(0,0,0,0))
        call('hd_mode_c',0,2)
        assert byte(degree(0,0,0,0)) == before_degree
        # Native root edit is incorporated, and recording can explicitly
        # replace a same-note degree identity captured earlier in another key.
        put(note(0,0,0,0), 53)
        assert call('hd_degree_c',0,0,0,0) == 38
        call('hd_record_c',0,0,0,0,35)
        assert call('hd_degree_c',0,0,0,0) == 35
        call('hd_edit_base_c',0,0,0,37)
        assert call('hd_degree_c',0,0,0,1) == 37
        # Source KEY is used for Follow conversion, not the receiver's KEY.
        put(sym['hd_test_sources']+1,0)
        put(key(0,0,1),24)
        assert call('hd_scale_c',0,0,1) == 0
        # Validation rejects malformed state before publication.
        addr = sym['hd_banks']
        for offset, bad in ((0,84),(8192,128),(16384,84),(16448,128),(16512,2),(16520,2)):
            old = byte(addr+offset)
            put(addr+offset,bad)
            assert call('hd_validate_c',addr) == 0, offset
            put(addr+offset,old)
        # Dense retained payload: every root lock and quality, not a sparse
        # subset. Corruption must leave BOTH live tables completely untouched.
        payload_len = 8192 + HDSIZE
        nv = 0x100f8600
        chord = sym['ch_lock_table']
        u.mem_write(chord, bytes(i%8 for i in range(8192)))
        put(sym['hd_test_modes'], 2)
        call('hd_nv_save_c',0)
        snapshot = bytes(u.mem_read(nv,32+payload_len))
        h_before = bytes(u.mem_read(sym['hd_banks'],HDSIZE))
        q_before = bytes(u.mem_read(chord,8192))
        u.mem_write(sym['hd_banks'], b'\0'*HDSIZE)
        u.mem_write(chord,b'\xff'*8192)
        assert call('hd_nv_restore_c',0) == 1
        assert bytes(u.mem_read(sym['hd_banks'],HDSIZE)) == h_before
        assert bytes(u.mem_read(chord,8192)) == q_before
        corrupt_positions = (0,4,8,12,16,24,28,32,8223,8224,16416,16480,16544,24751)
        for pos in corrupt_positions:
            broken = bytearray(snapshot)
            broken[pos] ^= 0x80
            u.mem_write(nv,bytes(broken))
            assert call('hd_nv_restore_c',0) == 0, pos
            assert bytes(u.mem_read(sym['hd_banks'],HDSIZE)) == h_before
            assert bytes(u.mem_read(chord,8192)) == q_before
        u.mem_write(nv,snapshot)
        assert call('hd_nv_restore_c',1) == 0
        # Field validation is independent of the checksum (forged valid hash).
        broken = bytearray(snapshot)
        broken[32+8192] = 84
        checksum = 0x811c9dc5
        for value in broken[32:]: checksum = ((checksum ^ value)*0x01000193)&0xffffffff
        broken[16:20] = checksum.to_bytes(4,'big')
        u.mem_write(nv,bytes(broken))
        assert call('hd_nv_restore_c',0) == 0
        print(json.dumps({'banks':16,'patterns':256,'stock_preservation':'all nonroot bytes compared',
                          'part_defaults':128,'root_locks':16384,'mirror_checks':3,
                          'inheritance_record_edits_follow_validation':'passed',
                          'retained_payload_bytes':payload_len,'corruption_rejected':len(corrupt_positions)+2,
                          'hardware_tested':False}))


if __name__ == '__main__':
    main()
