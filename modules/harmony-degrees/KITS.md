# Harmony degrees and native Part settings

Production implementation on `codex/features/harmony-degrees-kits`.
The user confirmed this is greenfield: no backward compatibility, migration
reader or duplicate settings store. D0 remains an unchanged separate package.
The new combined candidate is `mattias-bus-degrees-kits`, build DK. Its final
checks are running; it is not yet packaged or hardware accepted.

## Musical contract

- HARM NOTE and CHORD store DEG as degree plus tonic octave (`1:3`). Fresh
  DEG is 35 = `1:3`; fresh CHRD is TRI. Existing native notes convert on entry.
- KEY changes within Harmony preserve DEG. NOTE <-> CHORD preserves DEG.
- Explicit OFF -> HARM converts native NOTE using the effective incoming KEY,
  nearest in-scale pitch with lower ties. KEY OFF falls back to C major.
- Explicit HARM -> OFF writes the outgoing resolved root to native NOTE,
  excluding TRAN, voicing, spread and ROOT. OFF retains stock processing.
- A Part/Kit recall supplies its own unlocked NOTE, DEG and CHRD defaults.
  Explicit DEG/CHRD locks stay with the pattern. Incoming defaults are never
  overwritten by the outgoing Part's conversion.
- Accepted boundary: explicit `1:3`, outgoing C-minor CHORD, incoming D-minor
  OFF -> stored native **C3**, not D3. A subsequent OFF -> HARM establishes a
  new degree using the then-current scale.
- Out-of-range degrees are silent in HARM; OFF conversion clamps to MIDI
  0/127 without deleting the lock. Native NOTE/NOT2-4 remain valid stock data.
- Held keys, variations, emitted-note ownership, pending events, AUTO and
  Follow history are runtime state. Releases retain the original track/pitch.

All custom musical defaults are native Part settings, with or without KITS.
The user's latest correction removes WIDTH, FULL and SOFT entirely. SPRD
alone offers CLOSE/OPEN/WIDE with the former FULL spacing; E/F are inactive
in the Harmony window. No stored WIDTH bit remains.

## Implementation coordination and ownership

The degree task acknowledges the split in the sibling
`mattias-bus-kits/remixes/mattias-bus/KITS-EXPERIMENT.md`. Continue reading
that file periodically; do not edit sibling worktrees concurrently.

- **Shared task:** MIDI PART STATE access/ranges/dirty/CS1 and native copy/init
  boundaries; Harmony HARM/VOIC/SPRD/ROOT; Follow source/mode/octaves/response;
  shared port fixtures and standalone validation.
- **Degree task:** native CHRD/DEG defaults, CHRD callers, pattern roots and
  boundary conversion, companions/retention, degree tests and final combined
  candidate/package.
- Shared Harmony changes are exchanged as bounded commits. No KITS symbols,
  library scans, private Kit storage or KITS-specific conversion adapter.
  KITS source and format stay unchanged. MIDI SCENES remains incompatible.

