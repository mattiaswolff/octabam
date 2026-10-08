# MIDI Harmony

On a MIDI track, open **NOTE SETUP** (FUNC + SRC). Knob **F: HARM** selects:

| HARM | Output |
| --- | --- |
| OFF | Stock notes and stored NOT2–4 |
| NOTE | One note snapped to the selected scale |
| CHORD | Generate from native NOTE plus the dedicated CHRD choice |

**Press knob F on NOTE SETUP** to open the dedicated **HARMONY** window.
Knob **A: HARM** edits the same setting; knob **B: VOIC** selects **ROOT**
(default), **1ST**, **2ND**, **3RD** or **AUTO** (automatic voice leading).
Knob **C: SPRD** selects **CLOSE** (default), **OPEN** or **WIDE**.
Knob **D: ROOT** selects **KEEP** (default), **OMIT**, **-1 OCT** or **-2 OCT**.
The controls use the stock PLAYBACK selector graphics: three positions for
HARM, five for VOIC, three for SPRD and four for ROOT, with the value printed underneath.
HARM, VOIC and SPRD occupy the top row of a six-cell grid, matching the
physical encoder positions without letter prefixes. ROOT occupies the lower-left cell; F selects the temporary WIDTH comparison; E is inactive;
the footer identifies HARMONY and the MIDI track, beside NO:BACK.
NO, YES or another F press closes it. Track/page buttons
also close it; press again to select another track/page. The footer identifies
the track being edited. Transport and chromatic trig keys remain usable.
Encoder E remains inactive. Turning F on NOTE SETUP still edits HARM directly.

Choose KEY in its original position, **ARP SETUP F** (FUNC + AMP).
Without MIDI Scales, Harmony uses stock Major/Minor. Installing MIDI Scales
adds five modes in every key. **KEY OFF leaves roots unsnapped**: NOTE passes
the pitch through; CHORD uses major intervals from each played root. TRI
gives C–E–G or D–F♯–A, and 7TH adds the major seventh. Other CHRD choices
retain their intervals, including explicit MIN and DOM7. HARM OFF restores stock behavior.
Voicing, spread and ROOT still apply without a scale. HARM defaults OFF.

For example, C Major with HARM CHORD and CHRD TRI turns C, D and F into C major, D minor
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
ultimate source track. The receiver's MIDI Follow MODE/OCT setting chooses a
fixed register or the source root's octave (with -2..+2 octave offset) before
TRAN and root snapping. Source capture retains the harmonic root before VOIC,
SPRD and ROOT placement. This requires the matching MIDI Follow register update.
KEY is displayed from that source and is read-only
on the follower. Disable RFOL to restore the follower's own Part KEY.
For **NOTE and CHORD**, the root passes through TRAN/P-locks and then
snaps to the effective KEY/scale. TRI and 7TH build their additional notes
from that snapped scale degree. In C Major, C +2 gives D–F–A (or D–F–A–C),
not a chromatically shifted C-major chord. B +7 snaps F♯ down to F, then
builds F–A–C (or F–A–C–E). Followers use their source's scale throughout.

A chromatic keyboard press chooses the pitch directly, without replacing it
with a followed root. With the arp OFF, TRAN does not affect these live notes,
matching stock. With the arp ON, its outgoing notes use the current stock
TRAN and arranger offset on every tick. Turning TRAN changes subsequent arp
notes without another key press. This applies to chromatic keys and CHORD PLAY.
The source supplies the keyboard's scale. Scale-derived qualities receive
final scale correction after transposition; explicit MAJ/MIN/DOM7 do not.

Sequenced generated notes enter the stock arp with TRAN already applied once. Its
pitch offsets receive a final scale correction before MIDI transmission for
scale-derived choices. Explicit MAJ, MIN and DOM7 preserve their chromatic
chord tones through the arp.
A sequenced chord is rebuilt on its next note trig, using that trig's current
TRAN/P-lock; changing TRAN between trigs does not rebuild an existing arp
pool. Invalid transposed roots are silent until a valid trig; high chord
voices are omitted. Live keyboard pools remain playable independently.

