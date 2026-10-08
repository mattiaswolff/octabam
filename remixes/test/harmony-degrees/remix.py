"""Isolated degree-based Harmony candidate with all seven scale modes."""
from remix.schema import Proof, Remix

REMIX = Remix(
    name='harmony-degrees', family='mods', proof=Proof.CHECK,
    proof_note='Production replacement candidate; verification in progress',
    doc='Degree/register Harmony roots, isolated from the current Harmony selection.',
    modules=('MIDI HARMONY', 'HARMONY DEGREES', 'MIDI SCALES',
             'FILTER', 'EQUALIZER', 'DJ EQ', 'PHASER', 'FLANGER', 'CHORUS',
             'SPATIALIZER', 'COMB FILTER', 'COMPRESSOR', 'LO-FI', 'DELAY',
             'PLATE REV', 'SPRING REV', 'DARK REV'),
    fallback='NONE',
)
