#!/usr/bin/env python3
"""Execute linked Harmony firmware; optionally exercise full firmware on a virtual card."""
import argparse
import json
import pathlib
import re
import subprocess
import sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import toolpath
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.m68k_const import *
NV = 0x100b14e2

def raw_scale(key,mode):
    return 1+key*2+(mode==5) if mode in (0,5) else 25+key*5+(1,2,3,4,6).index(mode)

MODES = [(0,2,4,5,7,9,11),(0,2,3,5,7,9,10),(0,1,3,5,7,8,10),
         (0,2,4,6,7,9,11),(0,2,4,5,7,9,10),(0,2,3,5,7,8,10),(0,1,3,5,6,8,10)]

def symbols():
    raw = subprocess.check_output(['m68k-elf-nm', str(ROOT/'out/platform/runtime/runtime.elf')], text=True)
    return {n:int(a,16) for a,n in re.findall(r'^([0-9a-f]+) [Tt] ((?:mh|bf|ms)_\w+)$',raw,re.M)}

class Machine:
    def __init__(self):
        self.sym=symbols(); self.uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
        u=self.uc; u.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
        for a,n in [(0x40000000,0x1000000),(0x47000000,0x10000),(0x46c70000,0x20000),(0x10000000,0x200000),(0x80000000,0x10000)]:u.mem_map(a,n)
        u.mem_write(0x40000400,(ROOT/'out/mainos_bus.bin').read_bytes())
        self.base=json.loads((ROOT/'out/platform/layout.json').read_text())['base']
        u.mem_write(self.base,(ROOT/'out/platform/runtime/runtime.bin').read_bytes())
        self.stack=0x47008000;self.done=0x4700fff0;self.scratch=0x47001000
        self.stops={self.done}; self.arrival=None;self.writes=[]
        u.hook_add(UC_HOOK_CODE,self.stop)
        u.hook_add(UC_HOOK_MEM_WRITE,lambda u,a,p,n,v,x:self.writes.append((p,n)))
        if 'mh_defaults' in self.sym:self.call('mh_defaults',stop=0x40025ace)
    def stop(self,u,p,n,x):
        if p in self.stops:self.arrival=p;u.emu_stop()
    def call(self,name,d0=0,d1=0,a0=None,stop=None,regs=None):
        u=self.uc;self.stops={stop or self.done};self.arrival=None;self.writes=[]
        u.reg_write(UC_M68K_REG_SR,0x2700);u.reg_write(UC_M68K_REG_A7,self.stack)
        u.mem_write(self.stack,self.done.to_bytes(4,'big'))
        u.reg_write(UC_M68K_REG_D0,d0);u.reg_write(UC_M68K_REG_D1,d1)
        if a0 is not None:u.reg_write(UC_M68K_REG_A0,a0)
        for r,v in (regs or {}).items():u.reg_write(r,v)
        u.emu_start(self.sym[name],0,count=20000)
        assert self.arrival in self.stops,(name,hex(u.reg_read(UC_M68K_REG_PC)))
        return u.reg_read(UC_M68K_REG_D0)
    def setting(self,t,kind=0,key=0,scale=0):
        self.call('mh_set',t,kind)
        self.uc.mem_write(0x46c76df1+68*t,bytes((raw_scale(key,scale),)))
    def chord(self,t,n):
        self.uc.mem_write(self.scratch,bytes((n,11,12,13)))
        self.call('mh_generate',t,a0=self.scratch)
        return list(self.uc.mem_read(self.scratch,4))

