"""Per-track internal MIDI routing with a native CHAN-press window."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof, SymbolRef

MODULE = Module(
    name="midi-loopback", key="MIDI LOOPBACK", kind=Kind.CF_PATCH,
    category=Category.MIDI_USB, author="mattiaswolff",
    author_url="https://github.com/mattiaswolff",
    doc="Press CHAN for per-Part EXT/INT/BOTH routing of proven MIDI notes and CCs.",
    proof=Proof.PORT, proof_note="Panel, native Part persistence and routing under emulator; no hardware",
    requires=("MIDI PART STATE",),
    linked=(Linked("loopback", "modules/midi-loopback/loopback.s", cpu="54455", dram=True),
            Linked("loopbacksettings", "modules/midi-loopback/settings.s", dram=True),
            Linked("loopbackpage", "modules/midi-loopback/page.s", dram=True)),
    detours=(
        Detour(0x4009f794, bytes.fromhex("4e56ff9848d73cfc"),
               "loopback", "lb_tick", "release held destinations after route/channel changes", pad_to=8),
        Detour(0x40005558, bytes.fromhex("487946c7e9744e93"),
               "loopback", "lb_receive", "MIDI task receives complete internal messages", pad_to=8),
        Detour(0x4009f22a, bytes.fromhex("4879400d808f48780003"),
               "loopback", "lb_live_cached", "panel CC before cached live send", pad_to=10),
        Detour(0x4009f25e, bytes.fromhex("243c400d808f2f420044"),
               "loopback", "lb_live_tail", "panel CC before live sender restores source track", pad_to=10),
    ),
    symbol_refs=tuple(SymbolRef(site, 0x40010bc8, "loopback", "lb_send",
                                "route a proven MIDI-track producer before DIN/USB")
                      for site in (0x4009fbae, 0x4009fcf6, 0x4009feee, 0x4009ffba,
                                   0x4009f8be, 0x4009fc50, 0x4009fcd4,
                                   0x4009f328, 0x400a0020)) + (
        SymbolRef(0x400bc556, 0x4004ae08, "loopbackpage", "lb_channel_press", "confirm CHAN then open MIDI ROUTING"),
        SymbolRef(0x400d3f20, 0x4003c770, "loopbackpage", "lb_channel_format", "CHAN internal/both marker"),),
    gates=(Gate('tools/verify/verify_midi_loopback_settings.py', venv=True, stage='image'),
           Gate('tools/verify/verify_midi_loopback_stress.py', venv=True, stage='image'),
           Gate("tools/verify/verify_midi_loopback.py", venv=True, stage="image"),),
)