Live recording stores the **physical key played** in NOTE once, even in
CHORD mode. Extra generated voices only sound; they do not enter the
recorder or become NOT2–4 locks. An out-of-scale key remains that key in
NOTE and snaps when Harmony plays it. Shared chord tones do not suppress
a new key's recording. Playback regenerates the chord from NOTE, including
when NOT2–4 contain explicit disabled locks. HARM and KEY must remain active.

HARM, VOIC, SPRD and ROOT are stored per MIDI track per **project**, not per Part/pattern. They are
saved in backward-compatible project comment lines and survive battery-RAM
resume. KEY remains a native Part setting. MIDI Follow's RFOL selection is
still its existing volatile setting; select it again after power-up.

## CHORD PLAY and CHRD

This is a development candidate. Source and emulator checks do not establish
hardware timing, MIDI electrical behavior or physical battery retention.

Set HARM to CHORD, then return to the main MIDI NOTE page. D displays CHRD
in the old NOT2 position; E/F are inactive. Native NOT2–4 values remain stored
and become available again with HARM OFF. Turning D alone selects the live
chord. The CHRD knob displays this base value during performance; temporary
extensions appear in the sounding-chord guide. Hold one or more sequencer steps and turn D to edit their CHRD locks;
press D while holding steps to toggle their locks. Unlocked steps display
and play TRI, independently of the live selection or the previous step.

Choose CHORD PLAY with the normal FUNC + UP/DOWN mode selector. Outside grid
recording, trigs 1–8 play the selected scale from tonic through the next octave.
With KEY OFF they use C–D–E–F–G–A–B–C as roots; each TRI is major.
The stock-style inverted title bar reads CHORD PLAY when idle and shows the
actual MIDI notes while sounding. Chord names and note names both use sharps.
A compact line below the chord name always shows VOIC, SPRD and ROOT:
`V:1 S:O R:-1` means first inversion, OPEN spread, root down one octave.
VOIC uses R/A/1/2/3 (ROOT/AUTO/inversions), SPRD C/O/W, and ROOT
K/O/-1/-2 (KEEP/OMIT/octave drops). Long add9 names omit parentheses here
to leave this settings line visible.
FUNC + LEFT/RIGHT uses the chromatic octave controls. Trigs 9–16 temporarily
select these choices, in fixed positions:

| Key | CHRD | Notes, before global voicing |
| --- | --- | --- |
| 9 | TRI | Scale degrees 1, 3, 5 |
| 10 | 7TH | Scale degrees 1, 3, 5, 7 |
| 11 | ADD9 | Scale degrees 1, 3, 5, 9; four voices |
| 12 | SUS2 | Scale degrees 1, 2, 5 |
| 13 | SUS4 | Scale degrees 1, 4, 5 |
| 14 | MAJ | Root + 0, 4, 7 semitones |
| 15 | MIN | Root + 0, 3, 7 semitones |
| 16 | DOM7 | Root + 0, 4, 7, 10 semitones |

The last pressed variation takes effect immediately and retriggers held roots.
Releasing a variation is silent: the sounding quality stays latched until a
new root is pressed. That new root uses the newest still-held variation, or
D's base CHRD when no variation remains held. There is no carry-over latch
across root presses. In C minor: hold G for Gm, press MAJ for G major, release
MAJ (no new notes), then press DOM7 for G7. Releasing DOM7 then G sends no new
note-ons; the next G starts as Gm. With live recording active, only presses
that sound a chord create root-plus-CHRD trigs; releases do not record an
intermediate return to the base. Same-step changes leave the final choice.
Generated chord tones are never recorded into NOT2–4.

The LCD shows the resulting chord name below CHORD PLAY, leaving the native
footer intact. Root and variation groups use opposite trig LED channels; a held
key uses both. Physical colors and brightness require hardware acceptance.
Names use flat enharmonic pitch spellings. Scale alterations are retained:
in C minor, D ADD9 is Ddim(addb9), and D SUS2 is Dsusb2b5. Explicit qualities
bypass the final scale correction: G DOM7 remains G–B–D–F in C minor.

Grid recording keeps the normal 16-step layout. VOIC, SPRD and ROOT remain
track-wide controls in the Harmony window; they are not CHRD locks. Follow
inherits roots and scales as before, while every follower resolves its own
CHRD. Live playing does not take over a running leader pattern.

