# MIDI Harmony

MIDI Harmony supplies scale-degree roots, generated chords and CHORD PLAY.
Include `MIDI HARMONY` and its shared dependency `MIDI PART STATE` in a remix.
MIDI FOLLOW and MIDI SCALES are optional. Degree support is part of Harmony;
there is no separate module to select.

Open MIDI **NOTE SETUP** with **FUNC + SRC**. Turn **F: HARM**:

| HARM | Main NOTE page | Output |
| --- | --- | --- |
| OFF | Native NOTE / NOT2–4 | Stock playback |
| NOTE | A: DEG | One scale-degree root |
| CHORD | A: DEG, D: CHRD | Chord built from that root |

Choose **KEY** on **ARP SETUP F** (FUNC + AMP). MIDI SCALES adds five modes
to stock Major/Minor. DEG reads `1:3`: degree 1, tonic octave 3. Turning A
advances through the scale; **FUNC + A changes only the octave**. Hold steps
to edit their DEG locks; press A while holding steps to toggle those locks.
FUNC octave editing also works on held steps and MIDI Scene root locks.

Changing KEY preserves stored degrees. For example, 1–4–5 in C minor plays
Cm–Fm–Gm; changing KEY to D minor plays Dm–Gm–Am. Turning HARM on converts
native roots to the nearest scale degree (ties downward). Turning it OFF
materializes resolved roots as native NOTE. NOTE ↔ CHORD preserves degrees.
KEY OFF uses C major for degree mapping and unscaled chord recipes. Native
NOT2–4 remain stored and become active again in OFF. A degree resolving
outside MIDI 0–127 is silent; OFF conversion clamps to that native range.

Press **F** on NOTE SETUP to open **HARMONY**:

| Knob | Setting | Values |
| --- | --- | --- |
| A | HARM | OFF / NOTE / CHORD |
| B | VOIC | ROOT / AUTO / 1ST / 2ND / 3RD |
| C | SPRD | CLOSE / OPEN / WIDE |
| D | ROOT | KEEP / OMIT / -1 OCT / -2 OCT |
| E | SIZE | NAT / 2 / 3 / 4 |

F is inactive. YES, NO or F closes the window; track/page keys close it
before changing selection on a second press. Edits apply immediately. YES
on NOTE SETUP preserves RFOL and HARM while confirming stock staged fields.
Fresh Parts use HARM OFF, DEG `1:3`, CHRD TRI and ROOT/CLOSE/KEEP voicing and SIZE NAT.

Generated notes enter the stock arp. Sequenced TRAN/P-locks apply once before
chord generation; scale-derived qualities receive final scale correction.
Explicit MAJ/MIN/DOM7 retain their chromatic tones. Live keys use stock TRAN
behavior: none with arp OFF, current TRAN and arranger offset with arp ON.
Live recording captures one root degree and CHRD per played event, never
extra chord tones in NOT2–4. Live keys do not replace a running pattern's root.

With MIDI FOLLOW, the receiver keeps its rhythm, HARM, CHRD, voicing and TRAN.
Its root and effective KEY come from the ultimate source, before voicing or
ROOT placement; MODE/OCT sets the receiver's register. Source KEY is shown
read-only on the receiver. Held notes retain their original release identity.

## CHORD PLAY and CHRD

Set HARM to CHORD, then return to the main MIDI NOTE page. D displays CHRD
in the old NOT2 position; E/F are inactive. Native NOT2–4 values remain stored
and become available again with HARM OFF. Turning D alone selects the live
chord. The CHRD knob displays this base value during performance; temporary
extensions appear in the sounding-chord guide. Hold one or more sequencer steps and turn D to edit their CHRD locks;
press D while holding steps to toggle their locks. Unlocked steps display
and play the current Part's base CHRD, independently of the previous step.

