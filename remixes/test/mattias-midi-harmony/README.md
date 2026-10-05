# Personal MIDI Harmony candidate

The personal bus remix plus MIDI Follow, MIDI Scales and MIDI Harmony.
HARM is NOTE SETUP F; RFOL is D. Extended KEY stays ARP SETUP F.
See the three module READMEs for independent behaviour and the reusable
verification protocol. This is a local candidate, not a flashed release.

## Local verification

The module checks passed independently for MIDI Scales, MIDI Harmony and
MIDI Follow, and together on the stock-effect remix. The personal selection
passed the shared gates and `check-remix` with the disposable audio project,
including boot, audio output, mode defaults, tempo bus, FX2 lock, all three
MIDI machine-code gates and the full Follow UART/panel regression suite.

The first shared bus run failed because the shared `dsp_host` binary lacked
`-pword`. Re-running `verify_onebus.py` with the existing isolated host whose
source matches this checkout passed; no firmware or assertion was weakened.
Use `DSP_HOST=/path/to/current/dsp_host` if the shared binary is stale (the
isolated build procedure is in the repository's AGENTS.md).

Reproduce the personal checks with a read-only local template:

```sh
OT_PROJECT=/path/to/template make check REMIX=mattias-midi-harmony
.venv/bin/python3 tools/verify/verify_midi_harmony_port.py --project /path/to/template
```

The reusable MIDI suite captures generated chords, stock arp, reverse source
order, added scales, keyboard releases and real project save/reload on virtual
CF. Receipts and captures remain under `out/`; no OS bytes are committed.
Physical MIDI, timing, battery retention and device flashing are untested.
