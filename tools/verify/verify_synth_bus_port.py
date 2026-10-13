#!/usr/bin/env python3
"""FM Synth on both bus cores, native MIDI release and concurrent Harmony.

Uses disposable project/card copies and captures full-firmware DSP audio.
No device access or physical timing acceptance. Run after make bus:
  .venv/bin/python3 tools/verify/verify_synth_bus_port.py --project DIR
"""
import argparse
import cmath
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


def fixture(source, work, sequenced, voices, loopback=False):
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
                    d[at+18:at+20] = bytes((70, 70))  # Feed both real bus hosts.
                # A separate MIDI track emits a C major chord while FM plays.
                at = b + 0x4e2
                d[at:at+36] = bytes(36)
                d[at] = 16
                d[at+5] = 2
                d[at+13] = 3
                d[at+15] = 2
                if loopback:
                    for source_track, audio_track in enumerate(TRACKS):
                        at = b + 0x3e2 + 32*source_track
                        d[at:at+32] = bytes.fromhex(
                            '54 64 06 40 40 40 00 00 00 00 00 00 40 00 00 05 '
                            '00 06 40 00 00 00 00 40 00 00 00 00 00 00 00 00')
                        at = b + 0x4e2 + 36*source_track
                        d[at:at+36] = bytes(36)
                        d[at] = audio_track+1
                        d[at+2] = 128  # Program change OFF.
                        d[at+12] = 4  # Native Part DEST INT, Follow OFF.
            for pattern in range(16):
                for t in range(8):
                    at = otp.trac_off(pattern, t)
                    d[at:at+64] = bytes(64)
                    if sequenced and t in TRACKS:
                        d[at:at+8] = (1).to_bytes(8, 'big')
                    at = 0x492e + pattern*0x8eec + t*0x8b9
                    d[at+9:at+33] = bytes(24)
                    if loopback:
                        d[at+0x39:at+0x839] = b'\xff'*2048
                        if pattern == 0 and t < 2:
                            d[at+9:at+17] = (1).to_bytes(8, 'big')
                            d[at+0x39:at+0x3c] = bytes((84, 100, 6))
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


