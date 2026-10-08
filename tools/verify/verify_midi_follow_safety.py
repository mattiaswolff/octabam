#!/usr/bin/env python3
"""Extended local Root Follow acceptance. Creates disposable fixtures under out/.

Run after building mattias-midi-follow; never uses a physical device.
"""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import toolpath  # noqa: E402,F401
import verify_midi_follow as bf
import emu_card
from hw import ot_project as otp
from hw import ot_bank

OUT = ROOT/'out/midi-follow-safety'
EMU = ROOT/'out/emu/ot_emu'
CASES = ('held-boundary', 'stop', 'restart', 'pattern-boundary', 'pattern', 'part', 'project')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_notes(raw, allow_held=False):
    events = bf.notes(raw)
    held, duplicates, unmatched = set(), [], []
    for kind, ch, pitch, velocity in events:
        key = ch, pitch
        if kind == 'on':
            if key in held:
                duplicates.append(key)
            held.add(key)
        elif key in held:
            held.remove(key)
        else:
            unmatched.append(key)
    if not allow_held:
        assert not held, ('hanging notes', sorted(held))
    assert not duplicates, ('duplicate on', duplicates[:10])
    assert not unmatched, ('unmatched off', unmatched[:10])
    return events, held


def transition_card(source):
    work = OUT/'transitions'
    work.mkdir(parents=True, exist_ok=True)
    project = work/'project'
    bf.fixture(source, project)
    for path in project.glob('bank*.work'):
        def mutate(data):
            # A02 uses the same Part and a distinct D/A/B progression.
            for t in range(8):
                start = 0x492e + t*0x8b9
                dest = start + ot_bank.PTRN_STRIDE
                data[dest:dest+0x8b9] = data[start:start+0x8b9]
                if t == 0:
                    for s, n in ((2, 62), (4, 69), (8, 71)):
                        data[dest+0x39+s*32] = n
            for p in (0, 1):
                tail = ot_bank.PTRN_BASE+(p+1)*ot_bank.PTRN_STRIDE
                data[tail-9:tail-7] = bytes((16,2))
                # Hold the last bass across the actual pattern boundary.
                at = 0x492e+p*ot_bank.PTRN_STRIDE+0x8b9
                mask = int.from_bytes(data[at+9:at+17], 'big') | (1 << 15)
                data[at+9:at+17] = mask.to_bytes(8,'big')
                data[at+0x39+15*32:at+0x39+15*32+3] = bytes((48,91,12))
                data[ot_bank.PTRN_BASE+(p+1)*ot_bank.PTRN_STRIDE-5] = 0
            # Part TWO changes channels, stressing release ownership.
            for p in (1, 5):
                base = otp.PART_BASE+p*otp.PART_STRIDE+9
                data[base+0x4e2] = 9
                data[base+0x4e2+36] = 5
        otp._bank_write(project, int(path.stem[4:]), mutate, guard=False)
    otp.write_stored(project)
    tree = work/'tree'
    emu_card.stage_project(project, 'OCTABAM', 'BASS', tree=tree)
    second = tree/'OCTABAM'/'SECOND'
    shutil.copytree(tree/'OCTABAM'/'BASS', second, dirs_exist_ok=True)
    for path in second.glob('bank*.work'):
        def mutate(data):
            for p in range(8):
                base = otp.PART_BASE+p*otp.PART_STRIDE+9
                data[base+0x4e2+36] = 6
            for s, n in ((2, 62), (4, 69), (8, 71)):
                data[0x492e+0x39+s*32] = n
        otp._bank_write(second, int(path.stem[4:]), mutate, guard=False)
    otp.write_stored(second)
    card = work/'card.img'
    card.write_bytes(emu_card.build_image(str(tree)))
    return card


