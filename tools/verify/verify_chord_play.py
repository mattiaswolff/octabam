#!/usr/bin/env python3
"""CHORD PLAY development checks: linked ColdFire and actual panel events.

The port fixture is copied to out/chord-play-suite; never opens a device.
This gate does not establish physical hardware behaviour.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

import verify_midi_harmony as h
import verify_midi_harmony_port as port
from unicorn.m68k_const import UC_M68K_REG_D2, UC_M68K_REG_D3, UC_M68K_REG_A0

ROOT = h.ROOT
OUT = ROOT / 'out/chord-play-suite'


def symbols():
    raw = subprocess.check_output(['m68k-elf-nm', str(ROOT/'out/platform/runtime/runtime.elf')], text=True)
    return {n: int(a, 16) for a, n in re.findall(r'^([0-9a-f]+) [TtBb] ((?:ch|mh|bf|ms)_\w+)$', raw, re.M)}


def extra_voicings(m):
    count = 0
    for mode in range(7):
        for quality in range(8):
            m.setting(0,2,0,mode)
            m.uc.mem_write(m.sym['ch_current'],bytes((quality,)))
            size=4 if quality in (1,2,7) else 3
            for choice in range(5):
                m.call('mh_voic_set',0,choice)
                for spread in range(3):
                    m.call('mh_sprd_set',0,spread)
                    for root in (48,50,53,55,60,84,36,116,124,127):
                        raw=m.chord(0,root)
                        m.uc.mem_write(m.scratch,bytes(raw))
                        m.call('mh_voice',0,a0=m.scratch)
                        actual=list(m.uc.mem_read(m.scratch,4))
                        if raw[:size]!=sorted(set(raw[:size])):
                            assert actual==raw
                        elif choice!=1:
                            close=raw[:size]
                            if choice>=2:
                                bass=raw[min(choice-1,size-1)]
                                pcs={x%12 for x in close}
                                inversion=[n for n in range(bass,bass+12) if n%12 in pcs]
                                if max(inversion)<=127:close=inversion
                            want=h.spread_notes(close,spread) or close
                            assert actual[:size]==want,(mode,quality,choice,spread,root,actual,want)
                        else:
                            assert actual[:size]==sorted(set(actual[:size]))
                            assert {x%12 for x in actual[:size]}=={x%12 for x in raw[:size]}
                        count+=1
    m.setting(0,2,0,5)
    for root,q,want in [(48,0,'Cm'),(48,1,'Cm7'),(50,1,'Dm7b5'),(51,1,'Ebmaj7'),
                         (55,7,'G7'),(48,2,'Cm(add9)'),(50,2,'Ddim(addb9)'),
                         (48,3,'Csus2'),(50,3,'Dsusb2b5'),(53,4,'Fsus4')]:
        m.uc.mem_write(m.sym['ch_last_root'],bytes((root,)))
        m.uc.mem_write(m.sym['ch_live'],bytes((q,)))
        m.call('ch_chord_name',0)
        actual=bytes(m.uc.mem_read(m.uc.reg_read(UC_M68K_REG_A0),32)).split(b'\0')[0].decode()
        assert actual==want,(actual,want)
    print(f'[ok] {count} quality/voicing/spread/bounds cases and actual chord names',flush=True)
    return count


def root_qualities(m):
    count=0
    for scale in range(7):
        for quality in range(8):
            for voic in range(5):
                for spread in range(3):
                    for note in (0,11,12,23,24,48,60,116,127):
                        m.setting(0,2,0,scale)
                        m.uc.mem_write(m.sym['ch_current'],bytes((quality,)))
                        m.call('mh_voic_set',0,voic);m.call('mh_sprd_set',0,spread)
                        raw=m.chord(0,note);root=raw[0]
                        m.call('mh_root_set',0,0);m.uc.mem_write(m.scratch,bytes(raw))
                        m.call('mh_voice',0,a0=m.scratch)
                        full=set(m.uc.mem_read(m.scratch,4))-{255}
                        upper={n for n in full if n%12!=root%12}
                        for mode in (1,2,3):
                            m.call('mh_root_set',0,mode);m.uc.mem_write(m.scratch,bytes(raw))
                            m.call('mh_voice',0,a0=m.scratch)
                            actual=set(m.uc.mem_read(m.scratch,4))-{255}
                            bass=root-12*(mode-1)
                            wanted=upper | ({bass} if mode>1 and bass>=0 else set())
                            assert actual==wanted,(scale,quality,voic,spread,note,mode,actual,wanted)
                            assert len(actual)<=len(full)<=4
                            count+=1
    print(f'[ok] {count} CHRD/ROOT/voicing/spread/scale/bounds combinations; no extra voice',flush=True)
    return count


def machine():
    h.symbols = symbols
    m = h.Machine()
    intervals = [(0, 2, 4), (0, 2, 4, 6), (0, 2, 4, 8),
                 (0, 1, 4), (0, 3, 4), (0, 4, 7), (0, 3, 7), (0, 4, 7, 10)]
    count = 0
    for mode, degrees in enumerate(h.MODES):
        for key in range(12):
            for root in (36 + key, 60 + key, 120 + key):
                if root > 127:
                    continue
                scale = [n for n in range(root, 160) if (n-key) % 12 in degrees]
                mask = sum(1 << n for n in degrees)
                for quality, offsets in enumerate(intervals):
                    m.uc.mem_write(m.scratch, b'\xaa'*4)
                    m.call('ch_build', root, quality, a0=m.scratch,
                           regs={UC_M68K_REG_D2: mask, UC_M68K_REG_D3: key})
                    wanted = [scale[i] if quality < 5 else root+i for i in offsets]
                    wanted = [n for n in wanted if n <= 127]
                    wanted += [root] * (4-len(wanted))
                    actual = list(m.uc.mem_read(m.scratch, 4))
                    assert actual == wanted, (mode, key, root, quality, actual, wanted)
                    count += 1
    # Actual Harmony entry: explicit dominant preserves the B natural in C minor.
    m.setting(0, 2, 0, 5)
    m.uc.mem_write(m.sym['ch_current'], b'\x07')
    assert m.chord(0, 55) == [55, 59, 62, 65]
    assert m.call('mh_final', 59, 0) == 59
    m.uc.mem_write(m.sym['ch_current'], b'\x01')
    assert m.chord(0, 55) == [55, 58, 62, 65]
    assert m.call('mh_final', 59, 0) == 58
    print(f'[ok] {count} linked chord cases; explicit DOM7 preserves B natural', flush=True)
    return dict(chord_cases=count, voicing_cases=extra_voicings(m), root_quality_cases=root_qualities(m))


def playing(source):
    port.OUT = OUT
    work = port.fixture(source, 'held-variations', {0: 2}, key_raw=2)
    script = work/'play.txt'
    script.write_text('''100 key 0x31 down
150 key 0x31 up
500 key 0 down
1000 key 9 down
1500 key 12 down
1700 key 9 up
2000 key 12 up
2500 key 0 up
2800 key 3 down
3200 key 3 up
3600 quit
''')
    events = port.run(work, 'play', ['--step', '-:poke:0x80000015=1',
        '--step', '-:poke:0x460d16f3=6', '--step', '-:poke:0x100b14cc=0',
        '--live-script', script, '--lcd', work/'play.lcd'])
    port.balanced(events)
    notes = [e[2] for e in events if e[:2] == ('on', 1)]
    expected = [48,51,55, 48,51,55,58, 48,53,55, 48,51,55, 53,56,60]
    assert notes == expected, (notes, expected)
    subprocess.run([sys.executable, str(ROOT/'tools/emu/lcd_view.py'),
                    str(work/'play.lcd'), '--png', str(work/'play.png')], check=True)
    print('[ok] actual trig keys: Cm -> Cm7 -> Csus4 -> Cm -> Fm; balanced releases', flush=True)
    return dict(played=notes)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('remix', nargs='?')
    ap.add_argument('--project', type=pathlib.Path)
    args = ap.parse_args()
    result = machine()
    if args.project:
        result.update(playing(args.project))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'receipt.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
