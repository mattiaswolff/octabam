# MIDI Harmony

On a MIDI track, open **NOTE SETUP** (FUNC + SRC). Knob **F: HARM** selects:

| HARM | Output |
| --- | --- |
| OFF | Stock notes and stored NOT2–4 |
| NOTE | One note snapped to the selected scale |
| TRI | A diatonic triad on the selected note: scale degrees 1, 3, 5 |
| 7TH | A diatonic seventh chord: scale degrees 1, 3, 5, 7 |

**Press knob F on NOTE SETUP** to open the dedicated **HARMONY** window.
Knob **A: HARM** edits the same setting; knob **B: VOIC** selects **ROOT**
(default, root-position chords) or **AUTO** (automatic voice leading).
Knob **C: SPRD** selects **CLOSE** (default), **OPEN** or **WIDE**.
The controls use the stock PLAYBACK selector graphics: four positions for
HARM, two for VOIC and three for SPRD, with the value printed underneath.
NO, YES or another F press closes it. Track/page buttons
also close it; press again to select another track/page. The title identifies
the track being edited. Transport and chromatic trig keys remain usable.
The other encoders are inactive, leaving room for future controls. Turning F on NOTE SETUP still edits HARM directly.

Choose KEY in its original position, **ARP SETUP F** (FUNC + AMP).
Without MIDI Scales, Harmony uses stock Major/Minor. Installing MIDI Scales
adds five modes in every key. **KEY OFF bypasses Harmony**, including chord
generation. HARM defaults OFF.

For example, C Major with HARM TRI turns C, D and F into C major, D minor
and F major. C Dorian gives C minor, D minor and F major. Chromatic trig keys
snap to nearest valid notes (ties downward), so adjacent keys can coincide.
This first version does not replace a running pattern's chord from the live
keyboard: live performance transposition remains a separate future feature.

Shared scale logic serves live MIDI keys and sequenced NOTE/P-locks.
Generated chords enter the **stock arp before its note selection**. ARP MODE,
SPD, RNGE, NLEN, LEG and step offsets retain their stock controls. Original
NOT2–4 values are never overwritten. Turning HARM OFF restores their use.
High chord voices beyond MIDI 127 are omitted; pitches do not wrap.

With MIDI Follow, RFOL stays on NOTE SETUP D. The follower retains its own
HARM, rhythm and TRAN/P-locks, while its chord root and KEY come from the
ultimate source track. KEY is displayed from that source and is read-only
on the follower. Disable RFOL to restore the follower's own Part KEY.
For **NOTE, TRI and 7TH**, the root passes through TRAN/P-locks and then
snaps to the effective KEY/scale. TRI and 7TH build their additional notes
from that snapped scale degree. In C Major, C +2 gives D–F–A (or D–F–A–C),
not a chromatically shifted C-major chord. B +7 snaps F♯ down to F, then
builds F–A–C (or F–A–C–E). Followers use their source's scale throughout.

A chromatic keyboard press chooses the pitch directly, without adding track
TRAN or replacing it with a followed root. Pressing D plays D, D minor or
D minor 7 according to HARM, even with followed root F and TRAN +7. This
also applies to live arp. The source supplies the keyboard's scale.

Generated notes enter the stock arp with TRAN already applied once. Its
pitch offsets receive a final scale correction before MIDI transmission.
A sequenced chord is rebuilt on its next note trig, using that trig's current
TRAN/P-lock; changing TRAN between trigs does not rebuild an existing arp
pool. Invalid transposed roots are silent until a valid trig; high chord
voices are omitted. Live keyboard pools remain playable independently.

Live recording stores the **physical key played** in NOTE once, even in
TRI/7TH mode. Extra generated voices only sound; they do not enter the
recorder or become NOT2–4 locks. An out-of-scale key remains that key in
NOTE and snaps when Harmony plays it. Shared chord tones do not suppress
a new key's recording. Playback regenerates the chord from NOTE, including
when NOT2–4 contain explicit disabled locks. HARM and KEY must remain active.

HARM, VOIC and SPRD are stored per MIDI track per **project**, not per Part/pattern. They are
saved in backward-compatible project comment lines and survive battery-RAM
resume. KEY remains a native Part setting. MIDI Follow's RFOL selection is
still its existing volatile setting; select it again after power-up.

## Automatic voice leading

