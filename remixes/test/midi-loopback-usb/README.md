# MIDI Loopback and USB MIDI test remix

Stock effects with [MIDI Loopback](../../../modules/midi-loopback/README.md)
and [USB-MIDI](../../../modules/usb-midi/README.md). The hooks are adjacent
and must coexist: USB mirrors at sender entry, loopback classifies selected
sequencer calls after the stock save frame. Both retain DIN output.

Development fixture only; loopback is OFF by default, with no panel setting.
Build with `make bus REMIX=midi-loopback-usb`, then run
`REMIX=midi-loopback-usb python3 tools/verify/verify_usb.py` and
`.venv/bin/python tools/verify/verify_midi_loopback.py midi-loopback-usb`.
The project gate also accepts `--project /path/to/source-project`.
Add `--controls` to test filter CC locks, MIDI LFO and live CC knobs.
On 7 October 2026 both gates passed, including all five project scenarios.
The loopback receipts and captures are in `out/midi-loopback-usb/`.
On 8 October the CC-lock/LFO/panel extension passed USB enumeration/RX/TX
and the filter-control scenarios, including exclusion of UART input with
CC Direct Connect OFF and ON. Control captures live in its `controls/` subdirectory.
No hardware use or USB timing proof is claimed.
