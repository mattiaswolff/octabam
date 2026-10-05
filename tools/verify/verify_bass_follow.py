#!/usr/bin/env python3
"""Check the built BASS FOLLOW detour; optionally play a copied MIDI project.

Usage: .venv/bin/python3 tools/verify/verify_bass_follow.py bass-follow --project DIR
The local template is only read. Fixtures, UART bytes and logs stay in out/.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import toolpath  # noqa: E402,F401
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE  # noqa: E402
from unicorn.m68k_const import *  # noqa: E402,F403

OUT = ROOT / 'out/bass-follow'
CAPTURE, CAPTURE_END = 0x4009FB00, 0x4009FB08
SITE, CONTINUE, SKIP = 0x4009FB80, 0x4009FB86, 0x4009FD2A
REGS = [UC_M68K_REG_D0, UC_M68K_REG_D1, UC_M68K_REG_D2, UC_M68K_REG_D3,
        UC_M68K_REG_D4, UC_M68K_REG_D5, UC_M68K_REG_D6, UC_M68K_REG_D7,
        UC_M68K_REG_A0, UC_M68K_REG_A1, UC_M68K_REG_A2, UC_M68K_REG_A3,
        UC_M68K_REG_A4, UC_M68K_REG_A5, UC_M68K_REG_A6, UC_M68K_REG_A7]


def symbols():
    nm = subprocess.check_output(['m68k-elf-nm', str(ROOT/'out/platform/runtime/runtime.elf')], text=True)
    return {name: int(addr, 16) for addr, name in re.findall(r'^([0-9a-f]+) [Tt] (bf_\w+)$', nm, re.M)}


def machine_gate(image):
    """Execute the actual build's detour and DRAM bytes, not a Python model."""
    layout = json.loads((ROOT / 'out/platform/layout.json').read_text())
    base = layout['base']
    sym = symbols()
    root, sources = sym['bf_roots'], sym['bf_sources']
    entry, capture_entry = sym['bf_note'], sym['bf_capture']
    binary = image.read_bytes()
    assert binary[SITE - 0x40000400:SITE - 0x40000400 + 6] == b'\x4e\xf9' + entry.to_bytes(4, 'big')
    assert binary[CAPTURE - 0x40000400:CAPTURE - 0x40000400 + 6] == b'\x4e\xf9' + capture_entry.to_bytes(4, 'big')
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
    uc.mem_map(0x40000000, 0x1000000)
    uc.mem_write(0x40000400, binary)
    uc.mem_write(base, (ROOT / 'out/platform/runtime/runtime.bin').read_bytes())
    uc.mem_map(0x47000000, 0x10000)
    uc.mem_map(0x46c70000, 0x20000)
    uc.mem_map(0x10000000, 0x200000)
    uc.mem_map(0x80000000, 0x10000)
    pitch, stack = 0x47001000, 0x47008000
    arrivals = []

    done = 0x4700fff0

    def stop(u, address, size, user):
        if address in (CAPTURE_END, CONTINUE, SKIP, 0x4009f98c, 0x4003667a, done):
            arrivals.append(address)
            u.emu_stop()
    uc.hook_add(UC_HOOK_CODE, stop, begin=1, end=0)

    def note(track, slot, value):
        before = [0x12340000 + i for i in range(16)]
        before[4], before[7], before[10], before[15] = slot, track, pitch, stack
        uc.reg_write(UC_M68K_REG_SR, 0x2700)
        for reg, val in zip(REGS, before):
            uc.reg_write(reg, val)
        uc.mem_write(pitch - 1, bytes((0xa5, value, 0x5a)))
        arrivals.clear()
        uc.emu_start(SITE, 0, count=500)
        result = uc.mem_read(pitch, 1)[0]
        assert arrivals == [SKIP if result >= 128 else CONTINUE]
        after = [uc.reg_read(reg) for reg in REGS]
        before[1] = (before[1] & ~255) | result  # displaced move.b
        assert after == before, (track, slot, value, before, after)
        assert uc.mem_read(pitch - 1, 3) == bytes((0xa5, result, 0x5a))
        return result

    def capture(track, value, transpose=64, extra=0, scale=0):
        before = [0x12340000 + i for i in range(16)]
        frame, lane = 0x47004000, 0x47002000
        before[7], before[13], before[14], before[15] = track, lane, frame, stack
        uc.reg_write(UC_M68K_REG_SR, 0x2700)
        for reg, val in zip(REGS, before):
            uc.reg_write(reg, val)
        uc.mem_write(lane + 0x220, bytes((value,)))
        uc.mem_write(lane + 0x22c, bytes((transpose,)))
        uc.mem_write(0x46c7a124 + track, bytes((extra & 255,)))
        uc.mem_write(frame - 64, scale.to_bytes(4, 'big'))
        arrivals.clear()
        uc.emu_start(CAPTURE, 0, count=1000)
        assert arrivals == [CAPTURE_END]
        before[4] = track * 4  # displaced stock bookkeeping
        assert [uc.reg_read(reg) for reg in REGS] == before
        assert uc.mem_read(frame - 43, 1)[0] == track * 4
        assert uc.mem_read(lane + 0x220, 1)[0] == value
        return uc.mem_read(root + track, 1)[0]

    def select(track, delta):
        uc.reg_write(UC_M68K_REG_A7, stack)
        uc.reg_write(UC_M68K_REG_D0, track)
        uc.reg_write(UC_M68K_REG_D1, delta & 0xffffffff)
        uc.mem_write(stack, done.to_bytes(4, 'big'))
        arrivals.clear()
        uc.emu_start(sym['bf_select'], 0, count=2000)
        assert arrivals == [done]
        assert uc.reg_read(UC_M68K_REG_A7) == stack + 4
        return uc.mem_read(sources, 8)

    assert uc.mem_read(root, 8) == b'\xff' * 8
    assert uc.mem_read(sources, 8) == bytes(8)
    assert capture(0, 60) == 36
    assert note(1, 0, 48) == 48  # OFF is the default
    uc.mem_write(root, b'\xff' * 8)
    assert select(1, 1) == bytes((0, 1, 0, 0, 0, 0, 0, 0))
    assert note(1, 0, 48) == 48  # follower before first leader
    for n in range(128):
        expected = 36 + n % 12
        assert capture(0, n) == expected
        assert note(0, 0, n) == n
        assert uc.mem_read(root, 1)[0] == expected
        assert note(1, 0, 72) == expected
        for slot in (1, 2, 3):
            assert note(0, slot, 76) == 76  # leader chord cannot replace root
            assert note(1, slot, 76) == 255  # bass is monophonic
        for track in range(2, 8):
            assert capture(track, n) == expected
            assert note(track, 0, n) == n
        for track in range(8):
            assert note(track, 0, 255) == 255  # absent/out-of-range note
        assert uc.mem_read(root, 1)[0] == expected
    assert capture(0, 60) == 36
    for arp_note in (60, 64, 67, 64):
        assert note(0, 0, arp_note) == arp_note
        assert note(1, 0, 48) == 36
    assert capture(0, 65) == 41
    for arp_note in (65, 69, 72, 69):
        assert note(0, 0, arp_note) == arp_note
        assert note(1, 0, 48) == 41
    assert capture(0, 60, transpose=66, extra=3) == 41
    assert capture(0, 60, transpose=62, extra=-3) == 43
    assert capture(0, 255) == 43
    assert capture(0, 0, transpose=63) == 43
    assert capture(0, 127, transpose=65) == 43
    assert capture(0, 61, scale=12) == 36  # C# -> C in C major
    assert capture(0, 66, scale=12) == 41  # F# -> F in C major
    assert capture(0, 61, scale=10) == 37  # C# belongs to D major
    assert capture(0, 61, transpose=66, scale=12) == 38  # transpose THEN scale
    # All 56 source/follower pairs, independent of output MIDI channels.
    for follower in range(8):
        for leader in range(8):
            if follower == leader:
                continue
            uc.mem_write(sources, bytes(8))
            # Selection skips the follower itself.
            select(follower, leader + 1 - (leader > follower))
            assert uc.mem_read(sources + follower, 1)[0] == leader + 1
            capture(leader, 65)
            assert note(follower, 0, 60) == 41
            select(follower, -8)
            assert note(follower, 0, 60) == 60
    uc.mem_write(sources, bytes(8))
    select(1, 1)                 # T2 -> T1
    select(2, 2)                 # T3 -> T2 -> T1
    assert select(0, 1)[0] == 4  # T1 cannot choose itself, T2 or T3
    select(0, -1)                # OFF, skipping those same cycles
    capture(0, 67)
    assert note(2, 0, 48) == 43
    assert select(7, 1000)[7] == 7  # clamps at T7, skips itself
    assert select(7, -1000)[7] == 0
    assert select(99, 1)[7] == 0

    # Real pre-loop hook: T8's root arrives before T2's same-tick note.
    uc.mem_write(sources, bytes((0, 8, 0, 0, 0, 0, 0, 0)))
    frame = 0x47004000
    def pre_capture(mask=128, mute=0, channel=8, velocity=90, note_value=65, disabled=False):
        uc.mem_write(frame - 42, mask.to_bytes(4, 'big'))
        uc.mem_write(frame - 37, bytes((mute,)))
        uc.mem_write(0x80006676, bytes(7) + bytes((255 if disabled else 0,)))
        uc.mem_write(0x8000666e, bytes(8))
        setup = 0x46c76dc0 + 7 * 68
        lane = 0x46c76dc0 + 7 * 32
        uc.mem_write(setup + 32, bytes((channel,)))
        uc.mem_write(setup + 49, bytes((0,)))
        uc.mem_write(lane + 0x220, bytes((note_value, velocity)))
        uc.mem_write(lane + 0x22c, bytes((64,)))
        uc.mem_write(0x46c7a12b, bytes((0,)))
        uc.reg_write(UC_M68K_REG_A6, frame)
        uc.reg_write(UC_M68K_REG_A7, stack)
        arrivals.clear()
        before = [uc.reg_read(r) for r in REGS]
        uc.emu_start(0x4009f986, 0, count=4000)
        before[8] = 0x80006676  # displaced lea
        assert [uc.reg_read(r) for r in REGS] == before
        assert arrivals == [0x4009f98c]
        return uc.mem_read(root + 7, 1)[0]
    uc.mem_write(root + 7, b'\xff')
    assert pre_capture(disabled=True) == 255
    assert pre_capture(mask=0) == 255
    assert pre_capture(mute=128) == 255
    assert pre_capture(channel=0) == 255
    assert pre_capture(velocity=0) == 255
    assert pre_capture(note_value=255) == 255
    assert pre_capture() == 41
    assert note(1, 0, 48) == 41
    assert pre_capture(note_value=67) == 43
    assert note(1, 0, 48) == 43

    uc.mem_write(sources, bytes((2, 1, 0, 0, 0, 0, 0, 0)))
    assert note(1, 0, 48) == 48  # bounded even for corrupt cyclic RAM
    uc.mem_write(sources + 1, b'\xff')
    assert note(1, 0, 48) == 48

    for value in range(10):
        uc.reg_write(UC_M68K_REG_A7, stack)
        uc.mem_write(stack, b''.join(v.to_bytes(4, 'big') for v in (done, pitch, value)))
        uc.mem_write(pitch, b'xxxxxxxx')
        arrivals.clear()
        uc.emu_start(sym['bf_format'], 0, count=100)
        assert arrivals == [done]
        expected = f'T{value}' if 1 <= value <= 8 else 'OFF'
        assert bytes(uc.mem_read(pitch, len(expected)+1)) == expected.encode()+b'\0'
    print('  [ok] machine code: 56 routes, OFF, chains/cycles, 128 roots, arp isolation, same-tick T8 source, gates, note-offs path, formatters, registers')


