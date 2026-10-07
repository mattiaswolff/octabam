"""Experimental M1 channel-1 loopback; volatile OFF/BOTH, no UI or storage."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof

MODULE = Module(
    name="midi-loopback", key="MIDI LOOPBACK", kind=Kind.CF_PATCH,
    category=Category.MIDI_USB, author="mattiaswolff",
    author_url="https://github.com/mattiaswolff",
    doc="Experimental M1/channel-1 mirror of notes, CC locks, MIDI CC LFOs and panel CC knobs; off by default.",
    proof=Proof.PORT, proof_note="M1/ch1 notes, filter locks/LFO and panel CCs under RTOS; no hardware",
    linked=(Linked("loopback", "modules/midi-loopback/loopback.s", cpu="54455", dram=True),),
    detours=(
        Detour(0x40010bd0, bytes.fromhex("246f001c4ab9460ba978"),
               "loopback", "lb_send", "mirror selected producers after the USB sender hook", pad_to=10),
        Detour(0x40005558, bytes.fromhex("487946c7e9744e93"),
               "loopback", "lb_receive", "MIDI task receives complete internal messages", pad_to=8),
        Detour(0x4009f22a, bytes.fromhex("4879400d808f48780003"),
               "loopback", "lb_live_cached", "panel CC before cached live send", pad_to=10),
        Detour(0x4009f25e, bytes.fromhex("243c400d808f2f420044"),
               "loopback", "lb_live_tail", "panel CC before live sender restores source track", pad_to=10),
    ),
    gates=(Gate("tools/verify/verify_midi_loopback.py", venv=True, stage="image"),),
)
