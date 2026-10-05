# MIDI Harmony

On a MIDI track, open **NOTE SETUP** (FUNC + SRC). Knob **F: HARM** selects:

| HARM | Output |
| --- | --- |
| OFF | Stock notes and stored NOT2–4 |
| NOTE | One note snapped to the selected scale |
| TRI | A diatonic triad on the selected note: scale degrees 1, 3, 5 |
| 7TH | A diatonic seventh chord: scale degrees 1, 3, 5, 7 |

Choose KEY in its original position, **ARP SETUP F** (FUNC + AMP).
Without MIDI Scales, Harmony uses stock Major/Minor. Installing MIDI Scales
adds five modes in every key. **KEY OFF bypasses Harmony**, including chord
generation. HARM defaults OFF.

For example, C Major with HARM TRI turns C, D and F into C major, D minor
and F major. C Dorian gives C minor, D minor and F major. Chromatic trig keys
snap to nearest valid notes (ties downward), so adjacent keys can coincide.
This first version does not replace a running pattern's chord from the live
keyboard: live performance transposition remains a separate future feature.

The same generator serves live MIDI keys and sequenced NOTE/P-locks.
Generated chords enter the **stock arp before its note selection**. ARP MODE,
SPD, RNGE, NLEN, LEG and step offsets retain their stock controls. Original
NOT2–4 values are never overwritten. Turning HARM OFF restores their use.
High chord voices beyond MIDI 127 are omitted; pitches do not wrap.

With MIDI Follow, RFOL stays on NOTE SETUP D. The follower retains its own
HARM, rhythm and TRAN/P-locks, while its chord root and KEY come from the
ultimate source track. KEY is displayed from that source and is read-only
on the follower. Disable RFOL to restore the follower's own Part KEY.
TRAN remains a semitone offset applied once after chord generation; +7 and
+12 mean exactly those intervals and may intentionally leave the scale.

HARM is stored per MIDI track per **project**, not per Part/pattern. It is
saved in backward-compatible project comment lines and survives battery-RAM
resume. KEY remains a native Part setting. MIDI Follow's RFOL selection is
still its existing volatile setting; select it again after power-up.

## Implementation boundaries

The sequence hook changes the four-note scratch buffer before the stock arp
initializer. Unused voices duplicate the root for its valid-pitch bitmap;
stock deduplicates them. Live keys keep the generated pitches until release,
with reference counts for shared chord tones. A bypassed press also retains
its stock release path if HARM or KEY is enabled while held. Stock owns MIDI transmission,
arp insertion/removal and sequenced note-off records.

Harmony skips a second stock scale correction after TRAN. Follow captures
Harmony's selected root before the arp and bypasses its old final bass-only
replacement when Harmony is active. Each module also builds independently.

TYPE storage: battery RAM 0x100b14e2..e9, ea reserved, eb version 0x4a.
This is the stock linker padding before the record at 0x100b14f0; Quantizer's
ec..ee bytes are separate. Defaults and boot sanitize it. Project comments
are `#MIDI_HARMONY_TYPE_V1_T1=0` through T8, each 0..3. Parse-only loads do
not write settings. A project without these lines starts with HARM OFF.

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
project persistence, plus added-scale output with Harmony OFF. They do not verify electrical MIDI timing, battery
retention, musical feel or a physical flash. No device transfer is performed.