Choose CHORD PLAY with the normal FUNC + UP/DOWN mode selector. Outside grid
recording, trigs 1–8 play the selected scale from tonic through the next octave.
With KEY OFF they use C–D–E–F–G–A–B–C as roots; each TRI is major.
The stock-style inverted title bar reads CHORD PLAY when idle and shows the
actual MIDI notes while sounding. Chord names and note names both use sharps.
A compact line below the chord name always shows SIZE, VOIC, SPRD and ROOT:
`N:4 V:1 S:O R:-1` means four notes, first inversion, OPEN spread,
root down one octave. N:N means SIZE NAT.
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
Names use sharps. Scale alterations are retained:
in C minor, D ADD9 is Ddim(addb9), and D SUS2 is Dsusb2b5. Explicit qualities
bypass the final scale correction: G DOM7 remains G–B–D–F in C minor.

Grid recording keeps the normal 16-step layout and the guide follows the
sounding sequence. Rests and STOP clear the chord name and pitches. SIZE, VOIC, SPRD and ROOT remain
track-wide controls in the Harmony window; they are not CHRD locks. Follow
inherits roots and scales as before, while every follower resolves its own
CHRD. Live playing does not take over a running leader pattern.

## Chord size

SIZE sets how many distinct MIDI pitches Harmony sends to the stock arp.
NAT keeps the original chord recipes, inversions, ROOT behavior and AUTO
history rules. Fixed 2/3/4 counts use the following rules instead. They affect
HARM CHORD only and apply on the next trigger; held notes retain their releases.

First choose the chord tones. Keep the root unless ROOT is OMIT. Prioritize
the seventh/ninth for 7TH/DOM7/ADD9, or the suspension for SUS2/SUS4. Next keep
an altered fifth if present, then the third and ordinary fifth as space allows.
A plain triad prioritizes its third; a diminished triad prioritizes its b5.
This is a deterministic reduction, not a reharmonization or classical
part-writing engine. Two-note reductions necessarily leave some identity implied.

| Chord, ROOT KEEP | SIZE 2 | SIZE 3 | SIZE 4 |
| --- | --- | --- | --- |
| TRI / MAJ / MIN, ordinary fifth | Root + third | Complete triad | Triad + octave doubling |
| SUS2 / SUS4 | Root + suspension | Complete chord | Chord + octave doubling |
| 7TH / DOM7, ordinary fifth | Root + seventh | Root + third + seventh | Complete chord |
| ADD9, ordinary fifth | Root + ninth | Root + third + ninth | Complete chord |

For an altered-fifth seventh/add9 at SIZE 3, retain root, altered fifth and
extension, leaving out the third. SIZE 4 retains all four tones. ROOT OMIT
removes the root from consideration before selection: a normal seventh at
SIZE 2 gives third + seventh; a triad gives third + fifth. Scale-derived
alterations stay intact; no new chord tones are invented.

Invert the **retained distinct tones**, then fill spare voices with octave
copies, starting from the lowest tone and working upward. Doublings do not
create additional inversions. An unavailable inversion uses the last one:
3RD on a three-tone chord uses 2ND; 2ND/3RD on two tones use 1ST.

| C major, SIZE 4 / CLOSE / KEEP | Sounding pitches |
| --- | --- |
| VOIC ROOT | C3–E3–G3–C4 |
| VOIC 1ST | E3–G3–C4–E4 |
| VOIC 2ND or 3RD | G3–C4–E4–G4 |

SPRD operates on the expanded chord. OPEN raises the second-lowest note an
octave; if a doubling already occupies that pitch, use the next free octave.
WIDE raises every note above the bass an octave. For two voices, OPEN and
WIDE are equivalent. A spread that exceeds MIDI 127 falls back to CLOSE.
ROOT -1/-2 OCT places exactly one root at the requested lower register;
extra voices double non-root tones. SIZE therefore remains the **sounding**
count with KEEP, OMIT or a dropped root. When MIDI limits make that impossible,
sound fewer notes and reset AUTO history; never wrap or add an unrelated tone.

Fixed SIZE AUTO compares the final sorted sounding notes, including doubling,
spread and root placement. It minimizes total semitone movement, then prefers
more stationary voices. Equal scores prefer root position, then earlier
inversions and octave offsets 0/-12/+12. It searches at most twelve candidates,
keeps the bass near the requested register and retains the exact root with
KEEP (or the exact lowered root with a drop). Chord-quality changes keep
history: C3–E3–G3 can become C3–E3–B3 when TRI changes to 7TH at SIZE 3.
Changing SIZE resets history; other settings, source/scale, Part replacement
and deliberate octave jumps follow the same boundaries as NAT. There is no
promise to avoid parallel intervals or resolve classical tendency tones.