def fixture(source, dest, arp=False, leader=0):
    import ab_fixture
    from hw import ot_project as otp
    ab_fixture.prepare(source, dest)
    # Serialized MIDI data: MTRA has three masks then 64 x 32-byte locks.
    # Part MIDI page-1 = body+0x3e2, setup = body+0x4e2 (36 bytes/track).
    # Proven below by the stock image's notes/channels/velocities on UART0.
    steps = ({2: 60, 4: 65, 8: 67},
             {0: 48, 2: 48, 3: 48, 6: 48, 8: 48, 10: 48},
             {1: 72, 5: 74, 9: 76})
    steps = {leader: steps[0], 1: steps[1], 2: steps[2]}
    for path in dest.glob('bank*.work'):
        def mutate(data):
            for part in range(8):
                base = otp.PART_BASE + part * otp.PART_STRIDE + 9
                for t in range(8):
                    at = base + 0x3e2 + 32 * t
                    data[at:at+32] = bytes.fromhex(
                        '3c 64 06 40 40 40 20 20 20 00 00 00 40 00 00 05 '
                        '00 06 40 00 7f 00 00 40 00 00 00 00 00 00 00 00')
                    if arp and t == leader:
                        data[at+2] = 18  # enough time for the arp to walk the chord
                        data[at+3:at+5] = bytes((68, 71))  # major third and fifth
                        data[at+14] = 1  # UP
                        data[at+15] = 3  # fast enough for three notes before F
                    channel = {7: 13, 1: 5, 2: 3}.get(t, 0) if leader == 7 else t + 1
                    data[base + 0x4e2 + 36*t] = channel if t in steps else 0
            for p in range(16):
                for t in range(8):
                    at = 0x492e + p * 0x8eec + t * 0x8b9
                    assert data[at:at+4] == b'MTRA'
                    data[at+9:at+33] = bytes(24)
                    data[at+0x39:at+0x839] = b'\xff' * 2048
                    data[at+0x31:at+0x33] = bytes((16, 2))
                    if p == 0 and t in steps:
                        data[at+9:at+17] = sum(1 << s for s in steps[t]).to_bytes(8, 'big')
                        for s, n in steps[t].items():
                            lock = at + 0x39 + s * 32
                            data[lock:lock+2] = bytes((n, 90+t))
                            if t == 1 and s == 3:
                                data[lock+2] = 12  # held across the F root change
                            if t == leader and s == 4:
                                data[lock+3] = 68  # F + A: first NOTE remains root
                            if t == 1 and s == 8:
                                data[lock+3] = 71  # extra fifth suppressed in bass mode
        otp._bank_write(dest, int(path.stem[4:]), mutate, guard=False)
    for path in dest.glob('project.*'):
        raw = re.sub(rb'\[SAMPLE\].*?\[/SAMPLE\]\r?\n', b'', path.read_bytes(), flags=re.S)
        path.write_bytes(raw)


