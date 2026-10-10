# mattias-bus

Personal bus remix with BusDelay on T1, BusVerb on T5, SEND on T2–4/T6–7
and stock DELAY on master T8. FX1 offers Spectrum, Character and Modulation.
Includes Tempo Sync/Bus, Rig Hosts, FX2 Lock, Mode Defaults, RLEN PLEN, Tuner,
MIDI Part State, Follow, Scales, Harmony/Chord Play, KITS and MIDI SCENES.

PLOCKS P2 is excluded: its retained region and editing hooks still conflict
with Harmony. PLOCKS, KITS and MIDI SCENES sources are unchanged.

Harmony uses the new HDP3/HDN3 packed format: 10,400 bytes per bank including
the header. It retains every CHRD and DEG and reconstructs exact canonical
NOTE snapshots. Prior Harmony companions are not migrated. See [Harmony storage](../../modules/midi-harmony/degrees/README.md).

Source and emulator validation do not establish hardware acceptance. Package
receipts record the exact source, checks, firmware hashes and known limitations.

H5 includes measured CPU optimizations to the existing H3 behavior. See
[CPU measurements](CPU.md) for the repeatable benchmark, results and tradeoffs.

H6 adds per-track Harmony **SIZE NAT/2/3/4** on encoder E of the Harmony
window. Fixed sizes preserve their sounding count through inversions,
SPRD and ROOT placement and carry AUTO history across CHRD changes.
See [the musical rules](../../modules/midi-harmony/README.md#chord-size).
NAT retains H5 output. SIZE uses spare bits beside the Part's CHRD default;
HDP3/HDN3 and the 10,400-byte retained reservation are unchanged. Use a
project copy for the candidate: older firmware does not decode fixed SIZE.