With HARM TRI/7TH and VOIC AUTO, each track remembers its previous generated
chord and chooses a nearby inversion for the next one. With CLOSE spacing,
C3–E3–G3 followed by F produces C3–F3–A3. The harmonic root is still **F**:
Follow gets F, and recording the physical F key stores F in NOTE. Neither
the lowest voiced note nor the last generated chord tone replaces the root.
Voicing is applied before the stock arp, which therefore plays the chosen
inversion too. A follower with its own HARM TRI/7TH and VOIC AUTO chooses its
own inversions, using the inherited root and scale.

The bounded search considers each inversion at octave offsets 0, -12 and
+12. Each starts as a compact inversion within one octave, then applies the
selected spread. Every sounded candidate must remain inside MIDI 0–127 and
have its lowest note within one octave of the requested root. It first
minimizes total semitone travel between corresponding sorted **sounded** voices, then
prefers more unchanged voices. Exact ties prefer root position, then earlier
inversions and offsets in the listed order. This is our algorithm, not a
claim to reproduce OXI's unpublished implementation. At most twelve candidates
of four voices are considered per chord; there is no unbounded search.

The first chord uses root position with the selected spread. History is per track and shared between
that track's keyboard and sequence. HARM/VOIC/SPRD edits, project load,
and boot reset it; a changed effective scale/source or triad/seventh count
reseeds it on the next chord. A truncated high-MIDI chord keeps the existing
voice-omission behavior and resets history. Silence/STOP alone does not reset
history; set VOIC ROOT then AUTO to deliberately reseed it. AUTO is dynamic:
the same stored root can receive a different inversion after a different
preceding chord. Held keys retain their original note-offs when settings change.
VOIC and SPRD have no effect in HARM OFF/NOTE or with KEY OFF.

## Chord spacing

SPRD sets the spacing of the chosen inversion, independently of ROOT/AUTO:

| SPRD | Rule | C triad, VOIC ROOT | C seventh, VOIC ROOT |
| --- | --- | --- | --- |
| CLOSE | Keep the compact chord | C3–E3–G3 | C3–E3–G3–B3 |
| OPEN | Raise the second-lowest voice one octave | C3–G3–E4 | C3–G3–B3–E4 |
| WIDE | Raise every voice above the bass one octave | C3–E4–G4 | C3–E4–G4–B4 |

AUTO evaluates movement **after** applying this spacing. OPEN and WIDE may
therefore choose a different inversion from CLOSE. The bass stays near the
requested root while the upper voices can extend into the next octave.
Octave moves preserve the scale and chord identity; Follow still gets the
harmonic root and recording still stores the physical key once.

If a complete chord's root-position spread exceeds MIDI 127, its initial
chord falls back to CLOSE. Subsequent AUTO chords may find another valid
spread inversion; if none fits, they also fall back to CLOSE. An already
truncated chord keeps the generator's existing omitted voices. No notes
wrap or clip to a different pitch class. Changing SPRD affects the next
chord trigger; held notes retain their original release pitches. It resets
that track's AUTO history, so the next chord starts in root position.

## Implementation boundaries

The sequence hook changes the four-note scratch buffer before the stock arp
initializer. Unused voices duplicate the root (lowest voice after AUTO) for its valid-pitch bitmap;
stock deduplicates them. Invalid roots use safe zero-pitch padding and a
per-track volatile mute flag, so invalid bytes never index the arp bitmap.
The recorder uses the native handoff at `0x4009eb7a` once per physical key
press/release; generated voices call the stock sender with recording disabled.
Live keys keep the generated pitches until release, with reference counts
for shared chord tones. A bypassed press also retains
its stock release path if HARM or KEY is enabled while held. Stock owns MIDI
transmission, arp insertion/removal and sequenced note-off records.

Harmony skips stock scale correction for generated notes, then applies its
own final correction for every active HARM mode before note ownership is
recorded. Follow captures Harmony's selected root before the arp and bypasses
its old final bass-only
replacement when Harmony is active. Each module also builds independently.

Battery RAM 0x100b14e2..e9 stores one byte per track: TYPE in bits 0–1,
SPRD in bits 2–3 (0 CLOSE, 1 OPEN, 2 WIDE). ea is the VOIC bitmask
(one AUTO bit per track); eb is version 0x4b. Boot migrates the previous
0x4a layout, preserving TYPE/VOIC and defaulting SPRD to CLOSE.
This is the stock linker padding before the record at 0x100b14f0; Quantizer's
ec..ee bytes are separate. Defaults and boot sanitize it. Project comments
are `#MIDI_HARMONY_TYPE_V1_T1=0` through T8, each 0..3, and
`#MIDI_HARMONY_VOIC_V1_T1=0` through T8, each 0..1, plus
`#MIDI_HARMONY_SPRD_V1_T1=0` through T8, each 0..2. Parse-only loads do
not write settings. A project without these lines starts with HARM OFF and
VOIC ROOT and SPRD CLOSE. Existing TYPE comment values and native
Part/pattern formats are unchanged. Older Harmony builds ignore unknown
comments; their battery-version check resets Harmony settings on firmware
rollback, so reload the saved project to restore the settings they support. The 64-byte voice-leading history
and window state are volatile module DRAM; neither is saved to a project.