def notes(raw):
    """Decode running status; discard real-time bytes without losing state."""
    status, data, result, sysex = None, [], [], False
    for b in raw:
        if b >= 0xf8:
            continue
        if b == 0xf0:
            status, data, sysex = None, [], True
        elif b == 0xf7:
            sysex = False
        elif sysex:
            continue
        elif b & 128:
            status, data = (b if b < 0xf0 else None), []
        elif status is not None:
            data.append(b)
            if len(data) == (1 if status & 0xf0 in (0xc0, 0xd0) else 2):
                if status & 0xf0 in (0x80, 0x90):
                    result.append(('on' if status & 0xf0 == 0x90 and data[1] else 'off',
                                   (status & 15)+1, data[0], data[1]))
                data = []
    return result


def port_case(image, project, arp=False, leader=0, enabled=True):
    work = OUT / ("off" if not enabled else "reverse-arp" if leader and arp else "reverse" if leader else "arp" if arp else "chords")
    work.mkdir(parents=True, exist_ok=True)
    import emu_card
    fixture(project, work / 'project', arp=arp, leader=leader)
    card, _ = emu_card.stage_project(work / 'project', 'OCTABAM', 'BASS', tree=work / 'tree')
    (work / 'card.img').write_bytes(card)
    results, hashes = {}, {}
    for label, firmware in [('stock', ROOT / 'out/raw/section_3_MAIN_OS.bin'), ('patched', image)]:
        hashes[label] = hashlib.sha256(firmware.read_bytes()).hexdigest()
        capture = work / f'{label}.midi'
        log = work / f'{label}.log'
        cmd = [str(ROOT / 'out/emu/ot_emu'), '--image', str(firmware),
               '--card', str(work/'card.img'), '--set', 'OCTABAM', '--project', 'BASS',
               '--sequencer', '--internal-clock', '--frames', '7000', '--load-ms', '90000',
               '--midi-out', str(capture), '--card-out', str(work/f'{label}-card.img')]
        if label == 'patched' and enabled:
            cmd += ['--step', '-:poke:0x100b14cc=1',
                    '--step', f'-:call:{symbols()["bf_encoder"]:#x},3,{leader + 1 - (leader > 1)}']
        with log.open('w') as f:
            proc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        text = log.read_text()
        assert proc.returncode == 0 and 'run ended REACHED' in text, log
        assert 'load run ended: LOAD PROJECT handled' in text, log
        events = notes(capture.read_bytes())
        results[label] = events
        (work/f'{label}-notes.json').write_text(json.dumps(events, indent=2)+'\n')
        # Firmware must not write the transformed pitches back to the bank.
        files = emu_card.extract_image((work/f'{label}-card.img').read_bytes())
        for path in (work/'project').glob('bank*.*'):
            key = f'OCTABAM/BASS/{path.name}'
            assert files[key] == path.read_bytes(), key
        held = set()
        for kind, ch, pitch, velocity in events:
            key = ch, pitch
            if kind == 'on':
                assert key not in held, ('duplicate note-on', label, key)
                held.add(key)
            else:
                assert key in held, ('unmatched note-off', label, key)
                held.remove(key)
        assert not held, ('hanging notes', label, held)
    stock, patched = results['stock'], results['patched']
    if not enabled:
        assert stock == patched
        print('  [ok] port UART (OFF): all MIDI events identical to stock')
        return dict(status='pass', image_sha256=hashes)
    leader_ch = 13 if leader == 7 else leader + 1
    bass_ch = 5 if leader == 7 else 2
    for ch in (leader_ch, 3):
        assert [e for e in stock if e[1] == ch] == [e for e in patched if e[1] == ch]
    leader_notes = [e[2] for e in stock if e[:2] == ('on', leader_ch)]
    if arp:
        assert {60, 64, 67, 65, 69, 72, 71, 74} <= set(leader_notes), leader_notes
        # Regression: an E arp note must not turn the next C bass into E.
        e = patched.index(('on', leader_ch, 64, 90+leader))
        next_bass = next(event for event in patched[e+1:] if event[:2] == ('on', bass_ch))
        assert next_bass == ('on', bass_ch, 36, 91), next_bass
    else:
        assert leader_notes == [60, 65, 69, 67]
    assert [e[2] for e in stock if e[:2] == ('on', 3)] == [72, 74, 76]
    bass = [e for e in patched if e[:2] == ('on', bass_ch)]
    assert [e[2] for e in bass] == [48, 36, 36, 41, 43, 43], bass
    assert all(e[3] == 91 for e in bass)
    # F starts while the old C bass is still held; its release stays C.
    f = patched.index(('on', leader_ch, 65, 90+leader))
    assert patched.index(('off', bass_ch, 36, 0), f) < patched.index(('on', bass_ch, 41, 91))
    print(f'  [ok] port UART ({work.name}): independent rhythm, C/F/G, same-step order, held-note release, other tracks and stored banks')
    return dict(status='pass', leader_notes=leader_notes, bass_notes=[e[2] for e in bass], image_sha256=hashes)



