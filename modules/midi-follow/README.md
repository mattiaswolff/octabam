# MIDI Follow (experimental)

Each MIDI track can follow another MIDI track's chord root while keeping its
own rhythm, velocity and note length. By default, FIXED octave 3 with TRAN=0 uses MIDI notes 36–47:
C → F → G gives 36 → 41 → 43. The follower's TRAN adds a signed semitone
offset after its register choice. Scale Quantizer is not required.

## Register choice

On the receiving track, press **knob D (RFOL) on NOTE SETUP** to open FOLLOW.
Knob **B: MODE** selects FIXED or SOURCE. Knob **C: OCT** sets the register:

| MODE | OCT | Effect |
| --- | --- | --- |
| FIXED (default) | 0–10; default 3 | Keep the source pitch class in this octave, regardless of its original octave |
| SOURCE | -2, -1, 0, +1, +2; default 0 | Follow the source's complete root pitch, shifted by this many octaves |

For source notes C3 then C5 (MIDI 36 then 60): FIXED 3 produces C3 then C3;
SOURCE 0 produces C3 then C5; SOURCE -1 produces C2 then C4.
Octave names here use C0 = MIDI 0. Octave 10 is partial: only C–G fit MIDI.
Each mode remembers its own OCT value when switching modes.

The receiver applies register choice first, then its native TRAN/P-lock offset.
With Harmony active, root snapping and chord generation follow those steps.
Out-of-range final roots are silent, never wrapped or clamped. Settings affect
the next receiver note trig; already-held notes keep their original releases.
A chain uses the ultimate source's root and the final receiver's register and
TRAN; intermediate receiver offsets do not accumulate.

Source register refers to the harmonic root before inversion, spread and root
omission/placement, not whichever generated or arpeggiated note is lowest.
Source sequence TRAN/scale and live key root selection still happen before capture.

The new settings share RFOL's existing lifetime: per-track module RAM, reset on
reboot; not saved in Parts/projects or parameter locked. Existing stock controls
and the source selector remain in place. NO/YES/D or a track/page key closes the
window; transport and chromatic playing continue through it.

## On the Octatrack

1. Select the follower, for example **MIDI T2**.
2. Open **NOTE SETUP** with **FUNC + SRC** (or double-tap SRC).
3. Turn **knob D, RFOL**, from **OFF** to **T1**.
4. Program T1's C/F/G NOTE locks and optional NOTE2–4 chord tones. Its arp can
   play those chords. Program T2's rhythm; leave the follower's arp OFF.
5. Give the two tracks different output MIDI channels, then play.
6. On the follower's **ARP MAIN** page, use **TRAN** for relative pitch:
   **0** = root, **+7** = perfect fifth, **+12** = octave above, **-12** = octave
   below. Set it for the whole track, or hold a step and parameter-lock TRAN.
   A locked value replaces the track's base TRAN for that step; it is not added
   to the base. The follower's arp remains OFF.

RFOL appears on all eight MIDI tracks. It selects a **track**, independently of
its output CHAN. Several followers can select the same source. The selector
skips the track itself and choices that would create a circular dependency.
Chains resolve to their final source: T3 → T2 → T1 follows T1's root.

- **OFF** plays the track's original notes. Every track starts OFF at boot.
- Root means the source's first NOTE, with its stock transpose/scale processing;
  it does not infer the root from a chord inversion. C–E–G arp notes leave the
  bass on C. A new F–A–C chord moves it to F.
- A configured follower is monophonic once its source has a known root:
  NOTE2–4 are suppressed. Before the first eligible source trigger it passes
  through unchanged.
- The next follower trig uses the selected source's latest root and the receiver's register choice. A held bass
  keeps its original note-off, including when RFOL changes or switches OFF.
- The follower's NOTE does not set an interval: use TRAN. Its live value,
  including parameter locks, is added after root selection without an additional
  scale correction. These are chromatic semitones, not scale degrees; +7 is
  always a perfect fifth, even when that pitch falls outside the source scale.
  Pitches outside MIDI 0–127 are suppressed instead of wrapped. Existing stock
  absent/invalid-note gates still apply before the follower replacement.
- A dependency chain uses the ultimate source root plus the final follower's
  own register choice and TRAN; intermediate followers' offsets do not accumulate.
- Ordinary same-tick source trigs are captured before any track emits, so
  **T2 following T8** sees the new root on that tick. Earlier microtimed bass
  trigs still use the previous root.
- Roots latch through rests and transport stops. Configuration and roots are
  **RAM-only**: they survive pattern/Part/project changes in the running session
  and reset on reboot. They are not saved or copied with a Part/project.
