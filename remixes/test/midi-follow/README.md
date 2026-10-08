# MIDI Follow test remix

Stock effects plus [MIDI FOLLOW](../../../modules/midi-follow/README.md).
MIDI NOTE SETUP knob D adds **RFOL: OFF / T1–T8**, independently per track.
Followers play bass roots in their chosen register; sources may play chords or arps.
RFOL, MODE and both octave settings are saved per track in the project. New
projects start with RFOL OFF, FIXED octave 3 and SOURCE offset 0. No Scale
Quantizer dependency.
Experimental, emulator testing only; no hardware claim.

Build/check: `make check REMIX=midi-follow`. The module README describes the
optional virtual-project/panel tests and the prototype's limitations.
