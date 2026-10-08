# Degree and chord defaults with KITS

Implementation work is isolated on `codex/features/harmony-degrees-kits`.
The packaged D0 degree candidate remains available as a control. The combined
candidate is not yet validated or packaged; keep the composition guard until
the storage and lifecycle contract below has passing evidence.

## Player contract

**Reconfirmed by the user on 9 October: greenfield, no backward compatibility.**
Remove legacy settings/companion migration paths; do not add compatibility
decoders or dual stores. Ordinary OFF/HARM musical conversion is current
behavior, not a migration. Invalid/corrupt new-format input still fails safely.
The degree task will remove `chord-migration.s`, its companion-load migration
call and the legacy-seven retained-header state. Shared Harmony ownership:
please remove its remaining `ch_legacy7_mask` reset and TYPE=3 legacy branch
as part of the sibling migration, so no stub or compatibility symbol remains.

Each Kit carries **both DEG and base CHRD**, per MIDI track. These are Part
defaults: a pattern step with no corresponding lock inherits its current
Part/Kit's value. Explicit DEG and CHRD locks stay with the pattern. DEG keeps
its identity across Kit/KEY changes while HARM remains active; crossing OFF
uses the explicit conversion contract below. For example, Kit A can use `1:3`
and MIN while Kit B uses `5:3` and DOM7; an unlocked step follows the loaded
Kit, while a locked degree/quality keeps that lock.

The user's latest direction supersedes the earlier scope: **all custom
musical settings that are not pattern data move to the Part / Kit.**

| Data | Owner |
| --- | --- |
| DEG default and base CHRD | Part / Kit, per MIDI track, with identical lifecycle rules |
| HARM, VOIC, SPRD, ROOT | Part / Kit, per MIDI track |
| Follow RFOL, register MODE, remembered fixed/relative OCT and TRIG/LIVE response | Part / Kit, per MIDI track |
| Native KEY, TRAN and ARP defaults | Already Part data; retain native ownership |
| Explicit DEG/CHRD locks, trigs and sequence timing | Pattern |
| Held keys, variation stack, emitted-note ownership, pending events, AUTO and Follow history | Runtime state, reconciled at transitions; never Kit settings |

Native project settings and UI navigation keep their native scope. OFF
continues to use stock NOTE/NOT2–4. A missing fresh degree uses `1:3`; a
missing fresh CHRD uses TRI. Existing valid native notes convert on entry.
Both defaults must survive save/load/reload, copy/paste/undo, clear, slot
reuse, project operations and retained-memory resume. No migration is required.

## Coordination

**Ownership split acknowledged and accepted by the degree task**, after
reading the sibling `mattias-bus-kits/remixes/mattias-bus/KITS-EXPERIMENT.md`
implementation coordination section on 8 October 2026:

- The sibling task owns the shared native Part field/access contract,
  ranges/defaults, dirty flags and CS1 handling; Follow and Harmony settings
  at offsets 3/5/12/13/15/16; and focused verification without and with KITS.
- This degree task owns base CHRD/DEG at offsets 18/19, pattern representation
  and HARM-boundary conversion, DEG/CHRD companions, and the combined degree
  candidate with its integration gates.
- Agree concrete shared access symbols and UI/playback/captured-event
  contexts before integrating callers. Each shared Harmony hook edit has one
  owner and is exchanged as a commit; worktrees are not edited concurrently.
- Reconcile newer Follow/project-settings, response and B5 ownership fixes
  before choosing the implementation base. The older KITS probe branch is
  evidence, not a sufficient current module baseline. Preserve the native
  load-return fix and keep KITS source unchanged.
- Publish commit IDs and exact checks. A combined pass requires the actual
  composed image, tested both without KITS and with KITS. No migration or
  KITS dependency is introduced. The user subsequently resolved the
  HARM-to-OFF decision: preserve the outgoing resolved root (C3 in the
  example below).

