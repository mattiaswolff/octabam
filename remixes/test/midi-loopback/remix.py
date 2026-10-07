"""Loopback prototype on stock effects, isolated from personal remixes."""
from remix.schema import Proof, Remix

REMIX = Remix(
    name="midi-loopback", family="mods", proof=Proof.PORT,
    proof_note="M1/ch1 note lifecycle and filter locks/LFO/panel CCs under RTOS; no hardware",
    doc="Stock effects plus the volatile M1 MIDI loopback prototype.",
    modules=("MIDI LOOPBACK", "FILTER", "EQUALIZER", "DJ EQ", "PHASER",
             "FLANGER", "CHORUS", "SPATIALIZER", "COMB FILTER", "COMPRESSOR",
             "LO-FI", "DELAY", "PLATE REV", "SPRING REV", "DARK REV"),
    fallback="NONE",
)