- **Muting a source silences its sequenced MIDI output but keeps its root
  progression available to followers**, including when playback starts muted.
  Muting a follower independently silences that follower. Mute/unmute does not
  reset the remembered root or change the ownership of already sounding notes.
- Disabled tracks, CHAN OFF, zero velocity, invalid notes and rests still leave
  the previous root in place. Ordinary track mute is covered in linked and
  full-firmware emulator tests; unusual mute/plays-free modes remain untested
  on hardware.

On its own, MIDI Follow supplies bass-root following. MIDI Harmony optionally
adds live keyboard chords and follower chords/arp, as described below. Audio
following, live performance transposition of a running pattern and shared output
MIDI channels remain outside the tested use. This image has **not been flashed**.

## Implementation

The module uses the linked ColdFire pattern from `modules/repitch` and the
stock NOTE descriptor, drawer and encoder dispatch. No DSP code is added.

- `0x4009f986`: before the output loop, capture eligible ordinary chord roots
  for all tracks. Uses the stock trigger mask, enabled-track checks,
  output channel and velocity. The mute mask is intentionally left to stock
  output handling. Original NOTE lanes already contain the locks.
- `0x4009fb00`: capture each eligible source event, including arp ticks, from
  the original NOTE lane, not the arp's scratch output. Apply the stock
  transpose and scale correction.
- `0x4009fb80`: resolve a follower's source, add its live TRAN (`a5+0x22c`,
  biased by 64), and replace its scratch pitch before
  stock note ownership and release bookkeeping (`0x4009fbbc` / `0x4009fd04`).
  Chained resolution has a defensive eight-hop bound.
- NOTE SETUP's unused D slot is labelled RFOL and enabled. Its encoder callback
  at `0x400bc64e` points to the module; its formatter prints OFF/T1–T8.
  The drawer detour at `0x40036674` reads module RAM for that slot. The original
  staged Part value is never replaced or sent through the stock setter.

`bf_sources[8]` holds OFF=0 or source=1…8. `bf_roots[8]` holds the source's bass
pitch or 0xff (unknown). `bf_pitches[8]` retains full MIDI root pitches.
`bf_reg_modes`, `bf_reg_fixed` and `bf_reg_offsets` hold the receiver's register
choices. Harmony calls `bf_register` before applying the receiver's TRAN; its
matching adapter also publishes live keyboard root octaves into `bf_pitches`.
These initialized bytes belong to the linked runtime;
there is no persistence format or save/load hook. The generic MIDI sender is
not hooked. The existing DRAM platform reserves about 10 MB of sample RAM;
this small module shares that reserve when composed with other DRAM modules.

## Reproduce

With your own unpacked stock 1.40C image and prepared toolchain:

```sh
make emu-cf
make check REMIX=midi-follow
.venv/bin/python3 tools/verify/verify_midi_follow.py midi-follow --project /path/to/local/project
```

The last command reads the project as a template and creates disposable virtual
cards under `out/midi-follow/`. It does not edit the template or a device card.
The module gate also accepts `OT_PROJECT`; without one, the full-port checks
explicitly skip and the controlled machine-code gate still runs.

The register gate executes 12,288 combinations of source pitch, FIXED/SOURCE
register, receiver TRAN and direct/chained routing. When Harmony is linked it
also checks register selection before scale snapping, live root capture and
out-of-range suppression. The panel/MIDI register runner is:

```sh
.venv/bin/python3 tools/verify/verify_midi_follow_register_port.py --project /path/to/local/project
# Optional: combined image/symbols, using this checkout's emulator:
.venv/bin/python3 tools/verify/verify_midi_follow_register_port.py --project /path/to/local/project --harmony --build-root /path/to/combined/worktree
```

It captures FIXED 3/4 and SOURCE 0/-2/+2, checks MIDI releases and unchanged
Part data, and saves LCD images with an image-hash receipt. The Harmony fixture
uses source CHORD/ROOT -2 OCT and receiver NOTE to check that root placement
does not alter the captured source register.

The controlled gate executes the actual linked bytes: all 56 source/follower
pairs, OFF, chains/cycles, 128 root notes, all 128 follower TRAN values for
each of 12 roots, out-of-range suppression, arp isolation, source transposition/scales,
same-tick T8 capture, mute/channel/velocity gates, invalid notes, formatters and
register preservation. A write hook rejects writes outside the declared module
state, scratch result, displaced stock write and bounded call stack in these tests.
Full-port stock/patched UART captures cover chords,
source arpeggiation, T8 → T2, fallback, held-note release, unchanged other tracks
and stored banks. An all-OFF run must match stock MIDI events exactly.
Additional stock/patched captures set follower TRAN to +7 and lock individual
steps to 0, +12 and -12. They check return to the base +7 on an unlocked step,
a held transposed note's release across a source-root change, reverse source
order, and exact stock behavior with RFOL OFF. Fixture timing is explicitly
set so the input project's scale mode cannot change the capture window.

