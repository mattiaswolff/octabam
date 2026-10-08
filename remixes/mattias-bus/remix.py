"""mattias-bus -- a bus-centred personal Octatrack remix.

The FX2 layout is deliberately a send/return rig: BusDelay on T1, BusVerb
on T5, SEND on the other sound tracks, and stock DELAY on the T8 master.
FX1 is deliberately a compact station bank: Spectrum, Character and
Modulation replace the stock chooser's Filter, Lo-Fi and Chorus positions.

This is a source selection only.  It must pass `make check REMIX=mattias-bus`
on a setup containing the user's own 1.40C before an image is considered for
flashing.
"""

from remix.schema import Proof, Remix


REMIX = Remix(
    name="mattias-bus",
    family="rig",
    proof=Proof.CHECK,
    proof_note="Combined development candidate; full checks and hardware acceptance pending",
    doc=("Personal bus rig: BusDelay/BusVerb/SEND; Spectrum, Character and "
         "Modulation on FX1; RLEN PLEN, Tuner, MIDI Follow, Scales and Harmony with Chord Play."),
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
        "MIDI PART STATE", "MIDI FOLLOW",
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
