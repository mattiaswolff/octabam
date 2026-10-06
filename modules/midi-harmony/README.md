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
(default), **1ST**, **2ND**, **3RD** or **AUTO** (automatic voice leading).
Knob **C: SPRD** selects **CLOSE** (default), **OPEN** or **WIDE**.
Knob **D: OMIT** selects **OFF** (default) or **ROOT**.
The controls use the stock PLAYBACK selector graphics: four positions for
HARM, five for VOIC and three for SPRD, with the value printed underneath.
They occupy the top row of a six-cell grid, matching the physical encoder
positions without letter prefixes. OMIT occupies the lower-left cell; the other two lower cells are inactive;
the footer identifies HARMONY and the MIDI track, beside NO:BACK.
NO, YES or another F press closes it. Track/page buttons
also close it; press again to select another track/page. The footer identifies
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

HARM, VOIC, SPRD and OMIT are stored per MIDI track per **project**, not per Part/pattern. They are
saved in backward-compatible project comment lines and survive battery-RAM
resume. KEY remains a native Part setting. MIDI Follow's RFOL selection is
still its existing volatile setting; select it again after power-up.

## Manual inversions

VOIC ROOT keeps the generated root-position chord. 1ST, 2ND and 3RD rotate
one, two or three lower chord tones upward by an octave. With CLOSE spacing,
C3–E3–G3 becomes E3–G3–C4 (1ST) or G3–C4–E4 (2ND). For C3–E3–G3–B3,
3RD gives B3–C4–E4–G4. On a triad, 3RD uses 2ND; changing back to 7TH
restores the selected 3RD inversion. SPRD applies after inversion.

Manual inversions affect the next triggered chord, including the stock arp,
and do not use previous-chord history. The logical root and the recorded
physical key are unchanged. If an inversion exceeds MIDI 127, keep root
position and apply SPRD if it fits; an already incomplete chord keeps the
generator's omission behavior. Existing ROOT/AUTO projects keep their choices.
HARM, VOIC, SPRD and OMIT are track defaults, not parameter-lock destinations.

## Automatic voice leading

With HARM TRI/7TH and VOIC AUTO, each track remembers its previous generated
chord and chooses a nearby inversion for the next one. With CLOSE spacing,
C3–E3–G3 followed by F produces C3–F3–A3. The harmonic root is still **F**:
Follow gets F, and recording the physical F key stores F in NOTE. Neither
the lowest voiced note nor the last generated chord tone replaces the root.
Voicing is applied before the stock arp, which therefore plays the chosen
inversion too. A follower with its own HARM TRI/7TH and VOIC AUTO chooses its
own inversions, using the inherited root and scale.

Deliberate octave jumps move the voicing too: C3 → C4 raises every voice
one octave, including an already inverted or OPEN/WIDE chord. Before scoring,
AUTO shifts its previous chord by the whole-octave portion of the logical
root's change (toward zero: +12…+23 means +12; −12…−23 means −12).
Smaller root changes keep ordinary voice leading; crossing B3 → C4 does not
force an octave jump. MIDI limits still apply. This uses transient history
only; project settings and recorded notes are unchanged.

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
that track's keyboard and sequence. HARM/VOIC/SPRD/OMIT edits, project load,
and boot reset it; a changed effective scale/source or triad/seventh count
reseeds it on the next chord. A truncated high-MIDI chord keeps the existing
voice-omission behavior and resets history. Silence/STOP alone does not reset
history; set VOIC ROOT then AUTO to deliberately reseed it. AUTO is dynamic:
the same stored root can receive a different inversion after a different
preceding chord. Held keys retain their original note-offs when settings change.
VOIC and SPRD have no effect in HARM OFF/NOTE or with KEY OFF.

## Chord spacing

SPRD sets the spacing of the chosen inversion, independently of manual/AUTO voicing:

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

## Omit the root

OMIT ROOT removes the **harmonic root pitch class** after voicing and spread.
For C major, ROOT gives E–G; 1ST also gives E–G (removing the upper C),
and 2ND gives G–E (removing C between them). For C major seventh, 3RD
becomes B–E–G. OFF restores the complete chord on the next trigger.
A bass follower still follows C, and recording still stores the physical C
key. This can leave the root to a separate bass track without changing harmony.