Two live-change cases switch RFOL OFF and from T1 to T3 while playing. A separate
truncated capture first proves that the bass C is still held at the change
instant. The complete runs require that C's original note-off, the expected
new notes, and no hanging notes. The callbacks are invoked by the port's script;
the separate panel test below checks the actual UART encoder path.

The panel test sends actual UART1 key/encoder reports: enter MIDI NOTE SETUP,
select RFOL, share the source across tracks, leave/reopen the page, switch OFF,
and boot with defaults. It checks module settings and verifies that the working
Part mirror is unchanged. LCD screenshots are under `out/midi-follow/ui/`.
`out/midi-follow/result.json` is written only after all cases pass and records
the tested image hashes; artifacts are local and uncommitted.

For the personal composed remix, the additional safety runner creates disposable
MIDI and audio fixtures from the same local project template:

```sh
make check REMIX=mattias-midi-follow BUILD=2
.venv/bin/python3 tools/verify/verify_midi_follow_safety.py --project /path/to/local/project
.venv/bin/python3 tools/verify/verify_midi_follow_safety.py --project /path/to/local/project --mode soak --seconds 120
.venv/bin/python3 tools/verify/verify_midi_follow_safety.py --project /path/to/local/project --mode soak --seconds 120 --off
```

Keep that build and its runtime symbols in place until the commands finish.
The transition suite compares stock and patched UART captures for stop/restart,
pattern, Part and project changes. Truncated captures prove that notes really
are held at the tested change boundaries. Part/project cases change the output
channel too, exercising release ownership. The soak runs eight dense MIDI tracks
beside eight FLEX tracks and the remix's audio effects, then switches through
A01–A04 and Parts 1–4 using panel input. It checks balanced MIDI releases, audio
activity on every track, RFOL state, module instructions, DSP status and unchanged
stored banks. Each soak uses its own generated project and virtual card.
Receipts, captured MIDI, audio and command logs are in `out/midi-follow-safety/`.
Neither suite measures worst-case physical CPU timing. Follower arp and shared
output channels remain outside the supported test setup.

For a device trial, use a new build number and verify the final packaged image
against the tested MAIN_OS, with a backup and the known-good image available.
Start with RFOL OFF, then one source and one follower on different MIDI
channels. Check C/F/G, source arp, RFOL changes during long notes and STOP on
physical MIDI before extending the setup. These are pending hardware checks,
not evidence supplied by the emulator.

## What the emulator allows

The full port runs the patched CPU firmware, modeled timers and RTOS tasks,
virtual CF storage, panel input and MIDI UART. It can load projects, run the
sequencer, capture MIDI bytes, operate buttons/encoders and render the firmware's
LCD. `make panel REMIX=midi-follow OT_PROJECT=/path/to/project` opens an
interactive virtual panel. These tests do not require emulator audio output.

The extended soak also runs both DSP cores with `--dsp-rt` and captures audio;
its duration is emulated time, and it may take much longer on the host computer.

The relative-TRAN extension is newer than the packaged OCTABAM3 trial image.
It requires a new build; copying or testing OCTABAM3 does not test this extension.

The controlled Unicorn test proves behavior in selected states; the full port
checks the real UI/sequencer paths. Neither proves electrical DIN output,
hardware timing/jitter, external synth behavior, or safe flash/boot on a physical
Octatrack. Hardware testing remains pending.

## MIDI Harmony and MIDI Scales

The module is named **MIDI Follow** (formerly Bass Follow). RFOL is still
NOTE SETUP D and the standalone bass-root behaviour is unchanged. With
MIDI Harmony active, root selection happens before chord generation and
stock arp processing, so a follower can play NOTE, TRI or 7TH instead of
having its extra notes collapsed. The source's native KEY is inherited.
MIDI Scales extends that native KEY selector independently.

The NOTE SETUP callback forwards every non-D control to stock. Harmony can
own F without intercepting CHAN, BANK, PROG or SBNK. The two enable flags
are claimed as separate bytes so their manifests compose independently.

With HARM NOTE, TRI or 7TH enabled, the follower root is snapped into the
inherited scale after TRAN/P-locks, then any chord tones are built from that
scale degree. Arp output also receives a final scale correction. With HARM OFF, the standalone chromatic offset
behaviour described above is retained.


### Live source with Harmony bypassed