## CHRD storage and migration

CHRD uses one byte per bank/pattern/MIDI-track/step: 8192 bytes per bank,
131072 total. 0xff is unlocked; values 0–7 match the table above. Native bank
formats, NOTE, NOT2–4 and CC lanes remain unchanged. Keep the companions with
the project when copying or backing it up:

- `chrd01.work` through `chrd16.work` accompany working banks.
- `.strd` companions follow project store/reload and Save As copies.
- Version 1 has a 32-byte big-endian header: CHRD magic, version, bank index,
  payload length, FNV-1a payload checksum, native NOTE/trig fingerprint, and
  two zero reserved words. Payload length is exactly 8192 bytes.
- A 32-byte CHNO marker with zero remaining words explicitly represents an
  older stored bank without companion data; it replaces any stale target.

Missing companions mean unlocked TRI in ordinary projects. Bad size, version,
checksum or value range is rejected before any table byte is published. A
native NOTE/trig fingerprint mismatch also rejects the companion. The main
NOTE label becomes CH!, and the CHORD PLAY guide identifies a bad file,
mismatch or save error. Saving refuses to overwrite rejected companions or copy rejected working
data over the stored backup; restore the matching native bank and companion from a backup, or remove the
bad companion from a local project copy and reload it to explicitly discard
its locks. The fingerprint checks NOTE roots and note-trig placement, not all
unrelated CC/Part contents or project identity.

Old HARM TRI becomes CHORD. Old HARM 7TH becomes CHORD and existing note trigs
receive explicit 7TH locks when their bank has no companion. Newly placed or
unlocked trigs still use TRI. A versioned legacy eligibility comment allows
an old stored bank to migrate when reloaded later. VOIC/SPRD and root handling are retained.
A valid new companion is authoritative; corrupt files are never guessed from
legacy settings.

The current bank has a dense checksummed battery-RAM mirror at 0x100f8600
(8224 bytes including its header). It retains all 8192 locks without a sparse
capacity limit. A generation ticket prevents concurrent writers from
publishing mixed snapshots. The mirror retains the current bank’s file-error
status as well, so a restart cannot turn rejected data into a valid empty bank.
Torn CHRD snapshots are rejected in favor of the working companion. The
CHRD mirror is not an atomic transaction with the native NOTE mirror.
Companion/native file writes are not an atomic pair;
interruption between them can require recovery from a matching backup.

This reservation and several native editing hooks conflict with PLOCKS P2.
The build ledger rejects composing both; the personal Harmony remix does not
select PLOCKS P2. This candidate does not claim that combination is supported.

## CHORD PLAY verification and hardware acceptance

Run the linked gates with `make check REMIX=mattias-midi-harmony`. For the
panel/UART and companion lifecycle gate, use a local project template:

```sh
.venv/bin/python tools/verify/verify_chord_play_port.py --project /absolute/path/to/template
```

The gate copies that project into ignored `out/chord-play-port/`; it uses
an immutable image plus matching symbol snapshot so another build cannot
silently change later cases. The receipt records that image's SHA-256.
It checks the mode selector, LED bitmaps, live base and held overrides,
recorded NOTE/CHRD playback, same-step replacement, arp, editing/copy/clear/
undo across banks, unlocked fallback, project/current-bank reload, Save To
New, creation, unsaved resume, malformed companions and refusal to overwrite
rejected data after resume. LCD captures show the actual firmware UI.
For composed audio gates, supply a bus-equipped project to `OT_PROJECT`;
a MIDI-only fixture does not meet TEMPO BUS's host precondition.

After a separately authorized firmware transfer, use a disposable project:

1. Set T1 HARM CHORD, KEY C minor, VOIC ROOT, SPRD CLOSE, ROOT KEEP.
   On the main NOTE page verify D is CHRD and E/F are blank. Enter CHORD PLAY
   with FUNC + UP/DOWN; check the 1–8 and 9–16 LED groups are distinct both
   stopped and running, and held keys are distinguishable.
2. Hold trig 1, then hold trig 10, then trig 13. Hear Cm, Cm7 and Csus4 and
   check the chord name. Release trig 10 first: Csus4 stays. Release trig 13:
   Csus4 keeps sounding without a retrigger. Release the root, then play trig 4 for Fm.
