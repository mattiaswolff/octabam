#!/usr/bin/env python3
"""Execute the built loopback and stock queue/receive code. No firmware bundled.

Default: narrow machine gates. --project DIR also runs the real sequencer,
RTOS and UART receiver under the ColdFire port on a disposable project copy.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import toolpath  # noqa: E402,F401
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn.m68k_const import *

Q = 0x46c7e974
STACK, DONE, MSG = 0x47008000, 0x4700fff0, 0x47001000
REGS = [UC_M68K_REG_D0, UC_M68K_REG_D1, UC_M68K_REG_D2,
        UC_M68K_REG_D3, UC_M68K_REG_D4, UC_M68K_REG_D5,
        UC_M68K_REG_D6, UC_M68K_REG_D7, UC_M68K_REG_A0,
        UC_M68K_REG_A1, UC_M68K_REG_A2, UC_M68K_REG_A3,
        UC_M68K_REG_A4, UC_M68K_REG_A5, UC_M68K_REG_A6]


def symbols():
    nm = subprocess.check_output(["m68k-elf-nm", str(ROOT / "out/platform/runtime/runtime.elf")], text=True)
    return {n: int(a, 16) for a, n in re.findall(r"^([0-9a-f]+) [Tt] (lb_\w+)$", nm, re.M)}


class Machine:
    def __init__(self):
        self.sym = symbols()
        u = self.u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        u.ctl_set_cpu_model(UC_CPU_M68K_CFV4E)
        for a, size in ((0x40000000, 0x08000000), (0x10000000, 0x200000),
                        (0x80000000, 0x10000), (0xfc000000, 0x1000000)):
            u.mem_map(a, size)
        image = (ROOT / "out/mainos_bus.bin").read_bytes()
        u.mem_write(0x40000400, image)
        layout = json.loads((ROOT / "out/platform/layout.json").read_text())
        u.mem_write(layout["base"], (ROOT / "out/platform/runtime/runtime.bin").read_bytes())
        for site, symbol in ((0x40010bd0, "lb_send"), (0x40005558, "lb_receive"),
                             (0x4009f22a, "lb_live_cached"), (0x4009f25e, "lb_live_tail")):
            assert u.mem_read(site, 6) == b"\x4e\xf9" + self.sym[symbol].to_bytes(4, "big")
        self.stops = {DONE}
        self.arrived = None
        u.hook_add(UC_HOOK_CODE, self.stop)
        self.queue(Q, 0x47002000)
        self.queue(0x460d17ae, 0x47003000)
        self.put(0x400b966c, 0x47004000)  # UART TX ring
        self.put(0x400b9678, 4095)

    def stop(self, u, pc, size, data):
        if pc in self.stops:
            self.arrived = pc
            u.emu_stop()

    def put(self, at, value, size=4):
        self.u.mem_write(self.sym.get(at, at), value.to_bytes(size, "big"))

    def get(self, at, size=4):
        return int.from_bytes(self.u.mem_read(self.sym.get(at, at), size), "big")

    def queue(self, at, storage):
        self.u.mem_write(at, bytes(32))
        self.put(at + 16, 255)
        self.put(at + 20, storage)

    def call(self, at, args=(), regs=None, stop=DONE, return_pc=DONE):
        u = self.u
        self.stops, self.arrived = {stop}, None
        u.reg_write(UC_M68K_REG_SR, 0x2000)
        u.reg_write(UC_M68K_REG_A7, STACK)
        self.put(STACK, return_pc)
        for i, value in enumerate(args):
            self.put(STACK + 4 + i * 4, value)
        for reg, value in (regs or {}).items():
            u.reg_write(reg, value)
        u.emu_start(self.sym.get(at, at), 0, count=100000)
        assert self.arrived == stop, (at, hex(u.reg_read(UC_M68K_REG_PC)))
        return u.reg_read(UC_M68K_REG_D0)

    def capture(self, msg, source=0x4009fbb2, track=0):
        self.u.mem_write(MSG, bytes(msg))
        self.call("lb_capture", regs={UC_M68K_REG_D0: source,
                  UC_M68K_REG_D1: track, UC_M68K_REG_D2: len(msg), UC_M68K_REG_A0: MSG})

    def next(self):
        return bytes(self.u.mem_read(self.call("lb_next"), 3))

    def receiver_setup(self):
        self.put(0x46c82456, 0x40100000)
        self.u.mem_write(0x8000003f, bytes((0, 1, 2, 3, 4, 5, 6, 7)))
        self.put(0x80000047, 10, 1)
        self.put(0x80000049, 1, 1)
        self.put(0x8000004b, 1, 1)
        self.put(0x80000000, 7, 1)
        self.call(0x400054f4)  # stock incoming-note bookkeeping init

    def dispatch(self, msg):
        self.u.mem_write(MSG, bytes(msg))
        handler = self.get(0x400d6474 + (msg[0] >> 4) * 4)
        self.call(handler, (MSG, 0))


def machine_gate():
    m = Machine()
    assert m.get("lb_enabled", 1) == 0
    m.capture((0x90, 84, 100))
    assert m.get("lb_accepted") == 0
    m.put("lb_enabled", 1, 1)
    for msg, pc, track in [((0x90, 84, 100), 0x4000e11a, 0),
                           ((0x90, 84, 100), 0x4009fbb2, 1),
                           ((0x91, 84, 100), 0x4009fbb2, 0),
                           ((0xb0, 46, 70), 0x40040aa4, 0),
                           ((0xf8,), 0x4009fbb2, 0),
                           ((0x90, 128, 100), 0x4009fbb2, 0)]:
        m.capture(msg, pc, track)
    assert m.get("lb_accepted") == 0
    m.capture((0x90, 84, 100))
    m.capture((0xb0, 46, 70), 0x4009fef2)
    assert m.get(Q + 4) == 1, "only one wake token"
    assert m.next() == bytes((0x90, 84, 100))
    assert m.next() == bytes((0xb0, 46, 70))
    m.put("lb_enabled", 0, 1)
    m.capture((0x90, 84, 0), 0x4009f8c2)
    assert m.next() == bytes((0x90, 84, 0)), "OFF must still release owned notes"
    assert bytes(m.u.mem_read(m.sym["lb_owned"], 128)) == bytes(128)
    print("  [ok] source/track/channel filters, wake coalescing, OFF and note ownership")

    # Execute real stock queue receive, alternating external and internal.
    m = Machine(); m.put("lb_enabled", 1, 1)
    m.u.mem_write(MSG + 16, bytes((0x91, 60, 90)))
    m.call(0x40000c3c, (Q, MSG + 16))
    m.capture((0xb0, 46, 20), 0x4009fef2)
    m.capture((0xb0, 46, 30), 0x4009ffbe)
    assert m.next() == bytes((0xb0, 46, 20))
    assert m.next() == bytes((0x91, 60, 90))
    assert m.next() == bytes((0xb0, 46, 30))
    print("  [ok] native/internal fairness and complete-message ordering")

    m = Machine(); m.put("lb_enabled", 1, 1)
    m.put(0x46100b70, 0x91)  # DIN running status and half-message state
    m.put(0x46100b74, 60)
    for _ in range(256):
        m.call(0x40000c3c, (Q, MSG + 16))
    m.capture((0xb0, 46, 70), 0x4009fef2)
    assert m.get(Q + 4) == 256 and m.get("lb_wake_pending", 1) == 0
    assert m.next() == bytes((0xb0, 46, 70))
    assert m.get(0x46100b70) == 0x91 and m.get(0x46100b74) == 60
    print("  [ok] full native queue is not overrun; DIN framing state stays untouched")

    m = Machine(); m.put("lb_enabled", 1, 1)
    for note in range(127):
        m.capture((0x90, note, 100))
    m.capture((0xb0, 46, 70), 0x4009fef2)
    assert m.get("lb_dropped") == 1
    for note in range(127):
        m.capture((0x80, note, 0), 0x4009f8c2)
    assert m.get("lb_highwater") == 254
    for status in (0x90, 0x80):
        for note in range(127):
            assert m.next() == bytes((status, note, 100 if status == 0x90 else 0))
    for i in range(300):
        m.capture((0xb0, 46, i % 128), 0x4009fef2)
        assert m.next() == bytes((0xb0, 46, i % 128))
    assert m.get("lb_head") == m.get("lb_tail")
    assert m.get("lb_accepted") == m.get("lb_delivered") == 554
    print("  [ok] saturation reserves releases, whole-message drop, ring wrap and recovery")

    # Run installed sender detour, not only its helper. Caller is a proven
    # stock send site; stop at return before the sequencer continues.
    m = Machine(); m.put("lb_enabled", 1, 1)
    m.u.mem_write(MSG, bytes((0x90, 84, 100)))
    regs = {reg: 0x12340000 + i for i, reg in enumerate(REGS)}
    regs[UC_M68K_REG_D7] = 0
    m.put(STACK, 0x4009fbb2)
    # call() installs DONE; a tiny entry hook replaces only the test return PC.
    def caller(u, pc, size, data):
        m.put(STACK, 0x4009fbb2)
    hook = m.u.hook_add(UC_HOOK_CODE, caller, begin=0x40010bc8, end=0x40010bc8)
    m.call(0x40010bc8, (3, MSG), regs, stop=0x4009fbb2)
    m.u.hook_del(hook)
    for reg in REGS[2:8] + REGS[10:]:
        assert m.u.reg_read(reg) == regs[reg], reg
    assert m.get("lb_accepted") == 1
    assert m.get(0x400b967c) == 3
    assert bytes(m.u.mem_read(0x47004000 + 4093, 3))[::-1] == bytes((0x90, 84, 100))
    print("  [ok] installed sender preserves callee registers and actual stock UART bytes")

    # Both deliveries execute the installed stock handlers. Their deferred
    # RTOS/main-task continuation is additionally covered by --project.
    direct, internal = Machine(), Machine()
    for machine in (direct, internal):
        machine.receiver_setup()
    internal.put("lb_enabled", 1, 1)
    for msg, pc in [((0xb0, 46, 70), 0x4009fef2),
                    ((0x90, 84, 100), 0x4009fbb2),
                    ((0x80, 84, 0), 0x4009f8c2)]:
        direct.dispatch(msg)
        internal.capture(msg, pc)
        internal.dispatch(internal.next())
        for at, n in ((0x80000c50, 16), (0x400d64c2, 8), (0x46c7fb08, 1),
                      (0x46c80354, 32), (0x46c7fe4c, 64)):
            assert direct.u.mem_read(at, n) == internal.u.mem_read(at, n), hex(at)
        if msg[0] == 0x90:
            assert direct.get(0x400d64c2, 1) == 84
            assert direct.get(0x46c7fe4c) == 1
    assert direct.get(0x80000c50, 1) == 70
    assert direct.get(0x400d64c2, 1) == 255
    assert direct.get(0x46c7fe4c) == 0
    print("  [ok] CC46 and chromatic on/off match stock handler state and release count")

    # Run the stock live CC producer through both installed branches. The
    # parent return PC distinguishes the panel from the generic MIDI setter.
    for tail, param in ((tail, param) for tail in (False, True) for param in range(20, 30)):
        cases = [(0x4005542c, 1, 0, 1)]
        if param == 20:  # shared provenance filter, independent of CC slot
            cases += [(0x40054f74, 1, 0, 0), (0x40043b0e, 1, 0, 0),
                      (0x4005542c, 0, 0, 0), (0x4005542c, 1, 1, 0)]
        for parent, enabled, track, admitted in cases:
            m = Machine(); m.put("lb_enabled", enabled, 1)
            flag_byte, flag_bit = (0, param-18) if param < 24 else (1, param-24)
            for t in range(2):
                m.put(0x40171442 + 36*t, 1, 1)  # channel 1
                m.put(0x40171360 + 32*t + flag_byte, 1 << flag_bit, 1)
                m.put(0x46c76dc0 + 68*t + 30 + flag_byte, 1 << flag_bit, 1)
                m.put(0x46c76dc0 + 68*t + 32, 1, 1)
                m.put(0x46c76dc0 + 68*t + 52 + param-20, 34, 1)
            # Make the other track the active channel/CC owner for tail send.
            m.put(0x8000000c, (1 << (8+track)) if tail else (1 << (8+1-track)))
            visited = []
            hook = m.u.hook_add(UC_HOOK_CODE, lambda u, pc, n, data:
                               visited.append(pc) if pc in (0x4009f22a, 0x4009f25e) else None)
            m.call(0x4009eec8, (track, param, 80, 0), stop=parent, return_pc=parent)
            m.u.hook_del(hook)
            assert visited == [0x4009f25e if tail else 0x4009f22a], visited
            assert m.get("lb_accepted") == admitted, (tail, parent, enabled, track)
            assert m.get(0x400b967c) == 3  # exactly one external message
            if admitted:
                assert m.next() == bytes((0xb0, 34, 80))
    print("  [ok] CC1-10 cached/tail panel paths, OFF/M2 exclusion and generic-setter feedback exclusion")


def fixture(source, dest, length=6, control=None):
    import ab_fixture
    from hw import ot_project as otp
    ab_fixture.prepare(source, dest)
    for path in dest.glob("bank*.work"):
        def mutate(data):
            for part in range(8):
                base = otp.PART_BASE + part * otp.PART_STRIDE + 9
                for t in range(8):
                    at = base + 0x3e2 + 32 * t
                    data[at:at+32] = bytes.fromhex(
                        "54 64 06 40 40 40 20 20 20 00 00 00 40 00 00 05 "
                        "00 06 40 00 46 00 00 40 00 00 00 00 00 00 04 00")
                    data[at+2] = length
                    setup = base + 0x4e2 + 36 * t
                    data[setup] = 1 if t == 0 else 0
                    data[setup + 2] = 128  # PROG OFF
                    data[setup + 20] = 46  # CTRL1 CC1 setup, runtime +0x34
                    if control:
                        data[at+6:at+12] = bytes(6)  # all MIDI LFO speed/depth
                        if t == 0:
                            data[setup+20] = 34  # FX1 parameter 1: FILTER BASE
                            data[at+20] = 64
                            if control == "lfo":
                                data[at+6], data[at+9] = 32, 24  # SPD1, DEP1
                                data[setup+6] = 20  # PMTR = CC1
                                data[setup+9] = 0  # TRI
                                data[setup+30] = 4  # MULT x16
                                data[setup+33] = 0  # FREE
                if control:
                    data[base] = 4  # T1 FX1 FILTER
                    page = base + 0x11a
                    data[page+12:page+18] = bytes((20, 100, 0, 0, 0, 0))
            for p in range(16):
                end = 0x16 + (p + 1) * 0x8eec
                data[end-11:end-6] = bytes((16, 2, 64, 2, 0))
                for t in range(8):
                    at = 0x492e + p * 0x8eec + t * 0x8b9
                    assert data[at:at+4] == b"MTRA"
                    data[at+9:at+33] = bytes(24)
                    data[at+0x39:at+0x839] = b"\xff" * 2048
                    data[at+0x31:at+0x33] = bytes((16, 2))
                    if p == 0 and t == 0:
                        data[at+9:at+17] = (1).to_bytes(8, "big")
                        data[at+0x39:at+0x3c] = bytes((84, 100, length))
                        data[at+0x39+20] = 70
                        if control:
                            data[at+9:at+17] = (5 if control != "knob" else 0).to_bytes(8, "big")
                            data[at+0x39+20] = 32
                            data[at+0x39+64+20] = 96  # step 3 CC lock
        otp._bank_write(dest, int(path.stem[4:]), mutate, guard=False)
    values = dict(TRACK=7, MIDI_MODE=0, MIDI_AUTO_CHANNEL=10,
                  MIDI_AUDIO_TRK_CC_IN=1, MIDI_AUDIO_TRK_NOTE_IN=1,
                  MIDI_AUDIO_TRK_CC_OUT=3, MIDI_AUDIO_TRK_NOTE_OUT=3,
                  MIDI_CLOCK_RECEIVE=0, MIDI_TRANSPORT_RECEIVE=0,
                  MIDI_CLOCK_SEND=0, MIDI_TRANSPORT_SEND=0,
                  MIDI_PROGRAM_CHANGE_SEND=0, PATTERN_TEMPO_ENABLED=0,
                  TEMPOx24=2880)
    values.update({f"MIDI_TRIG_CH{i+1}": i for i in range(8)})
    if control == "knob":
        values.update(TRACK=0, MIDI_MODE=1)
    for path in dest.glob("project.*"):
        raw = re.sub(rb"\[SAMPLE\].*?\[/SAMPLE\]\r?\n", b"", path.read_bytes(), flags=re.S)
        for key, value in values.items():
            raw, count = re.subn(rb"(?m)^" + key.encode() + rb"=[^\r\n]*",
                                 key.encode() + b"=" + str(value).encode(), raw)
            assert count == 1, key
        path.write_bytes(raw)


def decode(raw):
    status, data, result = None, [], []
    for byte in raw:
        if byte >= 0xf8:
            continue
        if byte & 128:
            status, data = (byte if byte < 0xf0 else None), []
        elif status is not None:
            data.append(byte)
            if len(data) == (1 if status & 0xf0 in (0xc0, 0xd0) else 2):
                result.append([status, *data]); data = []
    return result


def port_gate(source, remix):
    import hashlib
    import emu_card
    # Keep standalone and USB receipts/captures separate.
    assert re.fullmatch(r"[a-z0-9-]+", remix), remix
    out = ROOT / "out" / remix
    out.mkdir(parents=True, exist_ok=True)
    fixture(source, out / "project")
    card, _ = emu_card.stage_project(out / "project", "OCTABAM", "LOOPBACK", tree=out / "tree")
    (out / "card.img").write_bytes(card)
    sym = symbols()
    outcomes = {}
    for label in ("off", "internal", "uart", "disable", "stop"):
        log, capture = out / f"{label}.log", out / f"{label}.midi"
        dumps = {key: out / f"{label}-{key}.bin" for key in ("level", "note", "held", "stats")}
        cmd = [str(ROOT / "out/emu/ot_emu"), "--image", str(ROOT / "out/mainos_bus.bin"),
               "--card", str(out / "card.img"), "--set", "OCTABAM", "--project", "LOOPBACK",
               "--sequencer", "--internal-clock", "--frames", "1200", "--load-ms", "90000",
               "--midi-out", str(capture), "--watch-mem", "0x400d64c2,1;0x80000c50,1",
               "--mem-dump", f"0x80000c50,16={dumps['level']};0x400d64c2,8={dumps['note']};"
               f"0x46c7fe4c,64={dumps['held']};{sym['lb_head']:#x},24={dumps['stats']}"]
        if label in ("internal", "disable", "stop"):
            cmd += ["--step", f"-:poke:{sym['lb_enabled']:#x}=1"]
        if label == "disable":
            cmd += ["--step", f"4:dump:0x400d64c2,1={out / 'before-disable.bin'}",
                    "--step", f"5:poke:{sym['lb_enabled']:#x}=0"]
        if label == "stop":
            fixture(source, out / "held-project", length=127)
            held_card, _ = emu_card.stage_project(out / "held-project", "OCTABAM", "LOOPBACK", tree=out / "held-tree")
            (out / "held-card.img").write_bytes(held_card)
            cmd[cmd.index("--card") + 1] = str(out / "held-card.img")
            cmd += ["--step", f"60:dump:0x400d64c2,1={out / 'before-stop.bin'}",
                    "--step", "80:poke:0x80000029=1", "--step", "80:call:0x4000a1e0,0"]
        if label == "uart":
            midi = out / "reference.midi"
            midi.write_text("40 b0 2e 46\n80 90 54 64\n500 80 54 00\n")
            cmd += ["--midi", str(midi)]
        with log.open("w") as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        text = log.read_text()
        assert result.returncode == 0 and "run ended REACHED" in text, str(log)
        assert "load run ended: LOAD PROJECT handled" in text, str(log)
        outcomes[label] = {key: path.read_bytes().hex() for key, path in dumps.items()}
        outcomes[label]["midi"] = decode(capture.read_bytes())
        print(f"  [port] {label}: level={dumps['level'].read_bytes()[0]}, "
              f"stats={outcomes[label]['stats']}, MIDI={outcomes[label]['midi']}", flush=True)
    off, internal, uart = (outcomes[k] for k in ("off", "internal", "uart"))
    assert off["level"][:2] == "7f"
    assert internal["level"] == uart["level"] and internal["level"][:2] == "46"
    assert internal["note"] == uart["note"] == "ff" * 8
    assert internal["held"] == uart["held"] == "00" * 64
    assert internal["midi"] == off["midi"], "internal mirror changed external MIDI"
    assert [0x90, 84, 100] in internal["midi"]
    assert [0xb0, 46, 70] in internal["midi"]
    assert outcomes["disable"]["note"] == outcomes["stop"]["note"] == "ff" * 8
    assert outcomes["disable"]["held"] == outcomes["stop"]["held"] == "00" * 64
    assert (out / "before-stop.bin").read_bytes() == bytes((84,)), "STOP test must start with a held note"
    assert (out / "before-disable.bin").read_bytes() == bytes((84,)), "OFF test must start with a held note"
    stats = bytes.fromhex(internal["stats"])
    vals = [int.from_bytes(stats[i:i+4], "big") for i in range(0, 24, 4)]
    assert vals[0] == vals[1] and vals[2] == vals[3] >= 3 and vals[4] == 0, vals
    receipt = {"image_sha256": hashlib.sha256((ROOT / "out/mainos_bus.bin").read_bytes()).hexdigest(),
               "runtime_sha256": hashlib.sha256((ROOT / "out/platform/runtime/runtime.bin").read_bytes()).hexdigest(),
               "stock_sha256": hashlib.sha256((ROOT / "out/raw/section_3_MAIN_OS.bin").read_bytes()).hexdigest(),
               "outcomes": outcomes, "scope": "ColdFire RTOS/sequencer and UART receiver; no DSP/audio or hardware proof"}
    (out / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("  [ok] real sequencer -> internal queue -> MIDI task -> audio state matches UART input")


def controls_gate(source, remix, only=None):
    """Real MIDI locks/LFO and the panel's encoder routine into T1 FILTER BASE."""
    import hashlib
    import emu_card
    assert re.fullmatch(r"[a-z0-9-]+", remix), remix
    out = ROOT / "out" / remix / "controls"
    out.mkdir(parents=True, exist_ok=True)
    sym, outcomes = symbols(), {}
    kinds = (only,) if only else ("locks", "lfo", "knob")
    for kind in kinds:
        fixture(source, out / f"{kind}-project", control=kind)
        card, _ = emu_card.stage_project(out / f"{kind}-project", "OCTABAM", "LOOPBACK", tree=out / f"{kind}-tree")
        card_path = out / f"{kind}-card.img"
        card_path.write_bytes(card)
        modes = {"locks": ("off", "on"), "lfo": ("off", "on", "receive-off"),
                 "knob": ("off", "on", "incoming", "direct")}[kind]
        for mode in modes:
            label = f"{kind}-{mode}"
            log, capture = out / f"{label}.log", out / f"{label}.midi"
            state, stats = out / f"{label}-filter.bin", out / f"{label}-stats.bin"
            cmd = [str(ROOT / "out/emu/ot_emu"), "--image", str(ROOT / "out/mainos_bus.bin"),
                   "--card", str(card_path), "--set", "OCTABAM", "--project", "LOOPBACK",
                   "--sequencer", "--internal-clock", "--frames", "1200", "--load-ms", "90000",
                   "--midi-out", str(capture), "--watch-mem", "0x80000822,1",
                   "--mem-dump", f"0x80000822,1={state};{sym['lb_head']:#x},24={stats}"]
            if mode != "off":
                cmd += ["--step", f"-:poke:{sym['lb_enabled']:#x}=1"]
            if mode == "receive-off":
                cmd += ["--step", "-:poke:0x80000049=0"]
            if kind == "knob":
                # CTRL1 page, encoder C = CC1, +16 from the Part's 64.
                cmd += ["--step", "-:poke:0x460d1687=3"]
                if mode in ("incoming", "direct"):
                    # Auto-channel CC36 changes M1 CC1 through the generic
                    # setter. Its external CC must not become new loopback.
                    midi_in = out / "incoming.midi"
                    midi_in.write_text("400 ba 24 50\n")
                    cmd += ["--midi", str(midi_in), "--step",
                            f"-:poke:0x8000004d={1 if mode == 'direct' else 0}"]
                else:
                    cmd += ["--step", "400:call:0x40055008,2,16"]
            with log.open("w") as stream:
                result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
            text = log.read_text()
            assert result.returncode == 0 and "run ended REACHED" in text, str(log)
            assert "load run ended: LOAD PROJECT handled" in text, str(log)
            raw = stats.read_bytes()
            counts = [int.from_bytes(raw[i:i+4], "big") for i in range(0, 24, 4)]
            midi = decode(capture.read_bytes())
            ccs = [msg[2] for msg in midi if msg[:2] == [0xb0, 34]]
            # Only the receiver's generic parameter writer, excluding load and
            # frame refresh stores. Compare every value, in order, with the wire.
            writes = [int(value, 16) for value in re.findall(
                r"\[0x80000822\] <- (0x[0-9a-f]+|0) \(1\) at pc 0x40054e22", text)]
            assert writes == (ccs if mode == "on" else []), (label, writes, ccs)
            outcomes[label] = dict(filter=state.read_bytes()[0], stats=counts, midi=midi, cc_values=ccs, filter_writes=writes)
            print(f"  [controls] {label}: filter={outcomes[label]['filter']}, CC34={ccs}, stats={counts}", flush=True)
        off, on = outcomes[f"{kind}-off"], outcomes[f"{kind}-on"]
        assert off["filter"] == 20, off
        assert on["cc_values"] and on["filter"] == on["cc_values"][-1], on
        assert on["midi"] == off["midi"], f"{kind}: external MIDI changed"
        assert on["stats"][2] == on["stats"][3] > 0 and on["stats"][4] == 0, on
        assert off["stats"][2] == 0, off
        if kind == "locks":
            assert on["cc_values"] == [32, 96], on
            assert 32 in on["filter_writes"] and 96 in on["filter_writes"], on
        if kind == "lfo":
            assert len(set(on["cc_values"])) >= 8, on
            assert len(set(on["filter_writes"])) >= 8, on
            assert outcomes["lfo-receive-off"]["filter"] == 20
            assert outcomes["lfo-receive-off"]["stats"][3] > 0
        if kind == "knob":
            assert 80 in on["cc_values"] and 80 in on["filter_writes"], on
            incoming = outcomes["knob-incoming"]
            assert incoming["cc_values"] == [80] and incoming["filter"] == 20, incoming
            assert incoming["stats"][2] == 0, incoming
            direct = outcomes["knob-direct"]
            assert direct["midi"] == [[0xb0, 36, 80]] and direct["filter"] == 20, direct
            assert direct["stats"][2] == 0, direct
    receipt = dict(image_sha256=hashlib.sha256((ROOT / "out/mainos_bus.bin").read_bytes()).hexdigest(),
                   runtime_sha256=hashlib.sha256((ROOT / "out/platform/runtime/runtime.bin").read_bytes()).hexdigest(),
                   stock_sha256=hashlib.sha256((ROOT / "out/raw/section_3_MAIN_OS.bin").read_bytes()).hexdigest(),
                   outcomes=outcomes, scope="ColdFire control state; no rendered audio or hardware proof")
    (out / (f"result-{only}.json" if only else "result.json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"  [ok] filter control scenarios passed: {', '.join(kinds)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("remix", nargs="?", default="midi-loopback")
    parser.add_argument("--project", type=pathlib.Path)
    parser.add_argument("--controls", action="store_true", help="run filter-control project scenarios instead of note lifecycle scenarios")
    parser.add_argument("--control-kind", choices=("locks", "lfo", "knob"), help="rerun one control group; requires --controls")
    args = parser.parse_args()
    if args.controls and not args.project:
        parser.error("--controls requires --project DIR")
    if args.control_kind and not args.controls:
        parser.error("--control-kind requires --controls")
    machine_gate()
    if args.project:
        if args.controls:
            controls_gate(args.project, args.remix, args.control_kind)
        else:
            port_gate(args.project, args.remix)
    else:
        print("  [not run] full RTOS/project gate: supply --project DIR")


if __name__ == "__main__":
    main()