Only HARM TRI/7TH with an active KEY use OMIT. NOTE and OFF stay unchanged.
AUTO still optimizes the complete underlying chord before removing its root;
this preserves its existing voice-leading decisions. Held keys retain their
original releases if OMIT changes. Stock arp receives the remaining notes.
At the upper MIDI limit, any available non-root tones still play. If none
remain, the chord is silent, with safe empty-pool handling and balanced
physical-key recorder ownership. No fake note zero or wrapped pitch is sent.

## Implementation boundaries

The sequence hook changes the four-note scratch buffer before the stock arp
initializer. Unused voices duplicate the root (lowest voice after voicing) for its valid-pitch bitmap;
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
SPRD in bits 2–3 (0 CLOSE, 1 OPEN, 2 WIDE), manual inversion in bits 4–5
(0 root, 1 first, 2 second, 3 third), with OMIT ROOT in bit 6. ea retains one
AUTO bit per track; eb is version 0x4d. Boot migrates 0x4c preserving manual
inversions, 0x4b preserving TYPE/SPRD/AUTO, and 0x4a preserving TYPE/AUTO
with CLOSE spacing. Old versions start with OMIT OFF.
This is the stock linker padding before the record at 0x100b14f0; Quantizer's
ec..ee bytes are separate. Defaults and boot sanitize it. Project comments
are `#MIDI_HARMONY_TYPE_V1_T1=0` through T8, each 0..3, and
`#MIDI_HARMONY_VOIC_V1_T1=0` through T8, each 0..4 (0 ROOT, 1 AUTO,
2 1ST, 3 2ND, 4 3RD; the existing 0/1 meanings are unchanged), plus
`#MIDI_HARMONY_SPRD_V1_T1=0` through T8, each 0..2, and
`#MIDI_HARMONY_OMIT_V1_T1=0` through T8, each 0..1. Parse-only loads do
not write settings. A project without these lines starts with HARM OFF and
VOIC ROOT, SPRD CLOSE and OMIT OFF. Existing TYPE comment values and native
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
Use `--bypass-follow-only` for live HARM OFF / KEY OFF source roots driving rhythmic followers.
Use `--octave-only` for live C-minor octave jumps in TRI/7TH with every spacing.
Use `--spread-only` for the ten spaced sequence/arp and follower-root cases.
Use `--inversions-only` for manual inversions, stock arp, follower-root identity,
root omission, physical-key recording/replay and manual-VOIC/OMIT save/reload/warm resume.
The default full suite includes all groups. The machine gate compares AUTO's
movement cost against all valid compact and spaced voicings across keys/scales/MIDI range,
checks per-track history and context resets, and polices writes and registers.
They do not verify electrical MIDI timing, battery
retention, musical feel or a physical flash. No device transfer is performed.

### Hardware acceptance for inversions, AUTO and physical-key recording

With HARM TRI, VOIC 1ST/2ND, SPRD CLOSE and KEY C Major, check C gives
E–G–C / G–C–E. Select 3RD: a triad still uses 2ND; HARM 7TH gives
B–C–E–G. Repeat with OPEN/WIDE and the stock arp. A root-following bass
must still play C, then F when playing F. Record physical C/D/F keys and
confirm NOTE stores those keys and replay regenerates the selected inversion.
Enable OMIT ROOT and confirm only C disappears from each C chord, regardless
of inversion, while the bass still plays C. Save/reload the project and check
the manual VOIC and OMIT choices survive.


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

### AUTO octave regression (OCTABAM5 hardware report)

With C minor, HARM TRI, VOIC AUTO, SPRD OPEN, OMIT OFF, play C3 → C4 → C3.
Expect C3–G3–E♭4 → C4–G4–E♭5 → C3–G3–E♭4, with no stuck notes.
OCTABAM5 incorrectly reused the first chord for both roots; the emulator
reproduced that failure through actual chromatic-key events. Repeat with
7TH and other spacing choices, then C → F to retain smooth voice leading.
The automated regressions live in the linked gate and full-firmware suite;
a passing emulator run is not hardware acceptance of the corrected build.
