# MIDI concert stress verification — 8 October 2026

This pass targets failures that are difficult to expose with two tracks and
manual playing. Upstream `7b2984c8` is integrated into the module branches
and this remix. MIDI Loopback remains a separate prototype selection; its
stress results do not imply that it is part of this bus image.

## Reproduced failures and repairs

| Failure | Reproduction and evidence | Repair and regression |
| --- | --- | --- |
| Generated live notes on different tracks overwrite one another's release destination | Eight tracks play C/E/G on channels 1–8. The original port capture has 24 note-ons but only three releases, all on channel 8. Stock's live keyboard token is indexed by pitch alone. | Harmony now retains per-track stock release tokens. Separate, shared and paired channels drain correctly; eight arps and channel edits/OFF while held also pass. The helper uses the captured destination and coalesces shared direct channel/pitch owners. |
| A bypassed key cuts off a tone that a held Harmony chord still needs | Hold C/E/G, turn HARM OFF, then press/release E. The old boundary trace forwards E's note-off despite the chord's reference. | Intersecting bypass notes join the reference count. The reverse order adopts a previously bypassed note when a chord shares it. Both orders pass on all eight tracks; an unrelated HARM OFF control matches stock UART output. |
| Long injected-event runs corrupt the emulator's own stack | Each four-argument `callAsMain` leaked 16 bytes. Sustained churn halted at an invalid PC; the new minimal RTOS test fails on its first call with SP reduced by 16. | The harness reclaims caller arguments after a valid C ABI return and rejects callee stack imbalance. 2,048 calls preserve SP and return correct results; a deliberately imbalanced callee is rejected. The full note flood and churn scenarios pass with the rebuilt port. |

The first two are firmware defects. The third is a verification defect and
does not describe a crash observed on an Octatrack. The channel-loss capture
used pre-fix Harmony `1d9cea0f`; the repairs are `d3dbb4c4`. The RTOS regression
was red on support `9ad057df`, then passed with `71e97fed` and the stack-imbalance
guard in `eed82335`. Original failing logs are retained as
`out/concert-port-before.log` and `out/concert-bypass-before.log` in the Harmony
worktree, and `out/concert-stack-before.log` in the support worktree.

## Durable coverage

| Gate | Workload and assertions |
| --- | --- |
| `verify_midi_follow_stress.py` | All 40,320 eight-track chain permutations, 12,000 seeded routing edits, 56,080 routed outputs; cycles, invalid links, unknown roots, register/TRAN limits, per-track isolation and write guards. |
| `verify_midi_harmony_stress.py` | Three deterministic seeds, over 44,000 key edges, 1,024 concurrent physical keys; NOTE/triad/seventh and key/scale changes while held, overlapping tones, shuffled releases and exact reference counts. The combined image exercises all seven Scales modes across tracks. |
| `verify_midi_concert_port.py` | Thirteen combined full-firmware cases (twelve on standalone Harmony): 1,024 simultaneous notes, separate/shared/paired channels, both bypass orders, stock OFF parity, captured channel changes/OFF, eight arps, 80 churn cycles and eight-track sequencing. Checks exact expected live UART events, balanced notes, cleared ownership and unchanged bank files. Combined sequencing also uses an eight-track Follow chain; seven sustained CHANGE followers must each match the changing source’s note count and produce at least six distinct pitches. |
| `verify_midi_loopback_stress.py` | 48 eight-producer floods per selection, 49,152 CC attempts, 128 held notes, a stalled consumer, 255 occupied release-reserved slots, mass route changes, late offs, whole-message shedding, wrap/recovery and full native receive-queue fairness. All 18,384 admitted messages drain. Run on standalone and USB-combined selections. |
| `ot_rtos_test` | Repeated C ABI call return values and stack stability, plus a negative control that must reject a bad callee. Existing EMAC, peripheral and DSP tests also pass. |

The linked stress scripts are registered image gates. Supplying `OT_PROJECT`
to the Harmony stress gate also runs the port suite. Reproduce the selected
image’s complete gate set and port suite with:

```sh
make check REMIX=mattias-bus OT_PROJECT=/path/to/template
```

Or run the concert port scenarios separately:

```sh
.venv/bin/python tools/verify/verify_midi_concert_port.py --project /path/to/template
```

The scripts only read that source project and use disposable copies under
`out/`. Seeds, counts and image hashes are written to JSON receipts. The
standalone Harmony port run passed all 12 cases with 5,998 UART note events.
The combined port run passed all 13 cases with 7,534 UART note events. The
supplemental Chord Play panel suite passed all nine release, overlap and
width/spread scenarios. Both used image SHA-256
`810530f44964fe1d360a622928b98588d0591b336cc56e17b8b109763efea71a`.
Detailed module findings are also recorded in `modules/midi-harmony/README.md`,
`modules/midi-follow/README.md`, and the Loopback branch's module README.

## Verification status

Standalone Follow's `make check` passed all runnable gates; project-dependent
checks were explicitly skipped in that run. Loopback and Loopback+USB each
passed `make check-remix`, including their new saturation gates. Standalone
Harmony's existing linked gates, new stateful gate and full port suite passed.
The complete combined `make check REMIX=mattias-bus OT_PROJECT=.../MUTE-RIG`
passed: 13 image gates, zero failures and no skipped checks. This includes
Follow’s 28 mute regressions, 9,216 stock arp comparisons, all 345,600
Harmony playability transitions, and Chord Play recording, display and
storage checks. The full run restored the shipping build afterward.

`make reach BASE=upstream/main TESTS=1` regenerated the upstream reach plan
successfully; that is a plan, not a claim that every historical remix was
rerun. Validation in this pass covers the selections listed above. The
rebuilt combined port also passed all five stock-independent unit tests
(the same CTest selection used by `ci-emu`).

Local receipts and command logs live in each module worktree's ignored
`out/concert-*` paths. This remix keeps collected receipts in
`out/concert-evidence/` and the combined command log in `out/concert-check.log`.

## What these results do not establish

These are linked ColdFire and full-firmware port results. Live port events
enter the keyboard C ABI; sequence events run through native transport.
They do not establish external-input parser throughput under arbitrary DIN
or USB traffic, physical wire jitter, USB host behavior, hardware CPU/audio
headroom, or hours of continuous performance. Physical MIDI capture and a
long rehearsal on the actual performance project remain separate acceptance
steps. No firmware was flashed or transferred to a card in this pass.