def run_transition(image, card, name, label, enabled=True):
    work = OUT/'transitions'/name/label
    work.mkdir(parents=True, exist_ok=True)
    sym = bf.symbols()
    steps = []
    if enabled:
        steps += ['-:poke:0x100b14cc=1', f'-:call:{sym["bf_encoder"]:#x},3,4']
    frames = 7000
    if name == 'held-boundary':
        frames = 1500
    elif name in ('stop', 'restart'):
        steps += ['1500:call:0x4009f5bc']
        if name == 'stop':
            frames = 2000
        else:
            steps += ['2200:call:0x4009b964,0']
            steps += [f'2200:call:0x4009b5c8,{t}' for t in range(8)]
            steps += ['6500:call:0x4009f5bc']
    elif name in ('pattern','pattern-boundary'):
        steps += ['1500:call:0x400a1030,0,1']
        if name == 'pattern-boundary':
            frames = 5500
        else:
            steps += ['6500:call:0x4009f5bc']
    elif name == 'part':
        # The PART chooser's own selection routine, not an apply-only helper.
        steps += ['1500:call:0x4004a8a4,1', '6500:call:0x4009f5bc']
    elif name == 'project':
        ptr = 0x47001000
        poke = ';'.join(f'{ptr+i:#x}={b}' for i,b in enumerate(b'SECOND\0'))
        steps += [f'1500:poke:{poke}', f'1500:call:0x40023c7c,{ptr}']
        steps += ['90000:call:0x4009b964,0']
        steps += [f'90000:call:0x4009b5c8,{t}' for t in range(8)]
        steps += ['97000:call:0x4009f5bc']
        frames = 98000
    else:
        raise ValueError(name)
    dump = (f'0x800065b8,8={work}/transport.bin;0x80000002,4={work}/selection.bin;'
            f'0x100f8378,32={work}/project-name.bin;0x46c76dc0,544={work}/midi-setup.bin')
    if enabled:
        dump += f';0x100a4ece,25288={work}/parts.bin;0x100b14cf,1={work}/ui-part.bin'
    cmd = [EMU, '--image', image, '--card', card, '--set', 'OCTABAM', '--project', 'BASS',
           '--sequencer', '--internal-clock', '--frames', str(frames), '--load-ms', '90000',
           '--midi-out', work/'out.midi', '--card-out', work/'card.img', '--mem-dump', dump]
    for s in steps:
        cmd += ['--step', s]
    with (work/'run.log').open('w') as log:
        log.write(' '.join(map(str,cmd))+'\n'); log.flush()
        p = subprocess.run(list(map(str,cmd)), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    text = (work/'run.log').read_text()
    assert p.returncode == 0 and 'run ended REACHED' in text, work/'run.log'
    assert 'DID NOT RETURN' not in text and 'main never spun' not in text, work/'run.log'
    events, held = audit_notes((work/'out.midi').read_bytes(), name in ('held-boundary','pattern-boundary'))
    (work/'notes.json').write_text(json.dumps(events,indent=2)+'\n')
    if name == 'held-boundary':
        assert (2, 36 if enabled else 48) in held, held
    elif name == 'pattern-boundary':
        assert (2,43 if enabled else 48) in held,held
    else:
        assert int.from_bytes((work/'transport.bin').read_bytes()[:4], 'big') == 2
    if enabled:
        part=(work/'ui-part.bin').read_bytes()[0]
        raw=(work/'parts.bin').read_bytes()
        sources=bytes(raw[part*0x18b2+0x4e2+36*t+3] for t in range(8))
        expected=bytes(8) if name in ('part','project') else bytes((0,1,0,0,0,0,0,0))
        assert sources==expected, (name,part,sources,expected)
    if name == 'pattern':
        assert (work/'transport.bin').read_bytes()[6] == 1
        assert any(e[:3]==('on',1,62) for e in events), events
    if name == 'part':
        assert (work/'selection.bin').read_bytes()[1] == 1
        assert any(e[:2]==('on',5) for e in events), events
    if name == 'project':
        assert (work/'project-name.bin').read_bytes().split(b'\0')[0] == b'SECOND'
        assert any(e[:2]==('on',6) for e in events), events
    files = emu_card.extract_image((work/'card.img').read_bytes())
    errors = [(k, line.decode('latin1')) for k,v in files.items() if k.endswith('.txt')
              for line in v.splitlines() if b'ERROR' in line and b'FILE NOT FOUND' not in line]
    assert not errors, errors
    for project in ('BASS','SECOND'):
        for src in (OUT/'transitions/tree/OCTABAM'/project).glob('bank*.*'):
            assert files[f'OCTABAM/{project}/{src.name}'] == src.read_bytes(), (name, project, src.name)
    print(f'[ok] {name}/{label}: {len(events)} note events; held={sorted(held)}', flush=True)
    return dict(events=events, image_sha256=sha(image), status='pass')


def transitions(source, image, cases):
    card = transition_card(source)
    (OUT/'transitions/result.json').unlink(missing_ok=True)
    result = {}
    for name in cases:
        stock = run_transition(ROOT/'out/raw/section_3_MAIN_OS.bin',card,name,'stock',False)
        patched = run_transition(image,card,name,'follow',True)
        # Channels 1/3 (and source's changed channel 9) remain independent.
        for ch in (1,3,9):
            assert [e for e in stock['events'] if e[1]==ch] == [e for e in patched['events'] if e[1]==ch], (name,ch)
        result[name] = dict(stock=stock,patched=patched)
        (OUT/'transitions/result.json').write_text(json.dumps(result,indent=2)+'\n')


def soak_card(source, work, enabled):
    """Existing audio stress generator plus eight busy MIDI tracks."""
    import ab_fixture
    prepared = work/'source'
    ab_fixture.prepare(source, prepared)
    project = work/'project'
    if project.exists():
        shutil.rmtree(project)  # owned disposable fixture, never the source
    with (work/'fixture.log').open('w') as log:
        subprocess.run([sys.executable, str(ROOT/'tools/harness/stress_project.py'),
                        '--remix', 'mattias-midi-follow', '--source', str(prepared),
                        '--out', str(project)], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    for path in project.glob('bank*.work'):
        def mutate(data):
            for part in range(8):
                base = otp.PART_BASE+part*otp.PART_STRIDE+9
                for t in range(8):
                    at = base+0x3e2+32*t
                    data[at:at+32] = bytes.fromhex(
                        '3c 64 02 40 40 40 20 20 20 00 00 00 40 00 00 05 '
                        '00 06 40 00 7f 00 00 40 00 00 00 00 00 00 00 00')
                    if t == 0:
                        data[at+3:at+5] = bytes((68,71))
                    setup=base+0x4e2+36*t
                    data[setup:setup+36] = bytes((t+1,))+bytes(35)
                    # The initial Part is configured through the encoder below;
                    # later Parts carry their own routing during the soak.
                    data[setup+3]=int(enabled and t>0 and part%4!=0)
                    data[setup+13]=3
                    data[setup+15]=2
            for p in range(16):
                tail = ot_bank.PTRN_BASE+(p+1)*ot_bank.PTRN_STRIDE
                # A 16-step normal cycle bounds queued panel switches to 2 s.
                # Do not inherit the template's 128-step advanced timing.
                data[tail-11:tail-6] = bytes((16,2,16,2,0))
                for t in range(8):
                    at = 0x492e+p*ot_bank.PTRN_STRIDE+t*0x8b9
                    assert data[at:at+4] == b'MTRA'
                    data[at+9:at+33] = bytes(24)
                    data[at+0x39:at+0x839] = b'\xff'*2048
                    data[at+0x31:at+0x33] = bytes((16,2))
                    if p < 4:
                        data[at+9:at+17] = (65535).to_bytes(8,'big')
                        for step in range(16):
                            lock = at+0x39+step*32
                            data[lock:lock+3] = bytes(((60,65,67,62)[step//4] if t == 0 else 48+t,80+t,2))
        otp._bank_write(project,int(path.stem[4:]),mutate,guard=False)
    otp.write_stored(project)
    # Keep only the generated FLEX sample; avoid unrelated missing files.
    for path in project.glob('project.*'):
        raw=path.read_bytes()
        raw=re.sub(rb'\[SAMPLE\].*?\[/SAMPLE\]\r?\n',
                   lambda m: m[0] if b'PATH=AUDIO/STRESS_LOOP.wav' in m[0] else b'',raw,flags=re.S)
        path.write_bytes(raw)
    card,_=emu_card.stage_project(project,'OCTABAM','STRESS',tree=work/'tree',
                                  audio=[f'{project}/AUDIO/STRESS_LOOP.wav:STRESS/AUDIO/STRESS_LOOP.wav'])
    dest=work/'initial-card.img';dest.write_bytes(card)
    return dest


def soak(image, seconds, enabled, source):
    import struct
    import time
    import wave
    sys.path.insert(0,str(ROOT/'tools/panel'))
    from panel_server import PortProc, popup_geometry, CLOCK_GEOMETRY
    from types import SimpleNamespace
    label='follow' if enabled else 'off'
    work=OUT/f'soak-{label}-{seconds:g}s';work.mkdir(parents=True,exist_ok=True)
    (work/'result.json').unlink(missing_ok=True)
    (work/'diagnostics.json').unlink(missing_ok=True)
    (work/'out.midi').unlink(missing_ok=True)
    card=soak_card(source,work,enabled)
    local_card=work/'card.img';shutil.copy2(card,local_card)
    sym=bf.symbols()
    cmd=[EMU,'--image',image,'--card',local_card,'--card-rw','--set','OCTABAM','--project','STRESS',
         '--load-ms','90000','--interactive','--dsp','--dsp-rt','--mkii',
         '--sequencer','--internal-clock','--frames','0','--midi-out',work/'out.midi']
    if enabled:
        for t in range(1,8):
            cmd += ['--step',f'-:poke:0x100b14cc={t}', '--step',f'-:call:{sym["bf_encoder"]:#x},3,4']
    (work/'command.json').write_text(json.dumps(list(map(str,cmd)),indent=2))
    port=PortProc(cmd,work/'stderr.log')
    transcript=(work/'commands.log').open('w')
    def command(line,expect='ok'):
        answer=port.command(line,expect,timeout=120)
        transcript.write(line+' -> '+(answer[:300] if line.startswith('audio read') else answer)+'\n');transcript.flush()
        return answer
    def peek(addr,n):
        result=bytearray()
        for offset in range(0,n,4096):
            result += bytes.fromhex(command(f'peek {addr+offset:#x} {min(4096,n-offset)}','peek').split(' ',1)[1])
        return bytes(result)
    def run(ms):
        answer=command(f'run {ms}')
        assert 'stop=time' in answer,answer
    try:
        port.wait_ready(900)
        (work/'boot.log').write_text('\n'.join(port.log)+'\n')
        # Match the panel server: dismiss only the actual boot clock dialog.
        # Otherwise later pattern keys can target that modal window.
        memory=SimpleNamespace(mem_read=peek)
        for _ in range(60):
            if popup_geometry(memory)==CLOCK_GEOMETRY:
                command('key 0x26 2');run(60)
                command('key 0x26 0');run(300)
                assert popup_geometry(memory)!=CLOCK_GEOMETRY
                break
            run(100)
        layout=json.loads((ROOT/'out/platform/layout.json').read_text())
        code_before=peek(layout['base'],layout['runtime_end']-layout['base'])
        def stable_code(raw):
            raw=bytearray(raw)
            # The runtime contains several modules' state; only Root Follow's
            # instructions (up to its state arrays) are immutable here.
            lo=sym['bf_pre_capture']-layout['base'];hi=sym['bf_roots']-layout['base']
            return bytes(raw[lo:hi])
        expected=bytes((0,1,1,1,1,1,1,1)) if enabled else bytes(8)
        def sources():
            part=peek(0x100b14cf,1)[0]
            raw=peek(0x100a4ece+part*0x18b2+0x4e2,288)
            return bytes(raw[t*36+3] for t in range(8))
        assert sources()==expected
        assert int.from_bytes(peek(0x800065b8,4),'big')==1
        before=command('cfstatus','cfstatus')
        rt_before=command('rtstatus','rtstatus')
        command('audio start tracks')
        run(2000)
        reply=command('audio read','audio').split(' ',2)
        pcm=bytes.fromhex(reply[2]);values=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
        stem_peaks=[max((abs(values[i+c]) for i in range(8+2*t,len(values),24) for c in (0,1)),default=0) for t in range(8)]
        # Start a compact stereo capture for the sustained part.
        command('audio start main')
        peaks=[];start=time.monotonic()
        switches=[]
        pending=None
        with wave.open(str(work/'audio.wav'),'wb') as wav:
            wav.setparams((2,2,44100,0,'NONE','not compressed'))
            for k in range(round(seconds*2)):
                run(500)
                reply=command('audio read','audio').split(' ',2)
                pcm=bytes.fromhex(reply[2]);wav.writeframes(pcm)
                values=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
                peaks.append(max(map(abs,values),default=0))
                assert sources()==expected
                assert all(36 <= n <= 47 for n in peek(sym['bf_roots'],8))
                elapsed=(k+1)/2
                if seconds >= 20 and elapsed in (seconds/4,seconds/2,3*seconds/4):
                    target=round(elapsed/(seconds/4))
                    # PATTERN + trig over UART1, matching the panel workflow.
                    command('key 0x25 64');run(40)
                    command(f'key 0x20 {1<<target}');run(40)
                    command('key 0x20 0');command('key 0x25 0')
                    pending=(elapsed+3,target)
                if pending and elapsed >= pending[0]:
                    selected=peek(0x800065be,1)[0]
                    part=peek(0x80000003,1)[0]
                    assert (selected,part)==(pending[1],pending[1]),('pattern/Part switch',selected,part,pending)
                    switches.append(dict(pattern=selected+1,part=part+1,elapsed=elapsed))
                    print(f'[ok] soak/{label}: A{selected+1:02d} / Part {part+1} active under load',flush=True)
                    pending=None
                if k%20==19:
                    print(f'[progress] soak/{label}: {(k+1)/2:g}/{seconds:g} emulated seconds',flush=True)
        after=command('cfstatus','cfstatus')
        rt_after=command('rtstatus','rtstatus')
        audio_status=command('audio status','audio')
        code_unchanged=stable_code(peek(layout['base'],len(code_before)))==stable_code(code_before)
        # Actual STOP key over UART1; no direct write to transport state.
        command('key 0x24 128');run(50);command('key 0x24 0');run(500)
        state=int.from_bytes(peek(0x800065b8,4),'big')
        assert state in (0,2),('STOP failed',state)
        command('card flush','card')
        command('quit')
        assert port.proc.wait(timeout=30)==0
        events,held=audit_notes((work/'out.midi').read_bytes())
        note_counts={}
        for ch in range(1,9):
            ons=[e for e in events if e[:2]==('on',ch)]
            note_counts[ch]=len(ons)
            assert len(ons)>=seconds*7.8,(ch,len(ons))
            if enabled and ch>1:
                assert {e[2] for e in ons}<={36,41,43,38},(ch,ons[:20])
        assert len(set(note_counts[ch] for ch in range(2,9)))==1,note_counts
        assert note_counts[1]==3*note_counts[2],note_counts
        assert sum(p>0 for p in peaks)>len(peaks)*0.9,('silent audio',peaks)
        assert all(stem_peaks),('silent tracks',stem_peaks)
        files=emu_card.extract_image(local_card.read_bytes())
        errors=[line.decode('latin1') for key,v in files.items() if key.endswith('.txt')
                for line in v.splitlines() if b'ERROR' in line]
        assert not errors,errors
        for path in (work/'project').glob('bank*.*'):
            assert files[f'OCTABAM/STRESS/{path.name}']==path.read_bytes(),path.name
        # Retain MIDI and diagnostics even when a DSP counter rejects this run.
        result=dict(status='pending-dsp-check',enabled=enabled,seconds=seconds,note_events=len(events),held=list(held),
                    stem_peaks=stem_peaks,note_counts=note_counts,nonzero_blocks=sum(p>0 for p in peaks),blocks=len(peaks),
                    cf_before=before,cf_after=after,rt_before=rt_before,rt_after=rt_after,switches=switches,
                    audio_status=audio_status,code_unchanged=code_unchanged,
                    wall_seconds=time.monotonic()-start,image_sha256=sha(image),hardware_tested=False)
        (work/'diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
        assert 'faulted=00' in rt_after and 'ok=1' in rt_after,rt_after
        assert all(int(v)==0 for v in re.findall(r'(?<![a-z])(?:dropped|treqdropped|stale|pullshort|skewto0|skewto1)=(\d+)',rt_after)),rt_after
        assert 'dropped=0' in audio_status,audio_status
        assert code_unchanged
        result['status']='pass'
        (work/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'[ok] soak/{label}: {seconds:g}s, {len(events)} MIDI events, eight audio stems, no held notes',flush=True)
    finally:
        transcript.close()
        port.kill()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=pathlib.Path,required=True)
    ap.add_argument('--cases',nargs='+',choices=CASES,default=CASES)
    ap.add_argument('--mode',choices=('transitions','soak'),default='transitions')
    ap.add_argument('--seconds',type=int,default=120)
    ap.add_argument('--off',action='store_true')
    a=ap.parse_args()
    if a.seconds < 1 or (a.seconds >= 20 and a.seconds % 2):
        ap.error('--seconds must be positive; runs of 20 seconds or more need an even duration for the three pattern switches')
    OUT.mkdir(parents=True,exist_ok=True)
    if a.mode=='transitions':
        transitions(a.project,ROOT/'out/mainos_bus.bin',a.cases)
    else:
        soak(ROOT/'out/mainos_bus.bin',a.seconds,not a.off,a.project)

if __name__=='__main__':
    main()
