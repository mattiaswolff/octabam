# Degree and chord defaults with KITS

Implementation work is isolated on `codex/features/harmony-degrees-kits`.
The packaged D0 degree candidate remains available as a control. The combined
candidate is not yet validated or packaged; keep the composition guard until
the storage and lifecycle contract below has passing evidence.

## Player contract

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
- OFF -> HARM converts native roots using the incoming applicable KEY.
- OFF -> OFF retains stock pitch processing.
- Unlocked steps always use the incoming Kit's own default in its own mode.

**Pending user decision:** for an explicit `1:3` lock, Kit A is HARM CHORD,
C minor (C3), and Kit B is HARM OFF, D minor. The proposed rule is to preserve
the outgoing C3 when leaving HARM; the alternative writes D3 using the incoming
key. This question is pending, not an approved assumption. It affects pattern
root conversion, not replacement of the incoming Kit's defaults.

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
- Project Save/Reload/Save As/New, cold load, unsaved retained-memory resume,
  corrupt/mismatched payloads and failed writes. No partial publication or
  overwritten stored backup on a rejected save.
- Full selected-remix `make check` with an actual copied project and no hidden
  skips, dedicated combined port cases, source/toolchain/image provenance and
  independently decoded BIN/SYX package checks.
- Hardware acceptance remains a separate user test of that exact image.
