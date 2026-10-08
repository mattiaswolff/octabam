#!/usr/bin/env python3
"""Project save/load, restart and switching on disposable virtual cards."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import verify_midi_follow as f
from midi_fixture import fixture
from verify_midi_follow_settings import packed, NV
import emu_card
from hw import ot_project as otp

ROOT = f.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--build-root', type=Path, default=ROOT)
    ap.add_argument('--resume', action='store_true', help='reuse this gate\'s checked save artifact')
    ap.add_argument('--reload-only', action='store_true', help='run native PROJECT RELOAD against the previous save artifact')
    ap.add_argument('--switch-only', action='store_true', help='run project changes against the previous save artifact')
    a = ap.parse_args()
    if a.reload_only or a.switch_only: a.resume = True
    a.build_root = a.build_root.resolve()
    out = ROOT / 'out/follow-settings-port' / a.build_root.name
    out.mkdir(parents=True, exist_ok=True)
    image = out / 'candidate.bin'
    image.write_bytes((a.build_root / 'out/mainos_bus.bin').read_bytes())
    f.ROOT = a.build_root
    sym = f.symbols()
    raw = subprocess.check_output(['m68k-elf-nm', str(a.build_root/'out/platform/runtime/runtime.elf')], text=True)
    has_harmony = ' mh_get' in raw
    project = out / 'project'
    fixture(a.project, project)
    for p in project.glob('project.*'):
        data = re.sub(rb'^#MIDI_(?:FOLLOW|HARMONY)[^\r\n]*\r?\n', b'', p.read_bytes(), flags=re.M)
        if has_harmony:
            data += b'\r\n#MIDI_HARMONY_TYPE_V1_T1=2\r\n#MIDI_HARMONY_ROOT_V1_T1=2\r\n'
        p.write_bytes(data)
    otp.write_stored(project)
    tree = out / 'tree'
    emu_card.stage_project(project, 'OCTABAM', 'BASS', tree=tree)
    second = tree / 'OCTABAM/SECOND'
    shutil.copytree(tree / 'OCTABAM/BASS', second, dirs_exist_ok=True)
    for p in second.glob('project.*'):
        p.write_bytes(p.read_bytes() + f'\r\n#MIDI_FOLLOW_V1_T2={packed(3, 0, 5, 2)}\r\n'.encode())
    empty = tree / 'OCTABAM/EMPTY'
    shutil.copytree(tree / 'OCTABAM/BASS', empty, dirs_exist_ok=True)
    card = out / 'card.img'
    card.write_bytes(emu_card.build_image(str(tree)))

    def run(name, script='1500 quit\n', extra=(), source_card=card, card_out=False):
        work = out / name; work.mkdir(exist_ok=True)
        panel = work / 'panel.txt'; panel.write_text(script)
        dump = ';'.join(f'{sym[n]:#x},8={work}/{n}.bin' for n in
                        ('bf_sources', 'bf_reg_modes', 'bf_reg_fixed', 'bf_reg_offsets', 'bf_roots'))
        dump += f';{NV:#x},24={work}/resume.bin;0x10000000,0x100000={work}/cs1.bin;0x100b14e2,10={work}/harmony.bin;0x100f8378,32={work}/project-name.bin'
        cmd = [str(ROOT/'out/emu/ot_emu'), '--image', str(image), '--card', str(source_card),
               '--set', 'OCTABAM', '--project', 'BASS', '--load-ms', '90000', '--mkii',
               '--rtc', '1800000000', '--live-script', str(panel), '--mem-dump', dump]
        if card_out: cmd += ['--card-out', str(work/'card.img')]
        cmd += list(map(str, extra))
        with (work/'run.log').open('w') as log:
            result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        assert result.returncode == 0, (name, work/'run.log')
        return work

    def settings(work):
        return tuple((work/f'{n}.bin').read_bytes() for n in
                     ('bf_sources', 'bf_reg_modes', 'bf_reg_fixed', 'bf_reg_offsets'))
    default = (bytes(8), bytes(8), bytes([3]*8), bytes(8))
    # Enter NOTE SETUP, select RFOL T1 on T2, then set FIXED 4 / SOURCE -1
    # using physical controls. Save through the stock PROJECT menu.
    panel = ('100 key 0x31 down\n150 key 0x31 up\n300 key 0x35 down\n350 key 0x35 up\n'
             '500 key 0x11 down\n550 key 0x11 up\n700 key 0x2d down\n800 key 0x22 down\n'
             '850 key 0x22 up\n900 key 0x2d up\n1100 enc 3 4\n1300 key 0x3b down\n1350 key 0x3b up\n'
             '1500 enc 2 4\n1700 enc 1 4\n1900 enc 2 -4\n2100 key 0x32 down\n2150 key 0x32 up\n')
    for at, key in zip(range(5000, 9200, 700), (0x1c, 0x21, 0x20, 0x31, 0x31)):
        panel += f'{at} key {key:#x} down\n{at+100} key {key:#x} up\n'
    save = out / 'save' if a.resume else run('save', panel + '40000 quit\n', card_out=True)
    expected = (bytes((0,1,0,0,0,0,0,0)), bytes((0,1,0,0,0,0,0,0)),
                bytes((3,4,3,3,3,3,3,3)), bytes((0,255,0,0,0,0,0,0)))
    assert settings(save) == expected, settings(save)
    files = emu_card.extract_image((save/'card.img').read_bytes())
    for filename in ('project.work', 'project.strd'):
        content = files[f'OCTABAM/BASS/{filename}']
        assert f'#MIDI_FOLLOW_V1_T2={packed(1,1,4,-1)}'.encode() in content, filename
        assert content.count(b'#MIDI_FOLLOW_V1_T') == 8
        if has_harmony:
            assert b'#MIDI_HARMONY_TYPE_V1_T1=2' in content
            assert b'#MIDI_HARMONY_ROOT_V1_T1=2' in content
    print('[ok] '+('reused saved project verified' if a.resume else 'physical RFOL/MODE/OCT edits and native SAVE to working/stored project files'), flush=True)

    for name, extra in (() if a.reload_only or a.switch_only else (('disk-load', ()), ('warm-resume', ('--no-post', '--cs1-in', save/'cs1.bin')))):
        result = run(name, extra=extra, source_card=save/'card.img')
        assert settings(result) == expected, (name, settings(result))
        if has_harmony: assert (result/'harmony.bin').read_bytes() == (save/'harmony.bin').read_bytes()
    if not a.reload_only and not a.switch_only:
        old = run('old-project', extra=('--cs1-in', save/'cs1.bin'))
        assert settings(old) == default
        corrupt = bytearray((save/'cs1.bin').read_bytes()); corrupt[NV-0x10000000+4] ^= 1
        corrupt_file = out/'corrupt-cs1.bin'; corrupt_file.write_bytes(corrupt)
        result = run('corrupt-resume', extra=('--no-post', '--cs1-in', corrupt_file), source_card=save/'card.img')
        assert settings(result) == default
        print('[ok] disk load, simulated power cycle, old-project defaults and corrupt resume record', flush=True)

    def key(at, code):
        return f'{at} key {code:#x} down\n{at+100} key {code:#x} up\n'
    # Make an unsaved RFOL edit through its real encoder, then use PROJECT
    # RELOAD. The saved record, rather than the current edit, must win.
    menu = key(100,0x31)+key(500,0x1c)+key(900,0x21)+key(1200,0x20)+key(1450,0x20)+key(4500,0x31)+key(6500,0x31)
    if not a.switch_only:
        result = run('project-reload', menu+'30000 quit\n', source_card=save/'card.img',
                     extra=('--step','-:poke:0x100b14cc=1','--step',f'-:call:{sym["bf_encoder"]:#x},3,4'))
        assert settings(result) == expected, settings(result)
        print('[ok] native PROJECT RELOAD restores saved Follow settings after an unsaved edit', flush=True)

    if a.reload_only:
        (out/'reload-receipt.json').write_text(json.dumps(dict(image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(), native_project_reload=True, hardware_tested=False), indent=2)+'\n')
        return

    # Invoke the actual project chooser routine with a name in injected RAM.
    # This exercises the two-pass native loader in the same running firmware.
    for name, want in (('SECOND', (bytes((0,3,0,0,0,0,0,0)), bytes(8),
                                      bytes((3,5,3,3,3,3,3,3)), bytes((0,2,0,0,0,0,0,0)))),
                       ('EMPTY', default)):
        ptr = 0x47001000
        poke = ';'.join(f'{ptr+i:#x}={b}' for i,b in enumerate(name.encode()+b'\0'))
        result = run('switch-'+name, '30000 quit\n',
                     extra=('--step', f'-:poke:{poke}', '--step', f'-:call:0x40023c7c,{ptr}'),
                     source_card=save/'card.img')
        assert (result/'project-name.bin').read_bytes().split(b'\0')[0] == name.encode()
        assert settings(result) == want, (name, settings(result))
        assert (result/'bf_roots.bin').read_bytes() == b'\xff'*8
    print('[ok] real project changes restore each project independently and clear stale roots', flush=True)
    (out/('switch-receipt.json' if a.switch_only else 'receipt.json')).write_text(json.dumps(dict(
        image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(), build_root=str(a.build_root),
        harmony=has_harmony, cases=2 if a.switch_only else 8, reused_save=a.resume, hardware_tested=False), indent=2)+'\n')


if __name__ == '__main__':
    main()