The linked [shared task](codex://threads/01a11d18-e86b-7842-ba90-4a7ee55004db)
has no callable messaging API in this session. Coordination uses these files.

## Current native storage and ABI

Each MIDI track has a native 36-byte SETUP record at Part offset `0x4e2`.

| Offset | Contents |
| --- | --- |
| 3 | Follow source |
| 5 | HARM OFF/NOTE/CHORD |
| 12 | Follow mode/response, bits 0/1 only |
| 13 | Remembered fixed octave |
| 15 | Remembered relative octave |
| 16 | Packed VOIC/SPRD/ROOT |
| 17 | Native KEY, read through the shared snapshot |
| 18 | Base CHRD, 0..7 |
| 19 | Base DEG, 0..83; default 35 |

Context is `bank*4+workingPart`, 0..63. Public shared entries preserve all
registers except d0/CCR. `mp_ui_context` identifies the selected Part;
`mp_play_context(d0=track)` identifies the per-track engine context, with
applied-engine fallback, never UI fallback. `mp_read`, `mp_write`,
`mp_read_key` and `mp_epoch` use explicit contexts. Getters distinguish UI,
playback and captured-event contexts deliberately.

MIDI PART STATE owns boot-safe ROM gates for native memcpy/init. During an
ordinary native working-Part replacement it publishes `mp_snapshot_bank`,
`mp_snapshot_parts` and the outgoing SETUP snapshot, then calls
`hd_part_before(d0=aligned Part address)` once per affected Part. DEG detaches
outgoing root/queued provenance and suppresses reattachment while the snapshot
is active, including Follow dependencies. Native bulk copying remains
interruptible. A short final publication updates epochs and releases the
snapshot. Unrelated Parts stay attached. The superseded degree-only copy
wrapper and its unused verifier have been removed.

Pattern roots are 131-byte records: 64 degrees, 64 native edit snapshots,
representation, outgoing scale and last context. One bank is 16,768 bytes;
CHRD plus roots is 24,960 bytes. Files use HDP2/version 2; retention uses
HDN2/version 2. Non-DEG CHRD uses CHD2/CHN2. Empty files use HDP0/CHD0.
Companions contain no Part defaults and ignore Part assignments/defaults in
their native fingerprint. Loads detach reusable physical-slot provenance.
Strict validation, failed-write protection and atomic publication remain.

## Published integration checkpoints

| Shared commit | Imported here | Purpose |
| --- | --- | --- |
| `f4eb4876` | `f42cc654` | Shared native access foundation |
| `35644f79` | `fba982b1` | Shared replacement foundation |
| `a76c3c6b` | `8fb92577` | Native settings and boot-safe copy ownership |
| `16781d86` | `068664a6` | Native port fixtures and Part lifecycle |
| `5812a970` | `62fbb415` | Greenfield docs and fresh-project assertions |
| `afca19f1` | `b55b3011` | Native KEY gesture without Scales |
| `601e4b21` | `95af7d31` | Remove WIDTH entirely; SPRD only |
| `6545a434` | `c2d9c679` | Correct anchored OPEN page oracle |
| `49c6e603` | `336a639a` | Native Follow safety fixtures and architecture |
| `76c76f87` | imported | Completed shared lifecycle validation docs |

Earlier WIDTH persistence `bc05b081`/`a386f381` is superseded by the removal.

Degree checkpoints useful to the shared owner:

- `de5d501f`: plain physical keys and queued recording resolve native CHRD;
  CHORD PLAY keeps its latched variation. Already imported by the shared task.
- `49afff78`: first-use lane conversion before the recorder's atomic root
  publication; includes `InterruptMaskTrace` for accurate mask observation.
- `763d9f19`: grid input uses native CHRD even beneath the CHORD PLAY layout;
  32 physical/queued cases pass. Also removes the unused degree copy prototype.
- `ab004551`: CHD2/CHD0 identities in the full recorder port gate; shared task
  imported it as `123da88f`.
- `00ac7490`: degree KEY decoding respects whether MIDI SCALES is selected.
- `0c7ca715`: native degree Part matrix and new-format lifecycle fixtures.
- `cecd0629`: dedicated KITS composition; no KITS implementation change.
- `462b6153`, `1aa1038b`: registry expectations and named Part-state boot
  data comparisons; already imported by the shared task.

Harness finding: reading Unicorn SR on every instruction can alter a lazy
CMP/BNE result. A cold degree conversion loops only with that observer, and
passes without it. `InterruptMaskTrace` decodes actual SR writes and rejects
unknown writers; degree publication/copy gates use it. Normal boundary SR
checks remain valid. No emulator-source change was made.

## Evidence and remaining gates

Current evidence is under `out/kits-degree-audit/` and the dedicated verifier
output directories. Source, linked execution, full firmware, package decoding
and physical hardware are separate evidence stages.

Passed without KITS:

- Shared native field/ABI, defaults/CS1 and interrupted copy/init gates.
- 16-bank root comparisons, 256 raw KEY values with/without Scales, Follow
  chains/cycles, detached outgoing scale, rapid stopped recalls and queued
  recording/sequence boundaries. Fifteen corrupt retained payloads reject.
- All nine native Part OFF/NOTE/CHORD transitions through native Part Select,
  explicit roots versus incoming defaults, unchanged unrelated Parts and C3.
- Recording, project SAVE, cold load, CS1 resume, physical DEG editing,
  pattern/track/bank copy, clear/undo, native trig deletion/replacement, and
  native Part Save/Reload/Clear. All nine no-KITS firmware groups pass, including project reload/Save As/
  New Project, corrupt companions, Follow, stock-OFF UART and active arp modes.
- Plain-key recording: 15 performed/replayed voicing/spread/ROOT cases and
  four explicit-empty NOT2-4 cases. CHORD PLAY linked shape/ownership gates.
- Ordinary root edits mask at most 65 instructions. Dense first recording
  masks at most 1,377 (previously 13,755); composed Part copy with Follow at
  most 247. These are emulator counts, not hardware latency measurements.

Combined evidence:

- Build and focused KITS load/save/quick-save, library copy/clear, pattern
  assignment/undo, project SAVE/reboot/retained resume pass.
- All 18 resident/nonresident OFF/NOTE/CHORD mode pairs pass on a frozen
  SPRD-only image, including C3 into OFF, held physical keys, explicit DEG
  and MAJ locks, incoming defaults, unchanged library and drained ownership.
- The first full KITS gate exposed five test-project assumptions: receive
  clock/transport/program settings, saturated LEVEL, the first empty pattern,
  and an out-of-scale raw note normalized by degree paste. All five pass with
  the copied fixture calibrated explicitly. The clean full rerun passes with zero failures (optional legacy-import and
  external corrupt-bank fixtures unavailable). `--only` also reads stale
  unselected results in the KITS verifier; keep those outputs isolated.
- Final combined SPRD/grid-corrected image is frozen as SHA-256
  `11e01381100f93436115c745dd35e484484a8be2a27cf1536bbef59a9a29b748`.
  All 18 musical Kit recalls have passed on that exact image. The complete
  all nine degree firmware groups also pass on that exact image.
- Final-source per-remix checks for no-KITS `mattias-bus-degrees` and no-Follow
  `harmony-degrees` run in isolated `out/degree-check-shards` worktrees.

The combined per-remix TEMPO BUS gate needs the real audio rig fixture: the
MIDI fixture deliberately clears FX hosts/samples. Project/TEMPO BUS now pass
against the audio rig, including send/return audio and CC delivery; both logs
are retained. The preparation helper is for the
shared KITS half; README gives the two `make check` component commands. No
firmware change was needed for these fixture issues. Emulator CI: all five
unit tests pass.

Shared Follow safety fixture/native architecture cleanup `49c6e603` is now
imported. Seven transition pairs and the 20-second Follow-on soak pass on the
shared carrier. OFF soak and the shared KITS per-remix check also pass; the
latter has 17 image gates and no skips. Its
SPRD-only panel, 172,800 AUTO transitions, native Part lifecycle on Follow,
Harmony and the KITS carrier, project persistence and stock-OFF UART pass.

Before package: finish all running checks, resolve failures, complete combined
pending/arp/Follow and project lifecycle coverage, reconcile shared followups,
freeze clean source/image provenance, build and independently decode BIN/SYX,
and package the new candidate with receipts. Upstream was refreshed on
9 October and is already contained (`063a4262`). No card copy, OS upgrade or
hardware acceptance is authorized or claimed by these checks.
