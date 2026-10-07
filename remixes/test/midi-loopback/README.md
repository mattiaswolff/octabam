# MIDI Loopback test remix

Stock effects plus the experimental [MIDI Loopback module](../../../modules/midi-loopback/README.md).
Loopback is OFF by default and enabled by the emulator gate. This is a
development fixture with no panel setting, not a hardware candidate.

Build and verify with `make check REMIX=midi-loopback`. To exercise the
sequencer and receiver on a disposable project copy, use
`.venv/bin/python tools/verify/verify_midi_loopback.py --project /path/to/source-project`.
See the module page for exact coverage and open limitations.