SIZE is a per-track Part default, not a parameter lock. CHRD locks still
select chord identity; SIZE determines its realization. The guide displays
the requested chord name and actual sounding pitches; a reduced voicing can
omit a tone implied by that name. Native Part Save/Reload, copy and KITS recall
carry SIZE. Old valid CHRD bytes select NAT. Pattern HDP3/HDN3 storage and the
10,400-byte retained reservation are unchanged. Older firmware does not decode
the newly packed CHRD/SIZE byte; use a project copy when testing this candidate.

## Manual inversions

The following sections describe SIZE NAT unless stated otherwise.

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
HARM, SIZE, VOIC, SPRD and ROOT are track defaults, not parameter-lock destinations.

## Automatic voice leading

With HARM CHORD and VOIC AUTO, each track remembers its previous generated
chord and chooses a nearby inversion for the next one. With CLOSE spacing,
C3–E3–G3 followed by F produces C3–F3–A3. The harmonic root is still **F**:
Follow gets F, and recording the physical F key captures its degree. Neither
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
inversions and offsets in the listed order. At most twelve candidates
of four voices are considered per chord; there is no unbounded search.

The first chord uses root position with the selected spread. History is per track and shared between
that track's keyboard and sequence. HARM/VOIC/SPRD/ROOT edits, project load,
and boot reset it; a changed effective scale/source or chord quality/count
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
harmonic root and recording captures the physical key as one degree.

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
recording captures the physical key as one degree. AUTO optimizes and remembers
the full underlying chord before ROOT placement, as it previously did for
OMIT. Changing ROOT resets that track's AUTO history and affects the next
chord trigger. Already-held keys retain their original release pitches.

If the requested low root falls below MIDI note 0, it is omitted; it never
wraps or clamps to an unrelated pitch. Other available chord tones continue.
At the high MIDI limit, ROOT placement acts on the available tones, retaining
the generator's omission of unavailable upper voices. An empty OMIT result
remains silent with balanced key/recording ownership and a safe arp pool.

ROOT is a per-track Part setting, not a parameter-lock destination.

## Storage and validation

HARM, DEG, CHRD, SIZE, KEY, voicing and Follow settings live in each native Part.
UI edits use the selected Part; playback uses each track's playing Part.
Part/Kit recall supplies incoming defaults; explicit DEG/CHRD locks stay with
patterns. Runtime roots, note ownership and AUTO history are not persisted.

Keep `hdeg01.work`–`hdeg16.work` and their `.strd` companions with the project.
They store pattern DEG/CHRD locks in compact HDP3 format. There is no migration
from earlier Harmony formats or project-comment settings. Start with a project
copy without older `hdeg` companions; incompatible files block overwriting saves. See [degree storage](degrees/README.md) for the
layout, failure handling and native boundary rules, [KITS](degrees/KITS.md)
and [MIDI Scenes](degrees/SCENES.md) for composition details. PLOCKS P2 conflicts
with the retained-memory reservation and editing hooks; the ledger rejects it.

Run `make check REMIX=harmony-degrees` for the minimal verification carrier.
For a prepared local project copy, run the full firmware gates:

```sh
.venv/bin/python tools/verify/verify_harmony_degree_port.py --project /path/to/project
.venv/bin/python tools/verify/verify_chord_display.py --project /path/to/project
.venv/bin/python tools/verify/verify_midi_setup_port.py --project /path/to/project
```

The manifest declares linked-code gates for routing, voicing, ownership,
recording, native Part publication, degree boundaries and companion storage.
See the [hardware acceptance sequence](degrees/ACCEPTANCE.md) for instrument
checks. Emulator results do not establish physical MIDI timing or battery retention.

The SIZE gate executes generated ColdFire code (`verify_harmony_size.py`);
`verify_harmony_size_port.py --project DIR` checks real firmware output.
Regenerate `size.s` with `python3 modules/midi-harmony/generate.py` and verify
with `--check`; edit the C source, never its generated assembly.
