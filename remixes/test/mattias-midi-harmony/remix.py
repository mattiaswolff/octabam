"""OCTABAM2 selection plus MIDI Follow, Scales and Harmony, isolated compatibility candidate."""
from remix.schema import Proof, Remix


REMIX = Remix(
    name="mattias-midi-harmony",
    family="mods",
    proof=Proof.PORT,
    proof_note="local OCTABAM2 compatibility candidate; not flashed",
    doc=("Personal bus rig: BusDelay/BusVerb/SEND; Spectrum, Character and "
         "Modulation on FX1; Mode Defaults, RLEN PLEN, Tuner, MIDI Follow, Scales and Harmony."),
    modules=(
        # Fixed FX2 send/return layout.
        "REVERB SERVER",
        "DELAY SERVER",
        "SEND",

        # The entire FX1 chooser: compact station bank, not stock FX1.
        "SPECTRUM",
        "CHARACTER",
        "MODULATION",

        "TEMPO SYNC",
        "RIG HOSTS",
        "TEMPO BUS",
        "FX2 LOCK",
        "MODE DEFAULTS",
        "DELAY",  # T8's master-track delay.

        # Requested firmware behaviour.
        "RLEN PLEN",
        "TUNER",
        "MIDI FOLLOW",
        "MIDI SCALES",
        "MIDI HARMONY",
    ),
    fallback="SEND",

    # Bus engines are assigned by RIG HOSTS rather than selected manually.
    hidden=("REVERB SERVER", "DELAY SERVER"),
    host_slots=(("DELAY SERVER", 2), ("REVERB SERVER", 2)),
    locked=("REVERB SERVER", "DELAY SERVER"),

    fx1=("SPECTRUM", "CHARACTER", "MODULATION"),
)