def run_case(source, name, sym, sequenced=False, voices=1, reload_card=None,
             check_pitch=True, extra_dumps=()):
    work = OUT/name
    work.mkdir(parents=True, exist_ok=True)
    loopback = name == 'loopback'
    fixture(source, work, sequenced, voices, loopback)
    midi = work/'input.midi'
    rows = []
    if not sequenced and not loopback:
        for t in TRACKS:
            for i, note in enumerate((84, 88, 91)[:voices]):
                rows += [f'{100+i*50} {0x90+t:02x} {note:02x} 64',
                         f'{1400+i*50} {0x80+t:02x} {note:02x} 00']
    midi.write_text('\n'.join(sorted(rows, key=lambda x: int(x.split()[0])))+'\n')
    # Exercise both audio and MIDI entries of the native CHROMATIC drawer.
    steps = [('-', 'poke:0x460d16f3=1;0x80000015=1;0x100b14cc=1'),
             ('-', 'call:0x40044920'),
             ('-', 'poke:0x80000015=0'),
             ('-', 'call:0x40044920'),
             (500, f'call:{sym["mh_keyboard"]:#x},0,60,100,0'),
             (1000, f'call:{sym["mh_keyboard"]:#x},0,60,0,0'),
             (1800, 'call:0x40006820,1'), (1800, 'call:0x40006820,5')]
    if voices > 1 or loopback:
        # Native UART-only polyphony: injecting C ABI calls waits for the
        # idle main task and can starve under this six-voice workload.
        # Concurrent Harmony is checked by the mono/sequence cases.
        steps = [(frame, action) for frame, action in steps if frame == '-']
    cmd = [str(ROOT/'out/emu/ot_emu'), '--image', str(OUT/'candidate.bin'),
           '--card', str(reload_card or work/'card.img'), '--set', 'OCTABAM', '--project', 'SYNTH',
           '--mkii', '--load-ms', '90000', '--sequencer', '--internal-clock', '--frames', '3000',
           '--dsp', '--main-level', '64', '--audio-out', str(work/'audio'),
           '--block-dump', str(work/'blocks.bin'), '--midi', str(midi),
           '--midi-out', str(work/'output.midi'), '--card-out', str(work/'saved-card.img'),
           '--mem-dump', f'{sym["sy_state"]:#x},1024={work}/synth-state.bin;'
                         f'{sym["po_voices"]:#x},2048={work}/poly-voices.bin;'
                         f'{sym["mh_refs"]:#x},1024={work}/harmony-refs.bin;'
                         f'0x80000110,512={work}/dsp-records.bin']
    for frame, action in steps:
        cmd += ['--step', f'{frame}:{action}']
    if extra_dumps:
        cmd[cmd.index('--mem-dump')+1] += ';'+';'.join(extra_dumps)
    if loopback:
        index = cmd.index('--mem-dump')+1
        cmd[index] += f';{sym["lb_accepted"]:#x},8={work}/loopback-stats.bin;{sym["lb_internal_held"]:#x},4={work}/loopback-held.bin'
    with (work/'port.log').open('w') as log:
        result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    log = (work/'port.log').read_text()
    assert result.returncode == 0 and 'run ended REACHED' in log, work/'port.log'
    assert 'LOAD PROJECT handled' in log and 'DID NOT RETURN' not in log
    assert 'main never spun' not in log and 'unimplemented opcode' not in log, work/'port.log'
    blocks = blockdump.read(work/'blocks.bin')
    # The dump opens after LOAD, before the two pre-transport panel calls.
    # Those calls can advance audio frames; its frame counter is not reset
    # by PLAY. Keep the final 3000 frames whose completion the log confirms.
    end_frame = max(row[1] for row in blocks)
    assert end_frame >= 3000, ('incomplete frame capture', end_frame)
    blocks = [row for row in blocks if row[1] > end_frame-3000]
    for core in (0, 1):
        frames = [row[1] for row in blocks if row[0] == '<' and row[2] == 1 and row[3] == core]
        assert frames == list(range(end_frame-2999, end_frame+1)), ('missing/duplicate DSP frame', core)
    c = blockdump.classes(blocks)
    # Read the DSP-facing IDs, not only the live UI IDs: a misresolved
    # TEMPO SYNC hook once left every record at NONE while the UI was right.
    records = (work/'dsp-records.bin').read_bytes()
    bank = (work/'project/bank01.work').read_bytes()
    expected_ids = bank[otp.PART_BASE+otp.FX2_OFF:otp.PART_BASE+otp.FX2_OFF+8]
    actual_ids = [int.from_bytes(records[t*64+56:t*64+58], 'big') for t in range(8)]
    assert actual_ids == list(expected_ids), ('DSP FX2 routing', actual_ids, list(expected_ids))
    bus_audio = {}
    for host in (1, 5):
        audio = recloop.readback_audio(c, host)
        assert audio, ('missing bus host readback', host)
        level = rms(audio)
        assert level > 100, ('Synth send did not reach bus host', host, level)
        bus_audio[f'T{host}'] = level
    metrics = {}
    for t in TRACKS:
        audio = recloop.readback_audio(c, t+1)
        assert audio, ('no DSP readback', t+1)
        # Block dumps begin at transport; ESAI WAVs include the preceding load.
        assert len(audio) == 3000*16, ('unexpected block-dump length', len(audio))
        sounding = audio[500*16:1100*16]
        if loopback:
            # Native LEN=6 gives a short note. Measure the loudest complete
            # window, independent of the receiver task's scheduling offset.
            sounding = max((audio[i:i+4096] for i in range(0, 2000*16, 1000)), key=rms)
        tail = audio[-400*16:]
        level, quiet = rms(sounding), rms(tail)
        assert level > 100, (name, t+1, 'silent synth', level)
        assert quiet < max(2, level*0.001), (name, t+1, 'voice did not stop', quiet, level)
        if not sequenced and not loopback:
            released = rms(audio[1650*16:1750*16])
            assert released < max(2, level*0.001), (name, t+1, 'MIDI note-off did not release', released)
        hz = sample.pitch(sounding)
        if voices == 1 and check_pitch:
            assert abs(hz-261.6256) < 2, (name, t+1, 'C4 pitch', hz)
        tones = {}
        if voices > 1:
            for freq in (261.6256, 329.6276, 391.9954):
                amp = 2*abs(sum(v*cmath.exp(-2j*math.pi*freq*i/44100) for i, v in enumerate(sounding)))/len(sounding)
                assert amp > level*0.2, (name, t+1, 'missing chord tone', freq, amp, level)
                tones[str(freq)] = amp
        metrics[f'T{t+1}'] = dict(rms=level, stopped_rms=quiet, pitch_hz=hz, chord_amplitudes=tones)
    state = (work/'synth-state.bin').read_bytes()
    # S_ON identifies the renderer, and stays set after a poly note-off.
    # V_STATE, not S_ON, owns each paraphonic voice's sounding/release state.
    poly = (work/'poly-voices.bin').read_bytes()
    assert all(poly[t*256+v*64+36] == 0 for t in TRACKS for v in range(4)), 'poly voice remains active'
    if voices == 1 and not loopback:  # These cases invoke the native voice kill.
        assert all(state[t*128+36] == 0 for t in TRACKS), 'native voice kill did not clear synth'
    assert (work/'harmony-refs.bin').read_bytes() == bytes(1024)
    notes = [e for e in midi_fixture.notes((work/'output.midi').read_bytes()) if e[1] == 16]
    expected = [('on', 16, n, 100) for n in (60, 64, 67)] + [('off', 16, n, 0) for n in (60, 64, 67)]
    assert notes == (expected if voices == 1 and not loopback else []), ('concurrent Harmony', notes)
    if loopback:
        assert not midi_fixture.notes((work/'output.midi').read_bytes()), 'INT leaked external notes'
        stats = (work/'loopback-stats.bin').read_bytes()
        accepted, delivered = (int.from_bytes(stats[i:i+4], 'big') for i in (0, 4))
        assert accepted >= 4 and accepted == delivered, ('internal delivery', accepted, delivered)
        assert (work/'loopback-held.bin').read_bytes() == bytes(4), 'internal note ownership remains'
    detail = ('internal delivery/release, no external notes' if loopback else
              'Harmony chord/release intact' if voices == 1 else 'native MIDI chord/release')
    print('[ok]', name, metrics, detail, flush=True)
    return dict(audio=metrics, bus_host_rms=bus_audio, dsp_fx2_ids=actual_ids, harmony_events=notes, command=cmd)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', required=True, type=Path)
    ap.add_argument('--case', choices=('sequence', 'midi-mono', 'midi-poly', 'reload', 'loopback'))
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'candidate.bin').write_bytes((ROOT/'out/mainos_bus.bin').read_bytes())
    raw = subprocess.check_output(['m68k-elf-nm', str(ROOT/'out/platform/runtime/runtime.elf')], text=True)
    sym = {f[2]: int(f[0], 16) for line in raw.splitlines() if len(f := line.split()) == 3}
    (OUT/'symbols.json').write_text(json.dumps(sym, indent=2)+'\n')
    marker(OUT/'FMSYNTH.wav')
    results = {}
    for name, seq, voices in [('sequence', True, 1), ('midi-mono', False, 1), ('midi-poly', False, 3), ('reload', True, 1), ('loopback', False, 1)]:
        if args.case and name != args.case:
            continue
        reload_card = OUT/'sequence/saved-card.img' if name == 'reload' else None
        results[name] = run_case(args.project, name, sym, seq, voices, reload_card)
        receipt = dict(cases=results, image_sha256=hashlib.sha256((OUT/'candidate.bin').read_bytes()).hexdigest(),
                       hardware_tested=False, scope='Full-firmware emulator, generated silent marker, both bus cores; reload uses virtual card after playback, not a save-path test')
        (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