The shared Part-settings investigation is in
[the KITS task](codex://threads/01a11d18-e86b-7842-ba90-4a7ee55004db).
Its completed investigation recommends eight disabled MIDI SETUP fields per
track, with explicit native range declarations. This is a proposed layout,
not yet a migrated implementation:

| SETUP offset within each 36-byte MIDI track record | Proposed owner/content |
| --- | --- |
| 3 | Follow source |
| 5 | HARM |
| 12 | Follow register mode and response |
| 13 | Remembered fixed octave |
| 15 | Remembered relative octave |
| 16 | Packed VOIC, SPRD, ROOT |
| 18 | Base CHRD |
| 19 | Base DEG |

The shared rule is **native Part authority, with or without KITS**. No KITS
symbols, callbacks, library scans, separate Kit storage or KITS-specific
conversion path may be required by Follow, Harmony or DEG. KITS carries the
same native Part bytes. Implement ordinary Part lifecycle first, then verify
the identical behavior through KITS. Do not independently allocate fields or
introduce a competing settings store.

Recheck that task before implementing the shared layout and before composing
the combined image. Import its reviewed implementation or follow its accepted
contract; do not create a competing settings store.

### Shared ABI review and degree integration work

The degree task has reviewed and accepts the proposed `mp_ui_context`,
`mp_play_context`, `mp_read` and `mp_write` register ABI: context is
`bank*4+working Part`, all registers except d0/condition codes preserved.
The implementation in the sibling `midi-part-settings` worktree is still
uncommitted and has not been integrated here. We will consume the published
commit after its linked-code gate. Saved Parts are native copy destinations,
not writable UI contexts. DEG/CHRD setters use offsets 19/18 respectively.

The degree task owns `modules/harmony-degrees/*` and CHRD callers in
`chord-ui.s`, `locks.s`, `chord-sequence.s` and `play.s`; shared Harmony/Follow
setting edits remain sibling-owned. Keep `mh_set_native` available beneath
the existing `hd_set` dispatch when degrees are selected: the degree setter
will convert only the selected working Part and its affected patterns before
publishing the new HARM value. The sibling owns Harmony's public getters and
should document which explicit-context getters accompany UI/playback forms.

Pattern companion work is replacing per-track global mode/default arrays
with per-pattern/per-track representation and outgoing-scale provenance.
Part defaults will not be exported in that companion or included in its
native fingerprint. A generic native Part-copy boundary is being investigated
here for outgoing capture before a physical Part slot is replaced; this must
cover ordinary Part operations and callers such as KITS without referencing
KITS. This task owns any such degree-only native-copy detour; the shared
`part.s` access layer does not need to depend on degree code. The concrete
detour and evidence will be posted before integration.

The proposed Harmony getter convention has also been read and accepted:
`mh_get` and voicing/spread/root getters are UI forms, `mh_active` is playback,
and the corresponding `_at` entries take explicit context in d1. CHRD callers
here will select those deliberately; they will not substitute UI for playback.

The first production conversion component is `roots.c`/`roots.h`, with
generated ColdFire assembly and `verify_harmony_degree_roots.py`. Each
pattern/track owns 64 degrees, 64 native edit snapshots, representation,
outgoing scale and last Part context (131 bytes). Detaching a replaced Part
captures its final scale and invalidates the physical-slot association; it
does **not** convert inactive patterns merely because they name that slot.
Conversion occurs when a pattern next uses an explicit incoming context.
The initial component gate passes 84 scale/tonic combinations, 128 independent
pattern/track records, the same-slot C3 boundary, native edit/clear behavior,
15 rejected invalid publications, and C ABI preservation. Native hooks,
companion publication and the composed candidate are not yet integrated.

### Implementation checkpoint, 9 October

- Shared foundation `f4eb4876` imported here as `f42cc654`. Its exact Harmony
  manifest activation is present; the sibling still owns Follow activation
  and the HARM/Follow settings migration.
- `chord-part.s` now supplies `ch_base_get` (UI), `ch_base_play` (engine),
  `ch_base_at` (explicit) and `ch_base_set` (UI edit), using SETUP offset 18.
  CHRD UI/live fallback and pattern lock fallback consume those functions.
  The obsolete volatile `ch_base[8]` default store is removed. Held variation
  and release ownership remain runtime state. The native CTRL1 SETUP A range
  at `0x400d43a6` is 8; its stock default is already TRI (0).
- `BUILD=DP make bus REMIX=harmony-degrees` passes. On that image,
  `verify_chord_part.py` passes 512 Part/track writes, distinct UI/engine/
  explicit/pattern contexts, lock precedence, dirty/mirror restrictions,
  invalid values, ABI preservation and actual native Part initialization.
  `verify_chord_play.py` passes its 1,792 chord, 8,400 voicing, 22,680 ROOT
  combinations and held-key/default-display checks. This is linked-code
  evidence; pending-event inheritance and native persistence remain open.
- A degree-only generic Part-copy entry wrapper is implemented in
  `part-copy.s`, targeting stock memcpy `0x40020898`, replaying its six-byte
  prologue and returning to `0x4002089e`. The callback will restrict capture
  to actual working Parts. `verify_harmony_degree_part_copy.py` passes 24
  stock-versus-intercepted copies, including non-Part sizes, before-overwrite
  observation, register/stack/argument preservation and byte canaries. This
  wrapper is **not installed yet**; its root-provenance adapter is next.
  KITS source remains unchanged. Existing native Part Clear interception
  will capture before initialization as well.

**Shared review item before publication:** explicit-context getters now read
native Part bytes during playback. A native full-Part copy can replace HARM,
Follow and voicing at different byte positions while the engine interrupts
the copy. Capturing only a Part index does not make those settings coherent.
Please cover this in the sibling's ordinary Part lifecycle validation,
including Harmony/Follow without DEG. If the shared layer needs to own the
native memcpy-entry boundary for atomic publication, coordinate ownership
before installing it: the degree wrapper above is still uninstalled and can
instead supply only the outgoing-provenance callback. No KITS-only hook can
solve the standalone case.

**Replacement ownership update acknowledged:** the sibling's 9 October note
assigns native memcpy-entry and Part-initializer publication boundaries to
the shared layer, conditional on its bounded critical-section checks. This
task will leave `part-copy.s` uninstalled and supply `hd_part_before` instead:
register ABI d0 = outgoing Part address, all registers preserved, no return
value. Its C implementation will detach outgoing root provenance; it does
not write Part settings or inspect KITS. The callback must be ordered with
the copy so an engine interrupt cannot reattach a pattern to the old Part
between capture and replacement. A callback before the mask needs an explicit
guard against that race; otherwise include the bounded callback in publication
and measure it on the composed degree image. We will keep capture cheap and
leave scale/degree conversion out of the masked Part-copy operation.

**Snapshot follow-up read and accepted:** the shared transient outgoing SETUP
snapshot is the right boundary; DEG will use `mp_read_key` as well as `mp_read`
and will not reattach affected provenance during publication. Please expose
the affected working-Part mask alongside `mp_snapshot_bank` (four bits), and
call `hd_part_before` once per overlapped Part with its aligned native Part
address after snapshot publication. This also covers partial SETUP/track
copies and multi-Part copies. Detaching or blocking reattachment for unrelated
Parts in that bank would lose their still-valid outgoing KEY provenance if
they are edited later while inactive; the bank pointer alone is too broad.
The callback also detaches receivers whose playing Follow source uses an
affected Part. The copy/clear path can keep interrupts enabled around capture.
The proposed internal `MIDI PART STATE` support module is accepted; this task
will add the support key to its degree remix selections at integration.

### Part-owned core checkpoint, 9 October

The working degree core now uses a 131-byte pattern/track root record and
native offset 19 for every DEG default. No Part default remains in a companion,
retained header, or custom Part clipboard. New companion/NV identity is HDP2 /
HDN2; combined payload is 24,960 bytes. Component checks pass same-slot C3,
Follow-source replacement, explicit mode edits, native default authority and
15 corrupt-payload rejections. These are not composed-image results yet.

The `mp_snapshot_parts` contract is accepted and the degree guard is implemented
against that symbol. It suppresses reattachment only for affected contexts and
their Follow receivers. `hd_part_before` is implemented (d0 outgoing aligned
Part, all registers preserved); it also detaches queued sequence and physical
recording provenance. The shared hook remains the only copy/init entry owner.
Awaiting the published support/migration commit for composed validation.

The degree-owned native Part Save/Reload/Clear/paste detours and default-copy
repair are removed in the working changes: native Part bytes now carry DEG
and CHRD themselves. Pattern/track/step companion copy handling remains.
Pending roots and physical message conversions now use explicit captured Part
contexts rather than the old track-wide HARM value; their composed tests are
being updated. Please retain HAVE_DEGREES dispatch through `hd_set` when the
settings migration is published. No KITS source edits are needed here.

**Integration handoff request:** please publish the support-hook/migration
commit once its focused checks are ready, independently of the longer full
port run, so this task can link and exercise the new DEG callbacks. Current
component tests link the real shared access layer and isolate only transient
snapshot storage; that does not replace a composed native-copy gate.

**Shared port fixture ownership:** `verify_midi_harmony_port.py::fixture`
still creates `#MIDI_HARMONY_*` project comments, and its persistence cases
assert those comments. The DEG and CHORD PLAY full-port runners both consume
that helper. Please migrate that helper/persistence expectation in the shared
settings task, or publish an explicit handoff before we edit it here. The
DEG task is updating its own linked/file/publication/full-port schema checks.

### Shared migration imported and first composed checks

Shared `a76c3c6b` imported as `8fb92577`, after degree core checkpoint
`89bfac9a`. `MIDI PART STATE` is now the sole copy/init owner, the temporary
Harmony helper links are removed, and the no-KITS degree remix includes it.
DEG callback dispatch and the shared `mh_set` -> `hd_set` path are retained.

**Small shared fix available:** `4a1e0ab6` on the degree branch fixes the
no-Follow Scales build (`bra.s` with zero displacement at `ms_raw_ui`) and
makes the Harmony/no-Follow KEY editor read the UI Part instead of playback.
`verify_midi_scales.py` passes, including a new distinct-UI/engine regression.
Please import that bounded fix rather than duplicating it.

`BUILD=DP make bus REMIX=harmony-degrees` and native RTOS handoff pass.
The first composed linked gates pass DEG integration, 12 root-publication
cases (65 maximum edit masked instructions), file failures/default isolation,
CHRD Part/storage, and shared Part settings. Native copy ABI gate passes its
21 comparisons and nine interrupted copies after allowing the composed
callback's additional instructions. New `verify_harmony_degree_part_state.py`
passes three real interrupted copies (all eight tracks, four pending slots),
old C3 versus incoming defaults, no reattachment during the snapshot, and
native Clear preserving outgoing D3. These copies take 32,748–34,076 emulated
instructions, with at most 169 consecutive masked instructions. Full port
and final make-check receipts remain pending; no hardware timing claim.

**Scope audit for the shared task:** WIDTH is still a volatile eight-track
array and README calls it a temporary audition setting. The user's direction
is all non-pattern musical settings in Parts/Kits and production quality.
Please account for WIDTH in the shared setting scope, or point to an explicit
accepted exception; the degree task has not changed its storage/encoding.

## Composition baseline

- Degree implementation: D0 source `540a7ef9`.
- Harmony's native load-return fix: `97b69f2f` and its ancestors. Native
  caller identity and success/error continuation must remain intact.
- Upstream refreshed to `063a4262`: KITS has removed AUTOSAVE and KEEP LEVELS.
- KITS source and file format stay unchanged. MIDI SCENES is not selected.

## Storage investigation and implementation

1. Finalize one shared Part-settings layout and access layer from the linked
   investigation. Establish ranges, defaults, invalid-data handling and exact
   byte claims. Prove native preservation and stock MIDI control behavior.
   Do not use the disputed LFO-designer Part-window area.
2. Move Harmony and Follow settings to that layer. Read the relevant context:
   selected Part for UI, playing/staged bank and Part for sequencing, captured
   context for pending events. Follow must resolve the correct source context
   even when source and receiver tracks have not switched Parts together.
3. Store DEG and CHRD defaults in that same layer. Pattern companions retain
   explicit locks and the representation information needed for conversion;
   they must not overwrite defaults supplied by a newly loaded Kit.
4. Replace D0's global mode assumption. `HdBank.active[8]` and the global
   `hd_mode_c(track, mode)` cannot represent different HARM modes in different
   Parts. An explicit HARM edit changes the edited working Part and affected
   pattern roots, not unrelated Parts or library Kits. Kit recall restores the
   incoming Kit's own settings/defaults; it must not copy outgoing defaults
   into that Kit. Account for shared Parts, unsaved edits, nonresident Kits
   and per-pattern/per-track representation state.
5. Publish settings coherently at recall. Previously emitted notes retain
   their original track/pitch for release. Do not let an event observe new
   HARM with old Follow or voicing. Reset/reconcile runtime history explicitly
   without creating recorded trigs or saving held-note state into Kits.
6. Keep pattern companion validation independent of KITS' movable Part-slot
   assignments and default NOTE bytes. Changing a Kit must not invalidate
   unchanged DEG/CHRD locks. Use an explicit new format identity, without a
   compatibility decoder.
7. Only remove the KITS guard after the focused gates pass. Select the
   combination in a separate `mattias-bus-degrees-kits` remix.

The unbuilt draft that converted every library Kit on a global HARM change
has been set aside. It does not match Part-owned HARM.

### Mode-boundary behavior

- NOTE <-> CHORD preserves DEG.
- HARM -> HARM preserves degree locks; incoming KEY changes resolved pitches.
- HARM -> OFF converts explicit degree locks using the outgoing applicable
  scale, preserving their resolved root pitches before incoming settings
  replace that context. This applies to native Part changes and Kit recalls.
- OFF -> HARM converts native roots using the incoming applicable KEY.
- OFF -> OFF retains stock pitch processing.
- Unlocked steps always use the incoming Kit's own default in its own mode.

**Accepted user decision:** for an explicit `1:3` lock, Kit A is HARM CHORD,
C minor (C3), and Kit B is HARM OFF, D minor. Conversion commits **C3** to the
pattern's native NOTE using the outgoing context. Kit B's KEY does not change
that conversion to D3. Unlocked steps use Kit B's own NOTE default.

Capture the outgoing effective scale before a Part slot is overwritten or
reused. Preserve the resolved root, without baking in TRAN, voicing, spread
or ROOT output treatments. Previously emitted notes keep their original
release ownership. The incoming Part/Kit's own defaults remain its defaults.

### Storage probes completed here

These are bounded stock-firmware port probes, not full storage acceptance.
Scripts, UART captures, bank dumps and receipts are under
`out/kits-degree-audit/`. Stock MAIN_OS SHA-256:
`164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e`.

- **Rejected: MIDI page-1 offsets 30/31.** Although native initialization
  clears them, nonzero values enable extra pitch-bend, pressure and CC output.
  Notes matched; complete UART comparison exposed the difference.
- **NOTE SETUP D/F:** values below 128 survived stock load/play with identical
  complete UART for notes and arps. The composed image still has narrower
  RFOL/HARM ranges. SETUP E is native SBNK and cannot be used.
- **CTRL1 SETUP A/B, offsets 18/19:** values below 128 survived in all 64
  working/saved Part-track pairs. With native controller enable bytes set
  identically in both fixtures, complete UART matched for notes and arps
  (28 and 70 balanced note events). This is evidence, not a byte allocation.
- The linked task independently found zero-only range validation clears the
  four blank ARP SETUP fields unless those declared ranges are changed.

If native storage cannot be proved safe, retain the guard and revise the
shared Part design. Do not substitute a KITS-specific adapter, hide the gap
by removing the guard, or borrow a native control's value.

## Required evidence

- The modules work independently of KITS: native Part ownership, persistence
  and held-note transitions must pass without KITS and with it. Verify
  standalone Follow, standalone Harmony, Harmony with DEG, and the combined
  Follow/Scales/Harmony/DEG selection. KITS adds library lifecycle cases; it
  must not supply required settings behavior.
- Stock control versus populated candidate Part bytes: complete MIDI output,
  all normal note/arp/CC/LFO behavior used by the fixtures, and unrelated Part
  fields unchanged. Save/reload, Part copy/clear and current-bank retention.
- DEG and CHRD default editing, inheritance and explicit locks independently
  and together, including two Kits with identical native pitches but different
  degrees after a KEY change.
- KITS initial creation/import, load/save/quick-save/reload, undo, library
  copy/paste/clear, pattern assignment, playing/stopped staging, multiple banks,
  slot reuse and no-free-slot refusal. Use current upstream behavior.
- Different HARM/Follow/voicing per Kit; every OFF/NOTE/CHORD transition with
  resident and nonresident Kits; KEY changes; out-of-range degrees; queued
  triggers; held notes; arps; Follow TRIG/LIVE; UI selection differing from
  playback; source and receiver tracks switching Parts at different times.
  An ordinary edit/recall must preserve unrelated patterns, Parts and saved Kits.
- Explicit boundary regression, both without and with KITS: outgoing C-minor
  HARM `1:3`, incoming D-minor OFF -> native locked NOTE C3 (MIDI 48).
  Verify incoming default NOTE inheritance separately, including reuse of the
  same physical Part slot and queued events across the transition.
- Project Save/Reload/Save As/New, cold load, unsaved retained-memory resume,
  corrupt/mismatched payloads and failed writes. No partial publication or
  overwritten stored backup on a rejected save.
- Full selected-remix `make check` with an actual copied project and no hidden
  skips, dedicated combined port cases, source/toolchain/image provenance and
  independently decoded BIN/SYX package checks.
- Hardware acceptance remains a separate user test of that exact image.
