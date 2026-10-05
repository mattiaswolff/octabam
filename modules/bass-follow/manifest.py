"""Per-MIDI-track root follower with a volatile NOTE SETUP D selector."""
from remix.schema import Category, Detour, Gate, Kind, Linked, Module, Proof, Poke, SymbolRef

MODULE = Module(
    name="bass-follow", key="BASS FOLLOW", kind=Kind.CF_PATCH,
    category=Category.MIDI_USB, author="Local Octabam prototype", author_url="https://github.com/sambanks/octabam",
    proof=Proof.PORT, proof_note="verify_bass_follow: stock/patched MIDI capture; not flashed",
    doc="NOTE SETUP RFOL selects a source track; bass roots 36-47 plus follower TRAN/P-locks.",
    linked=(Linked("bassfollow", "modules/bass-follow/bass_follow.s", dram=True),),
    symbol_refs=(
        SymbolRef(0x400BC64E, 0x4003A8E8, "bassfollow", "bf_encoder", "NOTE SETUP D encoder"),
        SymbolRef(0x400D3F2C, 0, "bassfollow", "bf_format", "RFOL OFF/T1-T8 formatter"),
    ),
    pokes=(
        Poke(0x400D3F5C, bytes(4), bytes.fromhex("400467a4"), "RFOL text widget, like CHAN"),
        Poke(0x400D3E8A, b"----\0\0", b"RFOL\0\0", "NOTE SETUP D label"),
        Poke(0x400D3EFC, bytes.fromhex("00000080"), bytes.fromhex("00000009"), "RFOL nine values"),
        Poke(0x400D3FC8, bytes.fromhex("00000101"), bytes.fromhex("00000111"), "enable NOTE SETUP D"),
    ),
    detours=(Detour(0x4009F986, bytes.fromhex("41f980006676"),
                    "bassfollow", "bf_pre_capture", "capture all ordinary source triggers before any track emits"),
             Detour(0x40036674, bytes.fromhex("261524047003"),
                    "bassfollow", "bf_draw_value", "draw RFOL from per-track module RAM"),
             Detour(0x4009FB00, bytes.fromhex("2807e58c1d44ffd5"),
                   "bassfollow", "bf_capture",
                   "latch the original chord root independently of arp output", pad_to=8),
             Detour(0x4009FB80, bytes.fromhex("12126d0001a6"),
                   "bassfollow", "bf_note",
                   "resolve root before the sequencer records the emitted note"),),
    gates=(Gate("tools/verify/verify_bass_follow.py", stage="image", venv=True),),
)