3. Turn D to 7TH. A root now starts as a seventh; held variations temporarily
   override it. Hold trig 5 plus trig 16 and verify G–B–D–F, including through
   the stock arp. Exit the mode, switch to grid and change MIDI/audio mode
   with notes held: no note should remain sounding.
4. Record the Cm/Cm7/Csus4/Fm gesture. Replay it; inspect native NOTE and
   CHRD locks. Turn D live to another quality: recorded locks remain intact.
   Clear one CHRD lock after a different-quality step: it must play TRI.
   Hold a step and turn/push D; check its lock without changing NOT2–4.
5. Copy/paste and clear/undo steps, tracks and patterns, including another
   bank. Save, edit, reload the current bank and project; use Save To New and
   load that copy. Keep bank files and companions together in backups.
6. With an unsaved current-bank CHRD edit, perform a normal power cycle and
   confirm retention. Use a backup copy to check old seventh-project migration.
   Check HARM OFF restores the original notes, NOT2–4 and CC behavior.

Emulation does not prove physical LED colors/brightness, audio load under
hardware timing, electrical MIDI behavior, battery retention or resilience
to power loss during a file write. Companion/native files are not committed
atomically; keep a matching project backup before hardware acceptance.

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
HARM, VOIC, SPRD and ROOT are track defaults, not parameter-lock destinations.

## Automatic voice leading

With HARM CHORD and VOIC AUTO, each track remembers its previous generated
chord and chooses a nearby inversion for the next one. With CLOSE spacing,
C3–E3–G3 followed by F produces C3–F3–A3. The harmonic root is still **F**:
Follow gets F, and recording the physical F key stores F in NOTE. Neither
the lowest voiced note nor the last generated chord tone replaces the root.
Voicing is applied before the stock arp, which therefore plays the chosen
inversion too. A follower with its own HARM CHORD and VOIC AUTO chooses its
own inversions, using the inherited root and scale.

Deliberate octave jumps move the voicing too: C3 → C4 raises every voice
one octave, including an already inverted or OPEN/WIDE chord. Before scoring,
AUTO shifts its previous chord by the whole-octave portion of the logical
root's change (toward zero: +12…+23 means +12; −12…−23 means −12).
Smaller root changes keep ordinary voice leading; crossing B3 → C4 does not
force an octave jump. MIDI limits still apply. This uses transient history
only; project settings and recorded notes are unchanged.

AUTO keeps the exact requested root pitch in every candidate; ROOT can still
lower or omit it afterward. Repeated roots keep their previous voicing.
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
that track's keyboard and sequence. HARM/VOIC/SPRD/ROOT edits, project load,
and boot reset it; a changed effective scale/source or triad/seventh count
reseeds it on the next chord. A truncated high-MIDI chord keeps the existing
voice-omission behavior and resets history. Silence/STOP alone does not reset
history; set VOIC ROOT then AUTO to deliberately reseed it. AUTO is dynamic:
the same stored root can receive a different inversion after a different
preceding chord. Held keys retain their original note-offs when settings change.
VOIC and SPRD have no effect in HARM OFF/NOTE.

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

## Root placement

ROOT shapes the existing harmonic root after inversion and spread. It never
adds a fifth voice. For a C4 major seventh chord with VOIC ROOT/SPRD CLOSE:

| ROOT | Sounded notes |
| --- | --- |
| KEEP | C4–E4–G4–B4 |
| OMIT | E4–G4–B4 |
| -1 OCT | C3–E4–G4–B4 |
| -2 OCT | C2–E4–G4–B4 |

KEEP retains the complete voiced chord. OMIT removes the harmonic root pitch
class wherever the inversion places it. -1 OCT and -2 OCT replace that root
with the generated logical root minus 12 or 24 semitones: the anchor is the
root before inversion/spread, not the lowest voiced note. The other chord
tones keep their pitches. For C4 major with VOIC 2ND, G4–C5–E5 becomes
C3–G4–E5 with -1 OCT. The resulting pool enters the stock arp normally;
there is no separate bass channel or special sustained-bass behavior.