def panel_gate(image):
    """Use UART1 key/encoder reports, not direct writes to module settings."""
    work = OUT/'ui'
    work.mkdir(exist_ok=True)
    card = OUT/'chords/card.img'
    sym = symbols()
    def script(actions):
        lines, time = [], 100
        for kind, value in actions:
            if kind == 'key':
                lines += [f'{time} key {value} down', f'{time+50} key {value} up']
                time += 250
            elif kind == 'setup':
                lines += [f'{time} key 0x2d down', f'{time+50} key 0x22 down',
                          f'{time+100} key 0x22 up', f'{time+150} key 0x2d up']
                time += 400
            else:
                lines += [f'{time} enc 3 {value}']
                time += 250
        return '\n'.join(lines + [f'{time+300} quit'])+'\n'
    open_t2 = [('key', '0x35'), ('key', '0x11'), ('setup', None)]
    # Set two followers, then return to T2 and confirm the displayed selection.
    linked = open_t2 + [('enc', 1), ('key', '0x32'), ('key', '0x12'),
                        ('setup', None), ('enc', 1), ('key', '0x32'),
                        ('key', '0x11'), ('setup', None)]
    # T1 skips self/T2/T3 (cycles), reaches T4, then can return to OFF.
    disabled = linked + [('key', '0x32'), ('key', '0x10'), ('setup', None),
                         ('enc', 1), ('enc', -1), ('key', '0x32'),
                         ('key', '0x11'), ('setup', None), ('enc', -1)]
    for name, actions, expected in [
            ('t2-t1', linked, bytes((0, 1, 1, 0, 0, 0, 0, 0))),
            ('t2-off', disabled, bytes((0, 0, 1, 0, 0, 0, 0, 0))),
            ('reboot-off', open_t2, bytes(8))]:
        events, log = work/f'{name}.txt', work/f'{name}.log'
        events.write_text(script(actions))
        before, after = work/f'{name}-before.bin', work/f'{name}-after.bin'
        state = work/f'{name}-state.bin'
        # Stock working-Part mirror (four Parts, stride 0x18b2), not live lanes.
        cmd = [str(ROOT/'out/emu/ot_emu'), '--image', str(image), '--card', str(card),
               '--set', 'OCTABAM', '--project', 'BASS', '--load-ms', '90000', '--mkii',
               '--step', f'-:dump:0x100a4ed0,25288={before}',
               '--live-script', str(events), '--lcd', str(work/f'{name}.lcd'),
               '--mem-dump', f'{sym["bf_sources"]:#x},8={state};0x100a4ed0,25288={after}']
        with log.open('w') as f:
            proc = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
        assert proc.returncode == 0 and 'ended on quit' in log.read_text(), log
        assert state.read_bytes() == expected, (name, state.read_bytes())
        assert before.read_bytes() == after.read_bytes(), (name, 'Part mirror changed')
        subprocess.run([sys.executable, str(ROOT/'tools/emu/lcd_view.py'),
                        str(work/f'{name}.lcd'), '--png', str(work/f'{name}.png')], check=True)
    print('  [ok] UART panel: RFOL selection, shared source, track reopening, OFF, reboot defaults; Part mirror unchanged')


def port_gate(image, project):
    (OUT/'result.json').unlink(missing_ok=True)
    cases = {name: port_case(image, project, arp=arp)
             for name, arp in [('chords', False), ('arp', True)]}
    cases['reverse'] = port_case(image, project, leader=7)
    cases['reverse-arp'] = port_case(image, project, arp=True, leader=7)
    cases['off'] = port_case(image, project, enabled=False)
    panel_gate(image)
    (OUT/'result.json').write_text(json.dumps(dict(status='pass', cases=cases,
                                                  hardware_tested=False), indent=2)+'\n')


def main():
    global OUT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('remix', nargs='?', default='bass-follow')
    ap.add_argument('--project', default=os.environ.get('OT_PROJECT') or None)
    a = ap.parse_args()
    if a.remix != 'bass-follow':
        OUT = ROOT/'out'/f'{a.remix}-bass-follow'
    OUT.mkdir(parents=True, exist_ok=True)
    image = ROOT/'out/mainos_bus.bin'
    machine_gate(image)
    if a.project:
        port_gate(image, pathlib.Path(a.project).expanduser())
    else:
        print('  [SKIP] port project test: supply --project DIR or OT_PROJECT (source is only read)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
