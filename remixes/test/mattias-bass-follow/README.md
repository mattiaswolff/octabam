# mattias-bass-follow compatibility candidate

The user's OCTABAM2 (`mattias-bus`, BUILD=2) selection plus
[BASS FOLLOW](../../../modules/bass-follow/README.md). The baseline rebuilt
byte-for-byte to its saved MAIN_OS SHA-256
`6d171d708c00637d15e91f2c9e2727f27b3c1cc3ade5ed33f390c337f669c68c`.

All original modules and FX1/FX2 choices are retained. This candidate adds
RAM-only RFOL to each MIDI track's NOTE SETUP D. It has not been flashed.
Local build receipts are in `out/bass-follow/compatibility/` (not committed).

Build/check: `make check REMIX=mattias-bass-follow BUILD=2`.
The tag is reused only for local binary comparison; a hardware image needs a
new build number. This task does not install or copy firmware to a device.

Measured size comparison (BUILD=2, 5 Oct 2026):

| resource | OCTABAM2 baseline | with Root Follow | added |
|---|---:|---:|---:|
| linked ColdFire runtime | 30,524 B | 31,204 B | 680 B |
| MAIN_OS image | 1,114,801 B | 1,115,310 B | 509 B |
| shared DRAM reservation | 10,487,808 B | 10,487,808 B | 0 |
| free DSP A program words | 194 | 194 | 0 consumed |
| free DSP B program words | 774 | 774 | 0 consumed |

The 678-byte Root Follow unit includes 16 bytes of volatile settings/root
state; its combined placement adds two alignment bytes. Both DSP payloads are
byte-identical to the baseline. MIDI processing adds ColdFire CPU work; physical
CPU timing and hardware operation have not been measured.

Validation on 5 Oct 2026:

- `make check REMIX=mattias-bass-follow BUILD=2` passed all runnable gates,
  including the composed runtime boot. Without OT_PROJECT, the project-specific
  `verify_set`, `verify_modedefaults`, `verify_tempobus` and `verify_fx2lock` gates
  skipped; this is not full audio-project acceptance.
- `verify_bass_follow.py mattias-bass-follow --project <local template>` passed:
  all 56 routes in machine-code tests, five stock/patched MIDI captures, and
  three UART panel scenarios. Includes source arpeggiation, reverse track order,
  different output channels, held-note release, OFF, page reopening and reboot.
  Part mirror and stored banks remain unchanged.
- Root Follow's composed-image results are separately retained under
  `out/mattias-bass-follow-bass-follow/`. The compatibility receipt records the
  exact image hash in `out/bass-follow/compatibility/result.json`.

No hardware timing, physical DIN MIDI, or firmware flashing was tested.