Only HARM CHORD uses ROOT, including with KEY OFF. NOTE and OFF stay
unchanged. MIDI Follow still receives the original harmonic root and live
recording still stores the physical key once. AUTO optimizes and remembers
the full underlying chord before ROOT placement, as it previously did for
OMIT. Changing ROOT resets that track's AUTO history and affects the next
chord trigger. Already-held keys retain their original release pitches.

If the requested low root falls below MIDI note 0, it is omitted; it never
wraps or clamps to an unrelated pitch. Other available chord tones continue.
At the high MIDI limit, ROOT placement acts on the available tones, retaining
the generator's omission of unavailable upper voices. An empty OMIT result
remains silent with balanced key/recording ownership and a safe arp pool.

Existing OMIT OFF/ROOT settings migrate to ROOT KEEP/OMIT. ROOT remains a
per-track project setting, not a parameter-lock destination.

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
own final correction for scale-derived chords before note ownership is
recorded. Explicit MAJ, MIN and DOM7 qualities retain their selected intervals. Follow captures Harmony's selected root before the arp and bypasses
its old final bass-only
replacement when Harmony is active. Each module also builds independently.

Battery RAM 0x100b14e2..e9 stores one byte per track: TYPE in bits 0–1,
SPRD in bits 2–3 (0 CLOSE, 1 OPEN, 2 WIDE), manual inversion in bits 4–5
(0 root, 1 first, 2 second, 3 third), and ROOT in bits 6–7 (0 KEEP, 1 OMIT,
2 -1 OCT, 3 -2 OCT). ea retains one AUTO bit per track; eb is version 0x4f.
Fresh projects are the target for this combined development build; the
intermediate 0x4e development layout resets. Existing support for older
versions is retained: boot migrates 0x4d preserving the former OMIT bit; its formerly invalid bit-7
values reset rather than becoming accidental octave drops. Versions 0x4c,
0x4b and 0x4a retain their supported settings with ROOT KEEP. Invalid spread
encodings reset the affected track. Quantizer's ec..ee bytes stay separate.

Project comments write TYPE_V1 (0..2), VOIC_V1 (0..4) and SPRD_V1 (0..2).
The reader also accepts historical TYPE_V1=3 as CHORD with a seventh default.
`#MIDI_HARMONY_ROOT_V1_T1=0` through T8 store ROOT (0..3). Old
`#MIDI_HARMONY_OMIT_V1_T1=0` through T8 are still read as KEEP/OMIT; save
writes a legacy OMIT value first, then the full ROOT value, for each track.
The legacy value is 1 only for OMIT; older firmware falls back to KEEP for
an octave-drop selection. Parse-only loads never write settings. Missing
comments default to HARM OFF, VOIC ROOT, SPRD CLOSE and ROOT KEEP.
Native Part/pattern formats are unchanged. Older firmware resets Harmony's
battery state on a version mismatch; reload a saved project after rollback
to restore the settings that firmware supports. Voice-leading history and
window state are volatile module DRAM, not project data.

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
Use `--live-transpose-only` for physical TRAN edits during held chromatic and
CHORD PLAY notes: stock direct/arp behaviour, all eight qualities, scale
correction, combined voicing/spread/ROOT placement, MIDI bounds and releases.
The machine gate also compares the live transpose path with native stock
instructions across every MIDI pitch, signed TRAN offsets and arranger offsets.
Use `--voicing-only` for AUTO sequence/keyboard/arp, recorded physical roots,
SPRD variants, Harmony-page controls, and actual save/reload/warm-resume checks. These also
produce the Harmony window screenshot at `out/harmony-port-suite/harmony-page/page.png`.
Use `--bypass-follow-only` for live HARM OFF / KEY OFF source roots driving rhythmic followers.
Use `--octave-only` for live C-minor octave jumps in TRI/7TH with every spacing.
Use `--spread-only` for the ten spaced sequence/arp and follower-root cases.
Use `--root-only` for ROOT octave placement through sequences, live overlapping
keys, arp, followers, recording/replay, physical encoders/LCD and save/reload/warm resume.
Use `--inversions-only` for manual inversions, stock arp, follower-root identity,
root omission, physical-key recording/replay and manual-VOIC/OMIT save/reload/warm resume.
The default full suite includes all groups. The machine gate compares AUTO's
movement cost against all valid compact and spaced voicings across keys/scales/MIDI range,
checks per-track history and context resets, and polices writes and registers.
They do not verify electrical MIDI timing, battery
retention, musical feel or a physical flash. No device transfer is performed.

