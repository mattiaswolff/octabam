#!/usr/bin/env python3
"""Full firmware MIDI/UI/project checks. Uses a copied project and virtual CF only."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import re
import verify_midi_follow as follow
import verify_midi_harmony as harmony
ROOT=harmony.ROOT
sys.path.insert(0,str(ROOT/'tools'))
import emu_card
from hw import ot_project as otp
OUT=ROOT/'out/harmony-port-suite'


def fixture(source, name, records, arp=False, reverse=False, key_raw=1, first_note=62, tran=None, locks=None):
    work=OUT/name;work.mkdir(parents=True,exist_ok=True)
    leader=7 if reverse else 0
    follow.fixture(source,work/'project',arp=arp,leader=leader,offsets=locks)
    for p in (work/'project').glob('project.*'):
        raw=re.sub(rb'^#MIDI_HARMONY[^\r\n]*\r?\n',b'',p.read_bytes(),flags=re.M)
        raw+=b'\r\n'+b''.join(f'#MIDI_HARMONY_TYPE_V1_T{t+1}={v}\r\n'.encode() for t,v in records.items())
        p.write_bytes(raw)
    for path in (work/'project').glob('bank*.work'):
        def mutate(data):
            for part in range(8):
                base=otp.PART_BASE+part*otp.PART_STRIDE+9
                for t in range(8):
                    data[base+0x4e2+36*t+17]=key_raw if t!=1 else 4
                for t,offset in (tran or {}).items():
                    data[base+0x3e2+32*t+12]=64+offset
                if arp:
                    # T2 arpeggiates its generated chord as well as the leader.
                    at=base+0x3e2+32
                    data[at+2]=18;data[at+14]=1;data[at+15]=3
            for p in range(16):
                at=0x492e+p*0x8eec+leader*0x8b9
                if p==0:data[at+0x39+2*32]=first_note # D minor, then F and G in C major.
        otp._bank_write(work/'project',int(path.stem[4:]),mutate,guard=False)
    card,_=emu_card.stage_project(work/'project','OCTABAM','BASS',tree=work/'tree')
    (work/'card.img').write_bytes(card)
    return work


def run(work, name, extra=(), image=None, card=None):
    cmd=[str(ROOT/'out/emu/ot_emu'),'--image',str(image or ROOT/'out/mainos_bus.bin'),
         '--card',str(card or work/'card.img'),'--set','OCTABAM','--project','BASS',
         '--load-ms','90000','--mkii','--midi-out',str(work/f'{name}.midi'),
         '--card-out',str(work/f'{name}-card.img')]+list(map(str,extra))
    with (work/f'{name}.log').open('w') as f:p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    log=(work/f'{name}.log').read_text()
    assert p.returncode==0 and ('run ended REACHED' in log or 'ended on quit' in log),(name,work/f'{name}.log')
    events=follow.notes((work/f'{name}.midi').read_bytes())
    (work/f'{name}-notes.json').write_text(json.dumps(events,indent=2)+'\n')
    return events


def balanced(events):
    held=set()
    for kind,ch,n,v in events:
        key=ch,n
        if kind=='on':
            assert key not in held,('duplicate',key);held.add(key)
        else:
            assert key in held,('unmatched off',key);held.remove(key)
    assert not held,('stuck',held)


def sequence(source):
    sym=harmony.symbols();has_follow='bf_sources' in sym
    cases={}
    for arp,reverse in [(False,False),(True,False)]+([(False,True),(True,True)] if has_follow else []):
        name=('reverse-' if reverse else '')+('arp' if arp else 'chords')
        leader=7 if reverse else 0
        # Destination TYPE seventh, source TYPE triad. Different own scale on
        # follower proves it inherits C major instead of its stored C# minor.
        work=fixture(source,name,{leader:2,1:3},arp,reverse)
        extra=['--sequencer','--internal-clock','--frames','7000']
        if has_follow:extra+=['--step','-:poke:0x100b14cc=1','--step',f'-:call:{sym["bf_encoder"]:#x},3,{7 if reverse else 1}']
        events=run(work,'patched',extra)
        balanced(events)
        leader_ch=13 if reverse else 1;follower_ch=5 if reverse else 2
        lead=[e[2] for e in events if e[:2]==('on',leader_ch)]
        bass=[e[2] for e in events if e[:2]==('on',follower_ch)]
        if not arp:
            assert lead==[62,65,69,65,69,72,67,71,74],lead
            if has_follow:
                assert bass==[48,52,55,59,38,41,45,48,38,41,45,48,41,45,48,52,43,47,50,53,43,47,50,53],bass
        else:
            assert {62,65,69,72,67,71,74}<=set(lead),lead
            if has_follow:assert {38,41,45,48,43,47,50,53}<=set(bass),bass
        saved=emu_card.extract_image((work/'patched-card.img').read_bytes())
        for p in (work/'project').glob('bank*.*'):assert saved['OCTABAM/BASS/'+p.name]==p.read_bytes()
        cases[name]=dict(leader=lead,follower=bass)
        print(f'  [ok] full firmware {name}: generated chords, note ownership and unchanged bank files',flush=True)
    work=fixture(source,'off',{})
    extra=['--sequencer','--internal-clock','--frames','7000']
    a=run(work,'stock',extra,image=ROOT/'out/raw/section_3_MAIN_OS.bin')
    b=run(work,'patched',extra)
    assert a==b
    balanced(b)
    print('  [ok] full firmware TYPE OFF matches stock MIDI',flush=True)
    return cases


def extended_scale(source):
    sym=harmony.symbols()
    if 'ms_decode' not in sym:return {}
    work=fixture(source,'dorian-output',{},key_raw=25,first_note=64)
    extra=['--sequencer','--internal-clock','--frames','7000']
    if 'bf_sources' in sym:
        extra+=['--step','-:poke:0x100b14cc=1','--step',f'-:call:{sym["bf_encoder"]:#x},3,1']
    events=run(work,'patched',extra);balanced(events)
    lead=[e[2] for e in events if e[:2]==('on',1)]
    bass=[e[2] for e in events if e[:2]==('on',2)]
    assert lead[0]==63 and all(n%12 in harmony.MODES[1] for n in lead),lead
    if 'bf_sources' in sym:assert bass[:3]==[48,39,39],bass
    print('  [ok] full firmware added scale with HARM OFF: E snaps to Eb; follower uses Eb root',flush=True)
    return {'dorian-output':dict(leader=lead,follower=bass)}


def keyboard(source):
    results={}
    for arp in (False,True):
        work=fixture(source,'keys-arp' if arp else 'keys-chords',{0:2},arp=arp)
        script=work/'keys.txt'
        script.write_text('100 key 0x31 down\n200 key 0x31 up\n1000 key 0 down\n1800 key 4 down\n2600 key 0 up\n3400 key 4 up\n4300 quit\n')
        extra=['--step','-:poke:0x80000015=1','--step','-:poke:0x460d16f3=1',
               '--step','-:poke:0x100b14cc=0','--internal-clock','--live-script',script,
               '--lcd',work/'keys.lcd']
        events=run(work,'keys',extra)
        balanced(events)
        pitches=[e[2] for e in events if e[0]=='on']
        if not arp:
            assert pitches==[48,52,55,59],events
            assert [(e[0],e[2]) for e in events if e[0]=='off']==[('off',48),('off',52),('off',55),('off',59)],events
        else:
            assert {48,52,55,59}<=set(pitches),events
        results[work.name]=pitches
        print(f'  [ok] UART chromatic keys {work.name}: generated notes and balanced releases',flush=True)
    return results


def note_rules(source):
    sym=harmony.symbols();has_follow='bf_sources' in sym;results={}
    for reverse in ([False,True] if has_follow else [False]):
        leader=7 if reverse else 0
        name='note-transpose-reverse' if reverse else 'note-transpose'
        work=fixture(source,name,{leader:1,1:1},reverse=reverse,first_note=71,
                     tran={leader:7,1:1},locks={2:6,3:1,6:12,8:7})
        extra=['--sequencer','--internal-clock','--frames','7000']
        if has_follow:extra+=['--step','-:poke:0x100b14cc=1','--step',f'-:call:{sym["bf_encoder"]:#x},3,{7 if reverse else 1}']
        events=run(work,'patched',extra);balanced(events)
        lead=[e[2] for e in events if e[:2]==('on',13 if reverse else 1)]
        bass=[e[2] for e in events if e[:2]==('on',5 if reverse else 2)]
        assert lead==[77,72,74],lead # B+7 -> F, F+7 -> C, G+7 -> D
        if has_follow:assert bass==[48,47,41,48,45,38],bass
        results[name]=dict(leader=lead,follower=bass)
        print(f'  [ok] {name}: final scale snap after TRAN/P-locks; source latch and balanced releases',flush=True)
    for arp in (False,True):
        t=1 if has_follow else 0
        name='note-key-arp' if arp else 'note-key-direct'
        work=fixture(source,name,{t:1},arp=arp,tran={t:7})
        script=work/'keys.txt'
        script.write_text('100 key 0x31 down\n200 key 0x31 up\n1000 key 2 down\n1800 key 2 up\n2200 key 1 down\n3000 key 1 up\n3700 quit\n')
        extra=['--step','-:poke:0x80000015=1','--step','-:poke:0x460d16f3=1',
               '--step',f'-:poke:0x100b14cc={t}','--internal-clock','--live-script',script]
        if has_follow:extra+=['--step',f'-:call:{sym["bf_encoder"]:#x},3,1','--step',f'-:poke:{sym["bf_roots"]:#x}=41']
        events=run(work,'keys',extra);balanced(events)
        pitches=[e[2] for e in events if e[0]=='on']
        if arp:assert set(pitches)=={48,50},pitches
        else:assert pitches==[50,48],pitches
        results[name]=pitches
        print(f'  [ok] {name}: played D remains D with TRAN +7 and followed F; C# snaps to C',flush=True)
    return results


def chord_rules(source):
    sym=harmony.symbols();has_follow='bf_sources' in sym;results={}
    def chord(root,kind):
        notes=[n for n in range(root,160) if n%12 in harmony.MODES[0]]
        return [notes[i*2] for i in range(kind+1) if notes[i*2]<=127]
    for kind in (2,3):
        for arp in (False,True):
            name=f'chord-transpose-{kind}-' + ('arp' if arp else 'direct')
            work=fixture(source,name,{0:kind,1:kind},arp=arp,first_note=71,
                         tran={0:7,1:1},locks={2:6,3:1,6:12,8:7})
            extra=['--sequencer','--internal-clock','--frames','7000']
            if has_follow:extra+=['--step','-:poke:0x100b14cc=1','--step',f'-:call:{sym["bf_encoder"]:#x},3,1']
            events=run(work,'patched',extra);balanced(events)
            lead=[e[2] for e in events if e[:2]==('on',1)]
            bass=[e[2] for e in events if e[:2]==('on',2)]
            want_lead=[n for root in (77,72,74) for n in chord(root,kind)]
            want_bass=[n for root in (48,47,41,48,45,38) for n in chord(root,kind)]
            if arp:
                assert lead and set(lead)<=set(want_lead) and {77,81,84}<=set(lead),lead
                if has_follow:assert bass and set(bass)<=set(want_bass),bass
            else:
                assert lead==want_lead,(lead,want_lead)
                if has_follow:assert bass==want_bass,(bass,want_bass)
            results[name]=dict(leader=lead,follower=bass)
            print(f'  [ok] {name}: snapped root then diatonic thirds; follower P-locks; balanced releases',flush=True)
            t=1 if has_follow else 0
            name=f'chord-key-{kind}-' + ('arp' if arp else 'direct')
            work=fixture(source,name,{t:kind},arp=arp,tran={t:7})
            script=work/'keys.txt'
            script.write_text('100 key 0x31 down\n200 key 0x31 up\n1000 key 2 down\n1800 key 2 up\n2200 key 1 down\n3000 key 1 up\n3700 quit\n')
            extra=['--step','-:poke:0x80000015=1','--step','-:poke:0x460d16f3=1',
                   '--step',f'-:poke:0x100b14cc={t}','--internal-clock','--live-script',script]
            if has_follow:extra+=['--step',f'-:call:{sym["bf_encoder"]:#x},3,1','--step',f'-:poke:{sym["bf_roots"]:#x}=41']
            events=run(work,'keys',extra);balanced(events)
            pitches=[e[2] for e in events if e[0]=='on']
            want=chord(50,kind)+chord(48,kind)
            if arp:assert set(pitches)==set(want),pitches
            else:assert pitches==want,pitches
            results[name]=pitches
            print(f'  [ok] {name}: D minor and C major despite TRAN +7/followed F; inherited scale',flush=True)
    return results


def persistence(source):
    work=fixture(source,'persistence',{0:2,1:1})
    lines=[]
    def key(at,k,hold=100):lines.extend([f'{at} key {k:#x} down',f'{at+hold} key {k:#x} up'])
    key(100,0x31);key(600,0x35);key(1100,0x10)
    lines.extend(['1600 key 0x2d down','1700 key 0x22 down','1850 key 0x22 up','1950 key 0x2d up','2300 enc 5 1'])
    key(2800,0x32)
    lines.extend(['3300 key 0x2d down','3400 key 0x23 down','3550 key 0x23 up','3650 key 0x2d up','4000 enc 5 1'])
    key(4500,0x32)
    for at,k in zip(range(5000,9200,700),[0x1c,0x21,0x20,0x31,0x31]):key(at,k)
    lines.append('40000 quit')
    script=work/'save.txt';script.write_text('\n'.join(lines)+'\n')
    extra=['--rtc','1800000000','--live-script',script,'--lcd',work/'save.lcd',
           '--mem-dump',f'0x10000000,0x100000={work}/saved-cs1.bin;0x100b14e2,10={work}/saved-state.bin']
    run(work,'save',extra)
    expected=bytes((3,1,0,0,0,0,0,0,0,0x4a))
    assert (work/'saved-state.bin').read_bytes()==expected
    files=emu_card.extract_image((work/'save-card.img').read_bytes())
    for name in ('project.work','project.strd'):
        assert b'#MIDI_HARMONY_TYPE_V1_T1=3' in files['OCTABAM/BASS/'+name]
    # Native Part storage contains appended scale ID 25 (C Dorian).
    for name in ('bank01.work','bank01.strd'):
        data=files['OCTABAM/BASS/'+name]
        assert data[otp.PART_BASE+9+0x4e2+17]==25,(name,data[otp.PART_BASE+9+0x4e2+17])
    quit_script=work/'quit.txt';quit_script.write_text('1500 quit\n')
    for name,options in [('reload',[]),('warm',['--no-post','--cs1-in',work/'saved-cs1.bin'])]:
        run(work,name,['--rtc','1800000000','--live-script',quit_script,
                      '--mem-dump',f'0x100b14e2,10={work}/{name}-state.bin;0x46c76df1,1={work}/{name}-key.bin']+options,
            card=work/'save-card.img')
        assert (work/f'{name}-state.bin').read_bytes()==expected,name
        assert (work/f'{name}-key.bin').read_bytes()==b'\x19',name
    old=fixture(source,'old-project',{})
    run(old,'load',['--rtc','1800000000','--cs1-in',work/'saved-cs1.bin','--live-script',quit_script,
                    '--mem-dump',f'0x100b14e2,10={old}/state.bin'])
    assert (old/'state.bin').read_bytes()==bytes(9)+b'J'
    print('  [ok] UART HARM/KEY controls, actual SAVE, disk reload, CS1 warm boot and old-project defaults',flush=True)
    return {'persistence':'pass'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',required=True,type=pathlib.Path)
    a=ap.parse_args();OUT.mkdir(exist_ok=True)
    cases=sequence(a.project)
    cases.update(extended_scale(a.project))
    cases.update(keyboard(a.project))
    cases.update(note_rules(a.project))
    cases.update(chord_rules(a.project))
    cases.update(persistence(a.project))
    (OUT/'result.json').write_text(json.dumps(dict(cases=cases,image_sha256=hashlib.sha256((ROOT/'out/mainos_bus.bin').read_bytes()).hexdigest(),hardware_tested=False),indent=2)+'\n')
if __name__=='__main__':main()
