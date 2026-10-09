# Degree compatibility with MIDI Scenes

Development candidate: `mattias-bus-degrees-scenes`, build DS. Based on the
completed degree/Part/KITS handoff `9cf41ec9` and upstream PR #647
`83a9d6c103e9f127c191769d9f51f01555419c89`. MIDI SCENES remains pinned to
MIDISC2.1 submodule `52eaab0a7bff43b0316e522a03199106d1553e98`.
KITS and MIDI SCENES source and linked bytes are not edited by this adapter.

## Controls and storage

With HARM NOTE/CHORD, the scene root is DEG (0..83). The crossfader interpolates
degree codes, then Harmony resolves the result through the effective KEY.
Changing KEY preserves scene degree identity. An empty endpoint inherits the
captured pattern lock or the current Part DEG default. Out-of-range resolved
pitches remain silent. CHRD stays a Part/pattern setting; holding a scene does
not edit CHRD or the hidden native NOT2–4 controls. Other native scene controls
retain MIDI SCENES behavior.

Explicit HARM OFF converts that Part's scene roots to native NOTE; switching
back encodes them against the new effective KEY. NOTE/CHORD changes preserve
degree values. Part/Kit recalls carry their own mode and scene representation.
The upstream sparse format, 46 stored endpoints and 32 active parameters are
unchanged. Both endpoints of the same parameter consume one active slot.

Scene editing, packing, clearing and persistence remain upstream-owned. Our
native hold-prefix adapters seed DEG from the Part DEG, clamp its range and
supply the degree display. No separate persistent scene store is introduced.

## Native boundaries

- Harmony publishes queued DEG/CHRD identity at `0x400a19ce`, before the
  unchanged scene pending-copy hook at `0x400a19da`.
- Scene endpoint snapshots are prepared before MIDI PART STATE publishes its
  outgoing bank pointer. Playback sees native outgoing data during snapshot
  preparation, the complete snapshot during copy, then the incoming Part.
- The PR's pattern-commit hook at `h_400c4704` contains `lea 240(sp),sp`, followed
  by `lea 16(sp),sp`: the gas port zero-fills an omitted stock `0xff` byte in
  the intended negative displacement. The unchanged KITS+Scenes `ok-ms`
  baseline and combined candidate both jump to `0x46c82000` on live pattern
  change. Our prefix at `0x400a44ee` reserves 256 bytes and supplies the native
  continuation in that hook's resulting return slot. It never rewrites the
  hook. The linked gate pins the exact offending opcode and checks stack and
  registers across valid, unchanged and invalid context paths. A different
  upstream hook requires revalidation of this adapter.

## Evidence in progress

`tools/verify/verify_harmony_degree_scenes.py` covers all 32 pending slots,
24,576 fader/key/track combinations, empty endpoints, malformed data, capacity,
real native scene edit/pack/morph, OFF round trips, and interrupted native Part
copy. It also checks that adapters are inert when MIDI SCENES is absent.
The worst measured scene-root preparation masks 2,844 emulated instructions;
this is not a hardware timing measurement.

The full-firmware verifier is `verify_harmony_degree_scenes_port.py`. Native
scene editing, project SAVE, cold reload and retained resume passed during
iteration. NOTE/CHORD roots follow KEY, and native OFF retains NOT2 locks.
The first nonresident Kit recall with scenes passed with held-key releases,
explicit CHRD locks, incoming scene roots and unchanged library bytes.

The original shared check's 15 KITS playback failures are retained in
`out/scenes-check-shared.log`. The stack adapter fixes live pattern changes; the complete KITS rerun passes
with zero failures. Eight-track physical-fader sweeps pass for shared-channel
chords and distinct-channel arps. A fixture that zeroed unused sparse padding
silenced arps even on stock; preserving untouched bytes, as the native packer
does, fixes the fixture. This does not establish compatibility with every
use of the upstream Part window (notably native LFO designer records).

The final degree lifecycle, musical Kit matrix and selected remix gates are
running on the frozen image. Packaging and hardware acceptance remain pending.