### Hardware acceptance for ROOT placement

With KEY C Major, HARM CHORD, CHRD 7TH, VOIC ROOT and SPRD CLOSE, open NOTE SETUP,
press F and turn D through KEEP, OMIT, -1 OCT and -2 OCT. For a C root,
expect the table above. Repeat with manual inversions, AUTO and OPEN/WIDE:
only the harmonic root moves or disappears, while a separate MIDI follower
retains the original root. Repeat with the stock arp.

Hold overlapping C and E chords, change ROOT while they are held, then
release both: no stuck notes or incorrect releases. Live-record C/D/F and
confirm NOTE stores the physical keys and replay reproduces the moved roots.
Save/reload and power-cycle to check persistence. Near the bottom of MIDI,
an unavailable lowered root must disappear rather than wrap. These checks
remain pending on hardware; emulator results do not prove electrical timing
or physical battery retention.

### Hardware acceptance for inversions, AUTO and physical-key recording

With HARM CHORD, CHRD TRI, VOIC 1ST/2ND, SPRD CLOSE and KEY C Major, check C gives
E–G–C / G–C–E. Select 3RD: a triad still uses 2ND; CHRD 7TH gives
B–C–E–G. Repeat with OPEN/WIDE and the stock arp. A root-following bass
must still play C, then F when playing F. Record physical C/D/F keys and
confirm NOTE stores those keys and replay regenerates the selected inversion.
Select ROOT OMIT and confirm only C disappears from each C chord, regardless
of inversion, while the bass still plays C. Save/reload the project and check
the manual VOIC and ROOT choices survive.


Use a disposable pattern, with T1 KEY C Major and TRAN 0. Set HARM CHORD and CHRD TRI,
press F on NOTE SETUP, set B VOIC AUTO and C SPRD CLOSE. Play C then F: expect C–E–G
then C–F–A. Hold both keys and release them in either order: shared C must
continue until its final owner releases, with no stuck notes. Repeat with
the stock arp active, and with CHRD 7TH. Set VOIC ROOT and check each
SPRD against the table above; repeat with AUTO and change SPRD while
a key is held to check that its release leaves no stuck notes.

Set T2 RFOL T1, HARM NOTE, TRAN 0 and program its rhythm. While performing
on T1, F must make T2's next trig play F, even though T1's lowest voice is C.
Repeat with T2 HARM CHORD, CHRD TRI and its own AUTO: it must retain its own rhythm and
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

With C minor, HARM CHORD, CHRD TRI, VOIC AUTO, SPRD OPEN, ROOT KEEP, play C3 → C4 → C3.
Expect C3–G3–E♭4 → C4–G4–E♭5 → C3–G3–E♭4, with no stuck notes.
OCTABAM5 incorrectly reused the first chord for both roots; the emulator
reproduced that failure through actual chromatic-key events. Repeat with
7TH and other spacing choices, then C → F to retain smooth voice leading.
The automated regressions live in the linked gate and full-firmware suite;
a passing emulator run is not hardware acceptance of the corrected build.

UI refinement: HARM and the detail-page choices use the stock encoder accumulator
with four raw counts per selection and a one-choice cap per input report. Closing
the detail window redraws NOTE SETUP from the current HARM value. Hardware feel
still needs a physical check.

CHORD PLAY's guide shows the currently sounding chord and its captured MIDI
pitches on one line above the chord name. The octave uses the stock CHROMATIC
PLAY box, position and numbering (MIDI 60 is C4). Long pitch lists use compact
sharps and separators to keep all four notes visible. Released chords disappear;
sequencer playback supplies its own root/CHRD identity and native active-note
ownership. With overlapping live roots, the latest still-held root is shown;
releasing it reveals another held root or the sequencer. The display reads
captured voices and each held root's captured quality rather than rerunning AUTO. Live and held-step CHRD selection
uses the same four-count stock accumulator as Harmony's other new controls.

