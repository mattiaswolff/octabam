"""Experimental M1 channel-1 loopback; volatile OFF/BOTH, no UI or storage."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof

MODULE = Module(
    name="midi-loopback", key="MIDI LOOPBACK", kind=Kind.CF_PATCH,
    category=Category.MIDI_USB, author="mattiaswolff",
    author_url="https://github.com/mattiaswolff",
    doc="Experimental M1/channel-1 internal mirror of sequenced notes and CCs; volatile, off by default.",
    proof=Proof.PORT, proof_note="M1/ch1 prototype: five RTOS project scenarios and machine-code gates; no hardware",
    linked=(Linked("loopback", "modules/midi-loopback/loopback.s", cpu="54455", dram=True),),
    detours=(
        Detour(0x40010bd0, bytes.fromhex("246f001c4ab9460ba978"),
               "loopback", "lb_send", "mirror selected producers after the USB sender hook", pad_to=10),
        Detour(0x40005558, bytes.fromhex("487946c7e9744e93"),
               "loopback", "lb_receive", "MIDI task receives complete internal messages", pad_to=8),
    ),
    gates=(Gate("tools/verify/verify_midi_loopback.py", venv=True, stage="image"),),
)