def machine_gate():
    m=Machine();u=m.uc
    assert bytes(u.mem_read(NV,10))==bytes(9)+b'J'
    # Per-track TYPE writes leave the other tracks and adjacent Quantizer alone.
    values=[t%4 for t in range(8)]
    for t,v in enumerate(values):m.call('mh_set',t,v)
    assert [m.call('mh_get',t) for t in range(8)]==values
    for t in range(8):
        for kind in range(4):
            m.call('mh_set',t,kind)
            assert m.call('mh_get',t)==kind
            assert all(m.call('mh_get',j)==values[j] for j in range(8) if j!=t)
        m.call('mh_set',t,values[t])
    m.call('mh_defaults',stop=0x40025ace)
    for mode,degrees in enumerate(MODES):
        if "ms_decode" not in m.sym and mode not in (0,5):continue
        for key in range(12):
            valid=[n for n in range(128) if (n-key)%12 in degrees]
            for kind in (1,2,3):
                m.setting(0,kind,key,mode)
                for note in range(128):
                    root=min(valid,key=lambda n:(abs(n-note),n))
                    assert m.call('mh_quant',note,0)==root,(mode,key,note)
                    scale_notes=[n for n in range(root,160) if (n-key)%12 in degrees]
                    expected=[root]*4
                    if kind>1:
                        for slot in range(1,kind+1):
                            candidate=scale_notes[slot*2]
                            if candidate<=127:expected[slot]=candidate
                    actual=m.chord(0,note)
                    assert actual==expected,(mode,key,kind,note,actual,expected)
                    # Only scratch and bounded call stack may be written.
                    assert all(m.scratch<=a and a+n<=m.scratch+4 or m.stack-192<=a and a+n<=m.stack+4 for a,n in m.writes)
    print('  [ok] linked code: all keys and available modes x 128 pitches x NOTE/TRIAD/7TH; bounds and write guards')
    m.setting(0,0,4,5)
    assert m.chord(0,61)==[61,11,12,13]
    assert m.call('mh_quant',61,0)==61
    # Invalid battery state disables the feature, boot sanitizes it.
    u.mem_write(NV,b'\xff'*10)
    assert m.call('mh_get',0)==0
    m.call('mh_boot',stop=0x4001022a)
    assert bytes(u.mem_read(NV,10))==bytes(9)+b'J'
    if 'bf_sources' in m.sym:
        u.mem_write(m.sym['bf_sources'],bytes((0,1,2,0,0,0,0,0)))
        u.mem_write(m.sym['bf_roots'],bytes((38,255,255,255,255,255,255,255)))
        m.setting(0,0,0,0);m.setting(2,2,1,5)
        assert m.call('mh_source',2)==0
        assert m.chord(2,72)==[38,41,45,38] # D minor in inherited C major
        u.mem_write(m.sym['bf_roots'],bytes([255]*8))
        assert m.chord(2,61)==[60,64,67,60] # unknown source: own note, inherited scale
        u.mem_write(m.sym['bf_roots'],bytes((37,255,255,255,255,255,255,255)))
        assert m.chord(2,72)==[37,41,44,37] # exact chromatic root is retained
        m.setting(0,1,0,1 if 'ms_decode' in m.sym else 0)
        u.mem_write(m.sym['bf_roots'],bytes((41,255,255,255,255,255,255,255)))
        assert m.chord(2,72)==[41,45,48,41] # F major in C dorian
        u.mem_write(m.sym['bf_sources'],bytes((2,1,0,0,0,0,0,0)))
        assert m.call('mh_source',0)==0
        print('  [ok] optional Follow inheritance, chains, cycle fallback and independent TYPE')
    m.setting(0,2)
    u.mem_write(0x46c76df1,b'\0')
    assert m.chord(0,61)==[61,11,12,13], 'KEY OFF must bypass Harmony'
    print('  [ok] TYPE persistence, TYPE/KEY OFF identity, invalid state and warm-boot sanitizer')


def keyboard_gate():
    """Execute wrapper with stock sender intercepted to inspect ownership arguments.
    Full-port UART tests separately exercise the real sender and MIDI parser.
    """
    m=Machine();u=m.uc;m.setting(0,2)
    u.mem_write(0x46c76fec,bytes((64,0,0)))
    from unicorn.m68k_const import UC_M68K_REG_D2,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A2
    regs=[UC_M68K_REG_D2,UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A2]
    def key(note,velocity):
        args=[0,note,velocity,0]
        u.mem_write(m.stack,m.done.to_bytes(4,'big')+b''.join(v.to_bytes(4,'big') for v in args))
        u.reg_write(UC_M68K_REG_A7,m.stack);u.reg_write(UC_M68K_REG_SR,0x2700)
        m.stops={m.done,0x4009e9b0};pc=m.sym['mh_keyboard'];events=[]
        for _ in range(20):
            m.arrival=None;u.emu_start(pc,0,count=50000)
            assert m.arrival in m.stops
            if m.arrival==m.done:return events
            sp=u.reg_read(UC_M68K_REG_A7)
            args=[int.from_bytes(u.mem_read(sp+32+4*i,4),'big') for i in range(4)]
            events.append((args[1],args[2]))
            for i,r in enumerate(regs):u.reg_write(r,int.from_bytes(u.mem_read(sp+4*i,4),'big'))
            pc=int.from_bytes(u.mem_read(sp+28,4),'big');u.reg_write(UC_M68K_REG_A7,sp+32)
        raise AssertionError('unbounded keyboard loop')
    assert key(48,100)==[(48,100),(52,100),(55,100)]
    assert key(52,100)==[(59,100)]
    m.setting(0,3,5,5) # held notes release their original pitches after edits
    assert key(48,0)==[(48,0)]
    assert key(52,0)==[(52,0),(55,0),(59,0)]
    m.setting(0,2);u.mem_write(0x46c76fec,b'\x00') # -64 st: root out of range, other tones valid
    assert key(60,100)==[(0,100),(3,100)]
    assert key(60,0)==[(0,0),(3,0)]
    u.mem_write(0x46c76fec,b'\x40')
    m.setting(0,0)
    assert key(61,100)==[(61,100)]
    assert key(61,100)==[(61,100)] # bypass repeats retain the stock call path
    m.setting(0,2)
    assert key(61,0)==[(61,0)] # enabling Harmony must still release stock press
    assert key(48,100)==[(48,100),(52,100),(55,100)]
    m.setting(0,0)
    assert key(48,0)==[(48,0),(52,0),(55,0)]
    m.setting(0,2);u.mem_write(0x46c76df1,b'\0')
    assert key(61,100)==[(61,100)]
    m.setting(0,2)
    assert key(61,0)==[(61,0)] # KEY OFF-to-on has the same ownership rule
    print('  [ok] linked keyboard ownership: overlapping chord tones, setting changes while held, invalid-root release')


