# MIDI Loopback test remix

Stock effects plus the experimental [MIDI Loopback module](../../../modules/midi-loopback/README.md).
Every track defaults to EXT; the emulator gate sets volatile INT/BOTH routes. This is a
development fixture with no panel setting, not a hardware candidate.

Build and verify with `make check REMIX=midi-loopback`. To exercise the
sequencer and receiver on a disposable project copy, use
`.venv/bin/python tools/verify/verify_midi_loopback.py --project /path/to/source-project`.
Add `--controls` for the filter CC-lock, MIDI LFO and live CC-knob scenarios.
See the module page for exact coverage and open limitations.

Add `--routing` for eight simultaneous tracks with mixed destinations.
