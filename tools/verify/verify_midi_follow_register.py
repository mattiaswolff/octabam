#!/usr/bin/env python3
"""Execute Follow register policy, capture and output bytes from the linked image."""
from midi_machine import Machine
from unicorn.m68k_const import *

def main():
    m=Machine();u=m.uc;s=m.sym;lane=m.scratch+0x1000
    def edit(track,control,delta):
        m.call('bf_reg_change',track,control,regs={UC_M68K_REG_D2:delta&0xffffffff})
    for track in range(8):
        assert m.call('bf_mode_get',track)==0
        assert m.call('bf_oct_get',track)==3
    edit(1,1,1);edit(1,0,1);edit(1,1,-1)
    assert m.call('bf_oct_get',1)==0xffffffff
    edit(1,0,-1);assert m.call('bf_oct_get',1)==4
    edit(1,0,0x7fffffff);assert m.call('bf_mode_get',1)==1
    edit(1,1,0x7fffffff);assert m.call('bf_oct_get',1)==2
    edit(1,1,-0x80000000);assert m.call('bf_oct_get',1)==0xfffffffe
    edit(1,0,-0x80000000);assert m.call('bf_mode_get',1)==0
    edit(1,1,0x7fffffff);assert m.call('bf_oct_get',1)==10
    edit(1,1,-0x80000000);assert m.call('bf_oct_get',1)==0
    before=bytes(u.mem_read(s['bf_reg_modes'],24))
    edit(8,0,1);edit(0,2,1)
    assert bytes(u.mem_read(s['bf_reg_modes'],24))==before
    assert m.call('bf_register',8,0)==256
    assert m.call('bf_register',0,8)==256
    assert m.call('bf_register',0,1)==256
    u.mem_write(s['bf_sources'],bytes((0,1,2,0,0,0,0,0)))
    cases=0
    for root in range(128):
        u.mem_write(lane+0x220,bytes((root,)));u.mem_write(lane+0x22c,b'\x40')
        m.call('bf_latch',d1=0,regs={UC_M68K_REG_D7:0,UC_M68K_REG_A5:lane})
        assert u.mem_read(s['bf_pitches'],1)==bytes((root,))
        assert u.mem_read(s['bf_roots'],1)==bytes((36+root%12,))
        for mode,octaves in ((0,range(11)),(1,range(-2,3))):
            for octave in octaves:
                for receiver in (1,2): # direct and chained receiver use ultimate source
                    u.mem_write(s['bf_reg_modes']+receiver,bytes((mode,)))
                    u.mem_write(s['bf_reg_offsets' if mode else 'bf_reg_fixed']+receiver,bytes((octave&255,)))
                    base=(root if mode else root%12)+12*octave
                    assert m.call('bf_register',0,receiver)==base&0xffffffff,(root,mode,octave)
                    for tran in (-12,0,12):
                        u.mem_write(lane+0x22c,bytes((64+tran,)))
                        u.mem_write(m.scratch,b'\x3c')
                        want=base+tran;valid=0<=want<128
                        m.call('bf_note',a0=0,stop=0x4009fb86 if valid else 0x4009fd2a,regs={UC_M68K_REG_D7:receiver,UC_M68K_REG_D4:0,UC_M68K_REG_A2:m.scratch,UC_M68K_REG_A5:lane})
                        assert u.mem_read(m.scratch,1)==bytes((want if valid else 255,)),(root,mode,octave,tran)
                        assert all((m.stack-96<=a<m.stack) or a==m.scratch for a,_ in m.writes),m.writes
                        cases+=1
    if 'mh_generate' in s:
        # Both sequenced and live sources retain their harmonic root's octave.
        u.mem_write(0x46c76df1,b'\x01') # source C major inherited by receivers
        m.call('mh_set',1,1) # receiver HARM NOTE
        for root in range(128):
            m.call('mh_latch_key_root',root,regs={UC_M68K_REG_D2:0})
            assert u.mem_read(s['bf_pitches'],1)==bytes((root,))
            for mode,octaves in ((0,range(11)),(1,range(-2,3))):
                for octave in octaves:
                    u.mem_write(s['bf_reg_modes']+1,bytes((mode,)))
                    u.mem_write(s['bf_reg_offsets' if mode else 'bf_reg_fixed']+1,bytes((octave&255,)))
                    for tran in (-190,-12,0,12,190):
                        pitch=(root if mode else root%12)+12*octave+tran
                        u.mem_write(m.scratch,b'\x3c\x01\x02\x03')
                        result=m.call('mh_generate',1,tran&0xffffffff,a0=m.scratch)
                        if 0<=pitch<=127:
                            wanted=min((n for n in range(128) if n%12 in (0,2,4,5,7,9,11)),key=lambda n:(abs(n-pitch),n))
                            assert result==1 and u.mem_read(m.scratch,4)==bytes((wanted,))*4,(root,mode,octave,tran)
                        else:
                            assert result==0xffffffff,(root,mode,octave,tran,result)
        print('[ok] Harmony NOTE inherits register before TRAN/scale, signed bounds, and live absolute-root capture')
    print(f'[ok] {cases} Follow register/TRAN/bounds cases, absolute source capture, chains, independent settings and UI clamps')
if __name__=='__main__':main()