def project_parser_gate():
    m=Machine();u=m.uc
    def load(line,parse_only=False):
        u.mem_write(m.scratch,line.encode()+b'\0')
        u.mem_write(m.stack+58,int(parse_only).to_bytes(4,'big'))
        m.call('mh_load',35,stop=0x40088224,regs={UC_M68K_REG_D3:m.scratch})
    load('#MIDI_HARMONY_TYPE_V1_T8=3\r\n')
    assert m.call('mh_get',7)==3
    for line in ('#MIDI_HARMONY_TYPE_V1_T8=2x','#MIDI_HARMONY_TYPE_V1_T8=4',
                 '#MIDI_HARMONY_TYPE_V1_T8=-1','#MIDI_HARMONY_TYPE_V1_T8=',
                 '#MIDI_HARMONY_TYPE_V1_T8=0000','#MIDI_HARMONY_TYPE_V1_T9=1',
                 '#MIDI_HARMONY_TYPE_V1_T0=1','#MIDI_HARMONY_TYPE_V2_T8=1'):
        before=bytes(u.mem_read(NV,10));load(line)
        assert bytes(u.mem_read(NV,10))==before,line
    load('#MIDI_HARMONY_TYPE_V1_T8=1',parse_only=True)
    assert m.call('mh_get',7)==3
    assert [m.call('mh_get',t) for t in range(7)]==[0]*7
    print('  [ok] project parser: valid track, malformed/out-of-range comments and parse-only isolation')


def controls_gate():
    """Check the shared NOTE callback and inherited KEY control boundaries."""
    m=Machine();u=m.uc
    def args(slot,delta):
        u.mem_write(m.stack+4,slot.to_bytes(4,'big')+(delta & 0xffffffff).to_bytes(4,'big'))
    entry='bf_encoder' if 'bf_encoder' in m.sym else 'mh_note_encoder'
    # Original CHAN, BANK, PROG and SBNK must reach the untouched stock body.
    for slot in (0,1,2,4):
        args(slot,1);m.call(entry,stop=0x4003a8f0)
        assert u.reg_read(UC_M68K_REG_A7)==m.stack-16
        assert int.from_bytes(u.mem_read(m.stack+4,4),'big')==slot
    u.mem_write(0x100b14cc,b'\x01')
    for delta,want in [(1,1),(1,2),(100000,3),(-1,2),(-100000,0)]:
        args(5,delta);m.call(entry,stop=0x40036548)
        assert m.call('mh_get',1)==want
        assert m.call('mh_get',0)==0
    if 'bf_sources' in m.sym:
        u.mem_write(m.sym['bf_sources'],bytes((0,1,0,0,0,0,0,0)))
        args(5,1);m.call('mh_arp_encoder',stop=0x40079d48)
        assert u.reg_read(UC_M68K_REG_A7)==m.stack
        args(0,1);m.call('mh_arp_encoder',stop=0x4007a2f4)
        u.mem_write(0x100b14cc,b'\0')
        args(5,1);m.call('mh_arp_encoder',stop=0x4007a2f4)
    print('  [ok] NOTE controls pass through, HARM clamps per track, inherited KEY is read-only')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('remix',nargs='?',default='midi-harmony')
    a=ap.parse_args()
    machine_gate()
    keyboard_gate()
    controls_gate()
    project_parser_gate()
if __name__=='__main__':main()