`tools/verify/verify_chord_display.py --project DIR` checks captured pitches,
release/STOP clearing, native octave changes and sequencer UART agreement on a
copied virtual card. These remain emulator checks, not hardware acceptance.

### Playability candidate: root anchoring and WIDTH

AUTO now admits only candidates containing the exact generated root pitch.
Playing C4 keeps C4 in the chord, regardless of earlier progressions; other
voices can still invert around it. KEY snapping and TRAN happen before this
anchor, and ROOT OMIT/-1 OCT/-2 OCT still apply afterward. A root need not be
the lowest voice. The bounded search and MIDI limits remain unchanged.

Harmony window **F: WIDTH** is a temporary per-track audition control:
**FULL** (default) retains existing OPEN/WIDE. **SOFT** makes OPEN lower the
third sorted voice by one octave, and makes WIDE use the former OPEN shape.
For a C4 major triad with VOIC ROOT and ROOT KEEP:

| WIDTH | OPEN | WIDE |
| --- | --- | --- |
| FULL | C4–G4–E5 | C4–E5–G5 |
| SOFT | G3–C4–E4 | C4–G4–E5 |

SOFT OPEN on a seventh is a drop-2 voicing; on a triad it lowers the fifth.
This keeps the root's register while reducing the upper register's weight;
it can put another chord tone below the root. CLOSE is identical in both.
At MIDI boundaries a spread that cannot fit falls back to the unspread chord.
WIDTH clears AUTO history when edited. It is intentionally volatile: it is
not saved into project comments or battery RAM and starts FULL at firmware
boot. Hardware playing feel remains to be evaluated.

`tools/verify/verify_harmony_playability.py` exercises anchored AUTO through
repeated scale/fifths progressions, octave changes, all available keys/scales,
all spreads, both WIDTH choices and MIDI boundaries. This is machine-code
emulation, not electrical MIDI or hardware acceptance.


## Concert stress findings (8 October 2026)

The eight-track full-firmware reproduction in `out/concert-port` exposed
an ownership defect: sounding C/E/G on channels 1 through 8 produced 24
note-ons, but only three releases, all on channel 8. Stock keyboard release
tokens at `0x46c79d70` are indexed only by pitch. Harmony's per-track reference
counts did not protect the stock layer from overwriting those tokens.

A second reproduction switches HARM OFF while C/E/G remains held, then
presses/releases E. The bypass call releases the held chord's E prematurely.
The dense active-Harmony model alone did not catch either problem: 1,024
simultaneous physical keys and 14,742 edges passed at the intercepted stock
keyboard boundary. This is why both boundary checks and real UART captures
are required. The fix gives generated notes private per-track stock release tokens and
coalesces shared direct channel/pitch owners. Captured tokens release the
original destination after channel edits and CHAN OFF. Bypass notes that
intersect held Harmony tones join its reference counts; an earlier bypass
note is adopted when a new chord shares it. Unrelated bypass stays native.
Four pinned slot detours recognize only the owned-call return PC; there is
no shared temporary pointer or new interrupt mask.

The stateful linked gate runs three reproducible seeds, over 44,000 key
edges, 1,024 simultaneous keys, NOTE/triad/seventh changes, all track/scale
contexts available in the selected image, and randomized release order.
The full port suite passes 12 scenarios and 5,998 UART note events:
1,024 simultaneous pitches, separate/shared/paired channels, both bypass
transition orders, stock bypass parity, channel changes/OFF while held,
eight arps, 80 shared-channel churn cycles, and an eight-track sequence.
Every scenario checks balanced notes, empty ownership and unchanged banks.
In a combined build, the sequence additionally runs an eight-track Follow
chain. Fixtures and receipts are under `out/midi-concert-port/`.

```
.venv/bin/python tools/verify/verify_midi_harmony_stress.py
.venv/bin/python tools/verify/verify_midi_concert_port.py --project /path/to/template
```

Live port events enter the real keyboard C ABI; sequence events run through
native transport. They do not prove external-input parser throughput,
physical DIN/USB jitter, hardware CPU headroom, or a hours-long concert.
The port itself needed a caller-stack cleanup fix before the longest floods
were meaningful; `tools/emu/README.md` records that separate finding.
No physical firmware was flashed or tested.
