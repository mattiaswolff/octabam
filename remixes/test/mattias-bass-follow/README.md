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
source. At that stage the project-dependent gates still skipped; their later
results are recorded below. The new controlled
Root Follow gate also checks for out-of-contract memory writes.
The expanded stock/patched MIDI suite passed eight cases, including a capture
proving the bass is held at the change boundary, switching RFOL OFF, and
switching its source T1 → T3. Both live changes preserve the old note's release
and leave no hanging notes. That suite uses a short sequencer fixture, not a
transport/project-transition or sustained-load test.
Current update receipts are in `out/upstream-update/`; original receipts remain
in `out/bass-follow/compatibility/`.

## Extended emulator checks (5 Oct 2026)

The same candidate hash above was tested with
`tools/verify/verify_bass_follow_safety.py`; reproduction commands are in the
[module README](../../../modules/bass-follow/README.md). No Root Follow firmware
code changed during this testing. The emulator now honors `--midi-out` after
interactive `quit`, allowing complete MIDI capture alongside the JIT DSPs.

- Seven stock/patched transition scenarios passed: held-note boundary, STOP,
  restart, pattern-boundary hold, pattern change, Part change and project change.
  The Part and project cases also change MIDI channels. All completed transitions
  release their notes; unrelated MIDI tracks and stored banks remain unchanged.
- A 120-second RFOL-OFF load test passed with 19,580 note events and no hanging
  notes. Eight dense MIDI tracks ran beside eight FLEX tracks, both bus effects,
  the selected FX1 effects, LFOs and parameter locks. Panel input switched through
  A01–A04 / Parts 1–4. All eight audio stems were nonzero, all 240 capture blocks
  contained audio, and the checked DSP counters were zero.
- The updated test runner passed a 20-second RFOL-active run with 3,580 note
  events, all four patterns/Parts, eight active audio stems and zero checked DSP
  counters. Its private fixture is byte-identical to the earlier load fixture.
- A subsequent isolated 120-second RFOL-active run passed with 19,580 note
  events: 979 bass notes on each of the seven followers, plus 2,937 source chord
  notes. All notes released after STOP. All eight audio stems and all 240
  capture blocks were nonzero; all three pattern/Part switches passed. RFOL
  settings, valid roots, module instructions and stored banks remained intact;
  the checked DSP counters were zero. This used the same project/bank/sample
  bytes as the OFF control, with no competing emulator run from this task.
- The initial 120-second active run was rejected: `pullshort=1`, `stale=1`,
  `faulted=00`. The emulator's incomplete-pull path has a 100 ms wall-time bound;
  several emulator processes were running concurrently. Host contention is a
  possible cause, not an established explanation. The failed artifacts are kept
  in `out/bass-follow-safety/soak-follow-120s-dsp-rejected/`. That early runner
  aborted before STOP and MIDI export, so it supplies no final note-release proof.
  The isolated repeat above did not reproduce the timeout; the original failure
  remains part of the evidence rather than being treated as a passing run.
- The previously skipped `verify_set`, `verify_modedefaults`, `verify_tempobus`
  and `verify_fx2lock` checks all passed against a generated project for this
  remix. The emulator rebuild, five firmware-independent emulator tests and
  documentation checks passed.

Durations above are emulated playback time; these runs took longer on the host.
Results and captures are under `out/bass-follow-safety/`. These checks do not
qualify physical CPU timing, electrical MIDI, flash/boot or an external synth.
The saved original OCTABAM2 image remains unchanged. Nothing was flashed.
