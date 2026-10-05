# mattias-bass-follow compatibility candidate

The user's OCTABAM2 (`mattias-bus`, BUILD=2) selection plus
[BASS FOLLOW](../../../modules/bass-follow/README.md). On upstream `5a46eb52`, the baseline rebuilt
byte-for-byte to its saved MAIN_OS SHA-256
`6d171d708c00637d15e91f2c9e2727f27b3c1cc3ade5ed33f390c337f669c68c`.

All original modules and FX1/FX2 choices are retained. This candidate adds
RAM-only RFOL to each MIDI track's NOTE SETUP D. It has not been flashed.
Local build receipts are in `out/bass-follow/compatibility/` (not committed).

Build/check: `make check REMIX=mattias-bass-follow BUILD=2`.
The tag is reused only for local binary comparison; a hardware image needs a
new build number. This task does not install or copy firmware to a device.

Original size comparison (BUILD=2, upstream `5a46eb52`, 5 Oct 2026):

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

Validation of that original comparison on 5 Oct 2026:

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

## Upstream refresh

Rebased onto `faa32663` on 5 Oct 2026, preserving the same module selection.
This includes the BusDelay/BusVerb, Spectrum, Character and Modulation
optimizations and the SEND zero-level modulation fix. It does not add the
new optional CHARACTER TXTR module.

The updated candidate still links 31,204 bytes of ColdFire runtime and reserves
10,487,808 bytes of DRAM. MAIN_OS is 1,115,310 bytes, SHA-256
`0539534391bf838ec3756f2ca40c4467856099cf8379ab5b57c01f42b457330c`.
DSP program space now has 217 words free on A and 779 on B. These are storage
counts, not a measurement of CPU timing. The old baseline's DSP payload identity
claim above applies only to the original comparison, not to this upstream update.

`make check REMIX=mattias-bass-follow BUILD=2` passed all runnable checks again,
using a rebuilt ColdFire port and an isolated DSP host compiled from the updated
source. The project-dependent skips listed above still apply. The new controlled
Root Follow gate also checks for out-of-contract memory writes.
The expanded stock/patched MIDI suite passed eight cases, including a capture
proving the bass is held at the change boundary, switching RFOL OFF, and
switching its source T1 → T3. Both live changes preserve the old note's release
and leave no hanging notes. This remains a short sequencer fixture, not a
transport/project-transition or sustained-load test.
Current update receipts are in `out/upstream-update/`; original receipts remain
in `out/bass-follow/compatibility/`.
