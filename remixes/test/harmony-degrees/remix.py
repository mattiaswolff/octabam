"""Isolated degree-based Harmony candidate with all seven scale modes."""
from remix.schema import Proof, Remix

REMIX = Remix(
    name='harmony-degrees', family='mods', proof=Proof.CHECK,
    proof_note='Isolated build; degree component and port evidence on mattias-bus-degrees D0',
    doc='Degree/register Harmony roots, isolated from the current Harmony selection.',
    modules=('MIDI PART STATE', 'MIDI HARMONY', 'MIDI SCALES',
             'FILTER', 'EQUALIZER', 'DJ EQ', 'PHASER', 'FLANGER', 'CHORUS',
             'SPATIALIZER', 'COMB FILTER', 'COMPRESSOR', 'LO-FI', 'DELAY',
             'PLATE REV', 'SPRING REV', 'DARK REV'),
    fallback='NONE',
)
