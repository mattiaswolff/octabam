#!/usr/bin/env python3
"""FM Synth on both bus cores, native MIDI release and concurrent Harmony.

Uses disposable project/card copies and captures full-firmware DSP audio.
No device access or physical timing acceptance. Run after make bus:
  .venv/bin/python3 tools/verify/verify_synth_bus_port.py --project DIR
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import toolpath  # noqa: E402,F401
import ab_fixture
import blockdump
import emu_card
import midi_fixture
import recloop
import verify_repitch as sample
from hw import ot_project as otp

OUT = ROOT / 'out/synth-bus-port'
TRACKS = (1, 5)  # T2 and T6: SEND participants on opposite DSP cores.


def marker(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(bytes(4 * 44100 * 2))


def fixture(source, work, sequenced, voices):
    base = ab_fixture.prepare(source, work / 'base')
    sample.SAMPLE_REL = 'AUDIO/FMSYNTH.wav'
    sample.LOOP_FRAMES = 4 * 44100
    sample.build_project(base, work / 'project', 0, 2, 120, 64, 64)
    project = work / 'project'
    otp.host_rig(project, 'mattias-bottleservice', guard=False)
    for bank in project.glob('bank*.work'):
        def edit(d):
            for part in range(8):
                b = otp.PART_BASE + part * otp.PART_STRIDE + 9
                for t in TRACKS:
                    d[b + 0x22 + t] = 1
                    d[b + 0x2ca + 5 * t + 1] = 0
                    d[b + 0x2a + 30*t + 6:b + 0x2a + 30*t + 12] = bytes((64, 0, 0, 64, 0, 127))
                    d[b + 0x1da + 30*t + 6:b + 0x1da + 30*t + 12] = bytes((1, 0, 0, 0, 0, 0))
                    at = b + 0x11a + 24*t
                    d[at:at+6] = bytes((0, 0, voices, 0, 0, 0))
                    d[at+6:at+12] = bytes((0, 127, 10, 64, 64, 127))
                # A separate MIDI track emits a C major chord while FM plays.
                at = b + 0x4e2
                d[at:at+36] = bytes(36)
                d[at] = 16
                d[at+5] = 2
                d[at+13] = 3
                d[at+15] = 2
            for pattern in range(16):
                for t in range(8):
                    at = otp.trac_off(pattern, t)
                    d[at:at+64] = bytes(64)
                    if sequenced and t in TRACKS:
                        d[at:at+8] = (1).to_bytes(8, 'big')
                    at = 0x492e + pattern*0x8eec + t*0x8b9
                    d[at+9:at+33] = bytes(24)
        otp._bank_write(project, int(bank.stem[4:]), edit, guard=False)
    for p in project.glob('project.*'):
        raw = p.read_bytes()
        for key, value in [('MIDI_AUDIO_TRK_NOTE_IN', 1), ('MIDI_AUDIO_TRK_CC_OUT', 0)]:
            raw = re.sub(key.encode()+rb'=\d+', f'{key}={value}'.encode(), raw)
        p.write_bytes(raw)
    card, _ = emu_card.stage_project(project, 'OCTABAM', 'SYNTH', tree=work/'tree',
                                    audio=[f'{OUT}/FMSYNTH.wav:AUDIO/FMSYNTH.wav'])
    (work/'card.img').write_bytes(card)


def rms(values):
    return math.sqrt(sum(v*v for v in values) / max(1, len(values)))


def run_case(source, name, sym, sequenced=False, voices=1, reload_card=None):
    work = OUT/name
    work.mkdir(parents=True, exist_ok=True)
    fixture(source, work, sequenced, voices)
    midi = work/'input.midi'
    rows = []
    if not sequenced:
        for t in TRACKS:
            for i, note in enumerate((84, 88, 91)[:voices]):
                rows += [f'{100+i*50} {0x90+t:02x} {note:02x} 64',
                         f'{1400+i*50} {0x80+t:02x} {note:02x} 00']
    midi.write_text('\n'.join(sorted(rows, key=lambda x: int(x.split()[0])))+'\n')
    steps = [(500, f'call:{sym["mh_keyboard"]:#x},0,60,100,0'),
             (1000, f'call:{sym["mh_keyboard"]:#x},0,60,0,0'),
             (1800, 'call:0x4009f5bc')]
    cmd = [str(ROOT/'out/emu/ot_emu'), '--image', str(OUT/'candidate.bin'),
           '--card', str(reload_card or work/'card.img'), '--set', 'OCTABAM', '--project', 'SYNTH',
           '--mkii', '--load-ms', '90000', '--sequencer', '--internal-clock', '--frames', '3000',
           '--dsp', '--main-level', '64', '--audio-out', str(work/'audio'),
           '--block-dump', str(work/'blocks.bin'), '--midi', str(midi),
           '--midi-out', str(work/'output.midi'), '--card-out', str(work/'saved-card.img'),
           '--mem-dump', f'{sym["sy_state"]:#x},1024={work}/synth-state.bin;'
                         f'{sym["mh_refs"]:#x},1024={work}/harmony-refs.bin']
    for frame, action in steps:
        cmd += ['--step', f'{frame}:{action}']
    with (work/'port.log').open('w') as log:
        result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    log = (work/'port.log').read_text()
    assert result.returncode == 0 and 'run ended REACHED' in log, work/'port.log'
    assert 'LOAD PROJECT handled' in log and 'DID NOT RETURN' not in log
    c = blockdump.classes(blockdump.read(work/'blocks.bin'))
    metrics = {}
    for t in TRACKS:
        audio = recloop.readback_audio(c, t+1)
        assert audio, ('no DSP readback', t+1)
        # The dump includes load/boot frames; use the audio file's transport marker.
        core = 1 if t < 4 else 0
        start = int(re.search(rf'audio_core{core}\.wav, .*?transport start at frame (\d+)', log).group(1))
        sounding = audio[(start+500)*16:(start+1100)*16]
        tail = audio[-400*16:]
        level, quiet = rms(sounding), rms(tail)
        assert level > 100, (name, t+1, 'silent synth', level)
        assert quiet < max(2, level*0.001), (name, t+1, 'voice did not stop', quiet, level)
        hz = sample.pitch(sounding)
        if voices == 1:
            assert abs(hz-261.6256) < 2, (name, t+1, 'C4 pitch', hz)
        metrics[f'T{t+1}'] = dict(rms=level, stopped_rms=quiet, pitch_hz=hz)
    state = (work/'synth-state.bin').read_bytes()
    assert all(state[t*128+36] == 0 for t in TRACKS), 'synth voice remains active'
    assert (work/'harmony-refs.bin').read_bytes() == bytes(1024)
    notes = [e for e in midi_fixture.notes((work/'output.midi').read_bytes()) if e[1] == 16]
    expected = [('on', 16, n, 100) for n in (60, 64, 67)] + [('off', 16, n, 0) for n in (60, 64, 67)]
    assert notes == expected, ('concurrent Harmony', notes)
    print('[ok]', name, metrics, 'Harmony chord/release intact', flush=True)
    return dict(audio=metrics, harmony_events=notes, command=cmd)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', required=True, type=Path)
    ap.add_argument('--case', choices=('sequence', 'midi-mono', 'midi-poly', 'reload'))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'candidate.bin').write_bytes((ROOT/'out/mainos_bus.bin').read_bytes())
    raw = subprocess.check_output(['m68k-elf-nm', str(ROOT/'out/platform/runtime/runtime.elf')], text=True)
    sym = {f[2]: int(f[0], 16) for line in raw.splitlines() if len(f := line.split()) == 3}
    (OUT/'symbols.json').write_text(json.dumps(sym, indent=2)+'\n')
    marker(OUT/'FMSYNTH.wav')
    results = {}
    for name, seq, voices in [('sequence', True, 1), ('midi-mono', False, 1), ('midi-poly', False, 3), ('reload', True, 1)]:
        if args.case and name != args.case:
            continue
        reload_card = OUT/'sequence/saved-card.img' if name == 'reload' else None
        results[name] = run_case(args.project, name, sym, seq, voices, reload_card)
        receipt = dict(cases=results, image_sha256=hashlib.sha256((OUT/'candidate.bin').read_bytes()).hexdigest(),
                       hardware_tested=False, scope='Full-firmware emulator, generated silent marker, both bus cores; reload uses virtual card after playback, not a save-path test')
        (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