When MIDI Harmony is installed, chromatic key presses publish the source
root even with its HARM OFF or KEY OFF. A rhythmic follower can use RFOL
with its own HARM OFF, NOTE, TRI or 7TH. Bypassed source keys keep the stock
sound and recording path; the root is the physical key's pitch class.
Note-offs retain the last played root. Arp-only ticks from a live keyboard
pool must not replace it with the source's unrelated stored NOTE. Ordinary
source pattern trigs still publish their own root when they occur.

Run `verify_midi_harmony_port.py --bypass-follow-only --project /path/to/template`
for live-source/follower UART regressions with source arp on/off and KEY OFF.
The keyboard linked-code gate also checks bypass recording arguments, root
retention on release, and protection from stale stored NOTE during live arp.

### Muted-source regression

With a copied local project, `verify_midi_follow.py --project DIR` also tests
muted sources and followers, both track orders, source arp, and mute/unmute
while a bass note is held. When installed, Scales and Harmony receive the same
checks; Chord Play quality locks are exercised alongside source scale changes.
Use `--mute-only` to run this focused suite plus the linked machine-code gate.
Captures, frozen candidate bytes, logs and `result.json` stay under the remix's
`out/*midi-follow/mute/` directory. These are emulator checks, not hardware proof.

Register verification: `tools/verify/verify_midi_follow_register.py` covers full MIDI range, both register modes, every octave choice, TRAN, chains, invalid roots and bounded writes. `tools/verify/verify_midi_follow_register_port.py --project DIR` exercises physical RFOL/window encoders, source octave changes, MIDI release balance and unchanged native Part bytes on a disposable virtual card.

FOLLOW uses the same six-cell grid as Harmony: **A RFOL, B MODE, C OCT**.
RFOL and MODE use stock fields/selectors; OCT stays a numeric octave value.
Custom selectors accumulate four raw encoder counts per choice and cap each
report to one choice. Closing FOLLOW redraws RFOL on NOTE SETUP.

The detail page has A=RFOL, B=MODE, C=OCT. Only C edits octave values.
FIXED remembers an absolute octave; SOURCE remembers a relative octave offset.
Changing MODE recalls that mode's own OCT value without editing either value.
The OCT label/value are centered in cell C; the footer shows only NO:BACK.

## Temporary response audition: NEXT / CHANGE

Press D on MIDI NOTE SETUP to open RFOL, then turn D inside the window
(**RESP**, lower left). A/B/C remain RFOL, MODE and OCT.

- **NEXT** is the boot default and keeps the original behavior: the receiver
  uses the latest source root on its next scheduled note.
- **CHANGE** also moves an already-sounding sequenced bass when the ultimate
  source changes root. It sends note-off for the old pitch and note-on for
  the new one, restarting the synth envelope. Rests stay silent. The original
  release deadline and the next programmed trig stay in place.

The setting is per receiver, volatile, and takes effect from its next ordinary trig (not an arp-only tick).
Live source-key changes are handled on the next sequencer service pass, not
held until the next receiver trig. This is not a measured zero-latency claim.
A source change coinciding with a scheduled receiver event does not add an
extra retrigger. Muted/disabled receivers and CHAN OFF do not generate notes.
Only voices owned by that receiver may move; occupied channel/note pairs
are not stolen. Out-of-range voices are omitted rather than wrapped.

With Harmony chords, CHANGE shifts the currently sounding shape by the
logical-root interval; the next ordinary trig generates a fresh chord and
voicing. With an arp, its clock/order are retained and outgoing cached-pool
notes track the changed root. It does not trigger during an arp rest or
restart the arp. This control targets sequenced/arp receivers, including
those following a live Chord Play source; it does not retune manually held
receiver keyboard notes.

`tools/verify/verify_midi_follow_response.py` checks linked machine code,
release deadlines, silence gates and MIDI ownership. The companion
`tools/verify/verify_midi_follow_response_port.py --project /path/to/project`
operates physical encoder D and captures the full firmware's MIDI output.
These tests do not establish physical MIDI latency or external-synth timing.


## Eight-track routing stress

`tools/verify/verify_midi_follow_stress.py` is an image gate. It tests all
40,320 permutations of a full eight-track chain, 12,000 seeded live routing
edits, and 56,080 routed outputs with register/transpose extremes, unknown
roots, cycles and invalid links. The independent graph model checks that
editing one receiver cannot change another, no selectable route introduces
a cycle, and runtime fallback terminates without writing outside its scratch
and stack. Run it on both standalone Follow and the combined Harmony image.
This exercises linked ColdFire code, not physical outgoing-MIDI timing.
