#!/usr/bin/env python3
"""Root-register and spacing regression over repeated progressions and MIDI edges."""
import argparse
import json
from pathlib import Path
import verify_midi_harmony as h


def machine():
    m=h.Machine(); u=m.uc
    def voiced(raw):
        u.mem_write(m.scratch,bytes(raw));m.call('mh_voice',0,a0=m.scratch)
        return list(u.mem_read(m.scratch,4))
    # Direct musical examples pin both audition choices independently of AUTO.
    for width,spread,want in ((0,1,[60,67,76]),(0,2,[60,76,79]),
                              (1,1,[55,60,64]),(1,2,[60,67,76])):
        m.setting(0,2);m.call('mh_voic_set',0,0)
        m.call('mh_width_set',0,width);m.call('mh_sprd_set',0,spread)
        assert voiced(m.chord(0,60))[:3]==want
        for root_mode,offset in ((1,None),(2,12),(3,24)):
            m.call('mh_root_set',0,root_mode)
            actual=set(voiced(m.chord(0,60)))-{255}
            expected=(set(want)-{60}) | ({60-offset} if offset else set())
            assert actual==expected,(width,spread,root_mode,actual,expected)
        m.call('mh_root_set',0,0)
    for track in range(8):
        m.call('mh_width_set',track,track%2)
    assert [m.call('mh_width_get',t) for t in range(8)]==[t%2 for t in range(8)]
    before=bytes(u.mem_read(m.sym['mh_width'],8))
    for track,value in ((8,1),(0xffffffff,1),(0,2),(0,0xffffffff)):
        m.call('mh_width_set',track,value)
        assert bytes(u.mem_read(m.sym['mh_width'],8))==before
    count=0
    qualities=range(8) if 'ch_current' in m.sym else range(2)
    walks=([60,62,64,65,67,69,71,72,71,69,67,65,64,62,60]*2+
           [60,65,70,63,68,61,66,71,64,69,62,67,60]*2+
           [48,60,84,36,59,60,61,60,0,1,11,12,23,24,115,116,120,126,127])
    for width in range(2):
        for spread in range(3):
            for mode in (-1,*range(7)):
                if 'ms_decode' not in m.sym and mode not in (-1,0,5):continue
                for key in range(12):
                    for quality in qualities:
                        m.setting(0,2 if 'ch_current' in m.sym else quality+2,key,max(0,mode))
                        if mode<0:u.mem_write(0x46c76df1,b'\0')
                        if 'ch_current' in m.sym:u.mem_write(m.sym['ch_current'],bytes((quality,)))
                        m.call('mh_voic_set',0,1);m.call('mh_sprd_set',0,spread)
                        m.call('mh_width_set',0,width)
                        for note in walks:
                            raw=m.chord(0,note);actual=voiced(raw)
                            pitches=sorted(set(actual)-{255}); pcs={n%12 for n in raw if n<128}
                            assert raw[0] in pitches,(width,spread,mode,key,quality,note,raw,actual)
                            assert abs(pitches[0]-raw[0])<=12,("sounded bass escaped",width,spread,raw,actual)
                            assert {n%12 for n in pitches}==pcs
                            assert len(pitches)<=4 and all(0<=n<=127 for n in pitches)
                            assert voiced(raw)==actual, ("repeated root changed",width,spread,quality,raw,actual)
                            count+=1
            print(f'  [ok] WIDTH={width} SPRD={spread}: {count} transitions checked',flush=True)
    print(f'[ok] {count} anchored AUTO transitions: repeated scales/fifths, register jumps, all keys, available qualities/scales, both widths, all spreads and MIDI boundaries',flush=True)
    return count

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('remix',nargs='?');ap.parse_args()
    count=machine()
    out=h.ROOT/'out/harmony-playability';out.mkdir(parents=True,exist_ok=True)
    (out/'receipt.json').write_text(json.dumps({'anchored_transitions':count})+'\n')
