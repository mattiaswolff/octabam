"""Stock effects and the experimental per-track MIDI root follower."""
from remix.schema import Proof, Remix

REMIX = Remix(
    name="bass-follow", family="mods", proof=Proof.PORT,
    proof_note="verify_bass_follow: stock/patched MIDI capture; not flashed",
    doc="Per-track RFOL source selection on MIDI NOTE SETUP; RAM-only bass following.",
    modules=("BASS FOLLOW", "FILTER", "EQUALIZER", "DJ EQ", "PHASER", "FLANGER",
             "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR", "LO-FI",
             "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