## Reusable verification

```
make check REMIX=midi-harmony
make check REMIX=midi-scales
make check REMIX=midi-follow
make check REMIX=midi-harmony-follow
.venv/bin/python3 tools/verify/verify_midi_harmony_port.py --project /path/to/local/template
```

The template is read only; generated projects, virtual CF cards, UART MIDI,
LCD captures and receipts go under `out/harmony-port-suite/`. The machine
checks execute linked ColdFire bytes, including all keys/scales/pitches,
register/memory boundaries, OFF behaviour, overlapping live-key releases,
HARM/KEY edits while held, native control passthrough and malformed comments.
The full-port checks exercise actual firmware MIDI, encoder controls and
project persistence, plus added-scale output with Harmony OFF. NOTE/TRI/7TH
regressions cover TRAN/P-locks before root snapping and chord generation,
matching source-root capture, and absolute keyboard pitches on followers
with direct output and live arp. Machine checks also cover invalid-root
muting/recovery and final arp scale correction. Live-recording cases use
REC+PLAY, play C♯/D/F, exit REC and compare the next loop with live output;
they inspect recorded NOTE bytes and explicitly disabled NOT2–4 locks.
Use `--recording-only` with the port script for these focused cases.
Use `--voicing-only` for AUTO sequence/keyboard/arp, recorded physical roots,
SPRD variants, Harmony-page controls, and actual save/reload/warm-resume checks. These also
produce the Harmony window screenshot at `out/harmony-port-suite/harmony-page/page.png`.
Use `--spread-only` for the ten spaced sequence/arp and follower-root cases.
The default full suite includes all groups. The machine gate compares AUTO's
movement cost against all valid compact and spaced voicings across keys/scales/MIDI range,
checks per-track history and context resets, and polices writes and registers.
They do not verify electrical MIDI timing, battery
retention, musical feel or a physical flash. No device transfer is performed.

### Hardware acceptance for AUTO and physical-key recording

Use a disposable pattern, with T1 KEY C Major and TRAN 0. Set HARM TRI,
press F on NOTE SETUP, set B VOIC AUTO and C SPRD CLOSE. Play C then F: expect C–E–G
then C–F–A. Hold both keys and release them in either order: shared C must
continue until its final owner releases, with no stuck notes. Repeat with
the stock arp active, and with HARM 7TH. Set VOIC ROOT and check each
SPRD against the table above; repeat with AUTO and change SPRD while
a key is held to check that its release leaves no stuck notes.

Set T2 RFOL T1, HARM NOTE, TRAN 0 and program its rhythm. While performing
on T1, F must make T2's next trig play F, even though T1's lowest voice is C.
Repeat with T2 HARM TRI and its own AUTO: it must retain its own rhythm and
voicing history while using T1's root/scale.

Live-record C, D and F on T1. Inspect NOTE on those trigs: it must show
the physical keys C, D, F; Harmony must not add NOT2–4 locks. Replay with
HARM/KEY still enabled and expect chords. A physical C-sharp key must remain
C-sharp in NOTE while the heard root snaps to C in C Major. Previously
misrecorded takes are not repaired. Finally save/reload the test project:
HARM/VOIC/SPRD should return, while the first AUTO chord starts in root
position with the saved spread.

### Live-recording regression found on OCTABAM4

Device feedback identified unexpected NOTE values and explicit empty NOT2–4
locks after chromatic live recording. The released image reproduced both
in the port: playing C/D/F triads stored G/A/C as NOTE and raw 64 (zero
offset) in each extra-note lane. Each generated voice had been sent through
the native recorder path, so later voices replaced the root.

The correction records the physical key once and keeps generated voices out
of that path. It does not repair notes already recorded by OCTABAM4. The
reported single-note playback has not been reproduced in the port: even
explicit empty extra-note locks still generated chords with HARM and KEY
active. That hardware symptom remains to be checked with the corrected image.
