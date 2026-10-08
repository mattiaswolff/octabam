# MIDI roots, scales and chords

A shared workflow for **MIDI Follow, MIDI Scales and MIDI Harmony**.
[MIDI Scenes](../../modules/midi-scenes/README.md) covers scene locks and
crossfader morphing separately. Other MIDI modules have their own guides.

MIDI tracks can share a root progression while keeping their own note trigs,
velocity, note length and arpeggiator settings. Choose where each track gets
its root, then how it plays that root.

Musical scales use **KEY** on ARPEGGIATOR SETUP. **SCALE SETUP** controls
sequencer length and timing.

## What each module adds

| Module | Use it to |
| --- | --- |
| [MIDI Follow](../../modules/midi-follow/README.md) | Select another MIDI track as the root source with RFOL; choose a fixed or source-relative octave. |
| [MIDI Scales](../../modules/midi-scales/README.md) | Add five modes to the existing Major/Minor KEY choices. |
| [MIDI Harmony](../../modules/midi-harmony/README.md) | Snap a root to KEY with HARM NOTE, or generate a voiced chord with HARM CHORD. |

Each works independently. Harmony supports stock Major/Minor without Scales.

## One progression, three MIDI tracks

Use a remix containing Follow and Harmony. Give T1–T3 separate MIDI output
channels and start with TRAN at 0.

1. **T1: root progression.** Set KEY to C Major on ARPEGGIATOR SETUP
   ([FUNC] + [AMP]). Place note trigs with NOTE parameter locks for C, F and G.
2. **T2: bass.** On NOTE SETUP ([FUNC] + [SRC]), turn knob D, RFOL, to T1.
   Press D to choose FIXED and a low OCT. Leave HARM and the arpeggiator OFF.
   Place note trigs for the bass rhythm.
3. **T3: chords.** Set RFOL to T1 and HARM to CHORD on NOTE SETUP, knob F.
   Place note trigs for the chord rhythm; unlocked CHRD uses TRI. Press F on
   NOTE SETUP to adjust VOIC and SPRD. Enable T3's arpeggiator if wanted.

T2 plays C, F and G in its chosen octave. T3 generates C major, F major and
G major. Each track plays on its own note trigs. T3 takes its KEY from T1;
its displayed KEY is read-only while following.

## What following means

- RFOL selects a **MIDI track**, independently of its output channel.
  The source's arpeggio does not change the followed root.
- A sequenced follower uses the latest source root on its next note trig.
  With RESP NEXT (default), held notes are not repitched. Rests retain the
  root. Until a source root
  is known, the follower plays its own notes.
- Muting the source silences its output while its sequenced root progression
  continues to drive followers. Keep its output channel enabled.
- Use the follower's **TRAN**, including parameter locks, for pitch offsets.
  Follow alone uses semitones. With Harmony active, the transposed root is
  snapped to the source's KEY before scale-derived chords are generated.
- RFOL OFF restores the track's own root selection. HARM OFF restores use
  of stored NOT2–4; Follow can still replace those notes while RFOL is active.

## Playing, recording and saving

**CHORD PLAY** belongs to Harmony. Outside GRID RECORDING mode, trig keys
1–8 play roots and 9–16 select chord variations. Recording stores the root
and CHRD choice; playback regenerates the chord, leaving NOT2–4 untouched.
Live playing does not replace a running pattern's root progression.

**KEY is a Part setting.** HARM, VOIC, SPRD and ROOT are saved per MIDI track
in the project. CHRD locks belong to sequencer steps and use project companion
files; keep those files with the project when backing up or copying it.
**RFOL, MODE and both OCT values are saved per MIDI track in the project**
and restored on restart. Use the normal project SAVE/RELOAD commands.
Changing Parts does not change the Follow setup.

See the module READMEs for full controls, storage details and verification
status. These are development modules; hardware acceptance remains pending.
