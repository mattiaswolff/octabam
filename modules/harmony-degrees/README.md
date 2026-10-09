# Harmony degrees

Production replacement for MIDI Harmony's root model, undergoing integration
and acceptance. Settings use native Parts, with the same behavior whether KITS
is selected or absent. This is a greenfield format with no migration path.

## Musical contract

OFF uses native NOTE and NOT2–4. HARM NOTE and CHORD use one degree/register
value, displayed as `1:3` (degree 1, tonic octave 3). Degree 7 advances to
degree 1 of the next tonic octave. Thus `7:3` is B-flat3 in C minor but C4 in
D minor. Octave names follow the native display (MIDI 60 = C4).

When a fresh or missing Harmony value requires a fallback, use `1:3`,
resolving to C3 under C major. Existing native notes are converted on entry;
the fallback does not replace them.

- OFF -> HARM converts absolute NOTE into degree/register using the applicable
  KEY. Nearest in-scale pitch wins; exact ties choose the lower pitch.
- NOTE <-> CHORD keeps the degree unchanged.
- KEY changes while HARM is active preserve degrees and change resolved pitches.
- HARM -> OFF writes resolved roots into native NOTE before native playback
  resumes. It preserves NOT2–4. It does not restore old absolute roots.
- A later OFF -> HARM uses the KEY at that later transition, establishing new
  degrees. KEY changes while OFF receive only stock processing.
- KEY OFF uses C major for degree conversion/resolution. Existing no-scale
  chord recipes remain unchanged (TRI makes major intervals on the root).
- TRAN/arranger offsets operate on resolved pitches, once. They are not baked
  into stored roots during conversion. Voicing, spread and ROOT are likewise
  output treatments, never inputs to representation conversion.
- Scale-derived CHRD choices adapt to the current scale. Explicit MAJ/MIN/DOM7
  preserve their interval recipes.
- A degree outside the MIDI range is silent in HARM. On conversion to OFF,
  which has no separate silent-root representation, it commits to the nearest
  MIDI boundary (0 or 127). It never wraps octaves or removes a root lock.

## Data and lifecycle contract

Native NOTE always remains a valid pitch or its native unlocked sentinel.
Harmony degree defaults and locks are separate data. Only the selected
representation is authoritative; conversion synchronizes at OFF/HARM boundaries.
Degree locks preserve native lock presence and Part-default inheritance.
Edits publish each root and its native snapshot together under a short
interrupt mask. Recording uses the same boundary; bank retention runs after
interrupts are restored. Clearing a HARM root removes its native mirror with
the degree so an intervening reader cannot reconstruct the deleted value.

HARM, Follow, voicing, DEG and CHRD defaults belong to each native Part.
Explicit DEG/CHRD locks stay with their patterns. An explicit HARM edit converts
the edited Part's default and its attached pattern roots. Recall inherits the
incoming Part's defaults. HARM-to-OFF locks preserve the outgoing scale's root;
for example, C-minor 1:3 becomes native C3 even when the incoming OFF Part has
D-minor KEY. A transient outgoing snapshot protects replacement of the same
physical slot. Inactive patterns retain their last scale until next used.

Native Part Save/Reload/copy/clear carries defaults directly. The companion
contains only 128 pattern/track root records: 64 degrees, 64 native edit
snapshots, representation, outgoing scale and context. Reusable slot context
is detached on load and before replacement. Part assignment and defaults are
excluded from the native pattern fingerprint. Dirty flags and retained mirrors
follow native bank ownership.

Native pitch consumers and generated note ownership receive real pitches.
Recording captures degree identity at the event, not a later queue-consumption
KEY. Releases retain their original track and emitted pitches. Pending events
cannot mix old representation data with a new mode. UI reads do not regenerate
AUTO voicing. The UI queue boundary reconciles the selected pattern even when
stopped; no trig is required for an OFF/HARM mode boundary.

Copy, paste, undo, clear, new trigs, new projects, bank load/store/reload,
Part save/reload/copy, Save As and battery retention carry the degree data
alongside their native counterparts. Corrupt or mismatched storage cannot
publish partially validated data. A rejected working save cannot overwrite
the stored bank/companion backup. Native bank and companion writes remain
separate filesystem operations; arbitrary power-loss atomicity is not claimed.
No legacy degree migration is required. The candidate uses its own companion
identity so it cannot masquerade as the current module's CHRD format.

KITS uses the same native Part fields and requires no special adapter. The
combined KITS selection is `mattias-bus-degrees-kits`. The additional
`mattias-bus-degrees-scenes` candidate adds DEG-aware MIDI Scenes; its
[compatibility checks](SCENES.md) are in progress.
See [the integration plan and ownership record](KITS.md).

## Implementation and evidence plan

1. Isolated feature branch, opt-in module selection, standalone and personal-bus
   candidate remixes. No integration into the current module branch or release.
2. Shared degree codec with exhaustive MIDI-range/key/mode round trips and
   explicit octave/bounds/tie tests against an independent reference.
3. Degree defaults/locks and transition engine, including bank/Part scope,
   native copies, dirty state and consistent transition publication.
4. Recording, live/grid editing, display, Follow and pending playback integration.
5. Durable companion/retention storage and complete native edit lifecycle.
6. Linked machine-code checks, actual panel/record/play/save port scenarios,
   stock-OFF comparisons and combined sustained-note/Follow/arp stress.
7. Required remix gates, clean source commit, immutable local package with
   hashes, provenance, validation receipts and an on-device acceptance guide.
   No hardware acceptance is claimed before the user tests that exact image.

## Required musical acceptance

| Action | Expected |
| --- | --- |
| HARM TRI, C minor, degrees 1-4-5 | Cm-Fm-Gm |
| Change KEY to D minor | Dm-Gm-Am, same degrees |
| Return to C minor | Exact original roots |
| HARM NOTE -> CHORD | Same resolved root; chord added |
| HARM D minor 1:3 -> OFF | Native D3, unchanged NOT2–4 |
| OFF D3, change KEY to C major, enable HARM | 2:3, resolving to D3 |
| Explicit MIN versus TRI on changing minor to major | MIN stays minor; TRI adapts |
| Degree 7 / tonic octave rollover | No accidental octave jump |
| Out-of-scale entry | Nearest valid pitch; lower on ties |
| KEY OFF | C-major degree mapping; no-scale chord recipe |
| Nonzero TRAN, arranger, ROOT and voicing | No duplicate/baked transposition |
| Switch mode with held notes/arp/pending triggers | Balanced note ownership |
| Followers before/after source in track order | Same resolved source root |
| Multiple banks/Parts with different KEYs | Each converts with its own context |
| Unlocked roots and explicit root locks | Default inheritance preserved |
| Edit/copy/undo/clear and persistence operations | No stale degrees or wrong root |

## Current evidence

The Part-owned core passes 16-bank native-byte comparisons, same-slot outgoing
C3, rapid stopped recall, Follow chains/cycles, queued sequence/recording
provenance, snapshot reattachment guards and 15 corrupt retained payloads.
The payload is 24,960 bytes (CHRD plus pattern roots), with HDP2 file and HDN2
retained identities. No default is restored from a companion.

Codec/root checks cover all 84 scales and 7,056 scale/degree combinations.
CHRD native defaults and pending inheritance have linked-code checks. Full
firmware checks pass native Part transitions across all nine mode pairs,
independent incoming defaults, degree/CHRD recording, save, cold reload and
retained resume. The composed hooks, interrupted native copy/clear, file
failure paths and bounded publication checks pass. The combined KITS image
passes all nine degree firmware groups and 18 resident/nonresident Kit mode
pairs, including held-key releases, explicit locks and incoming defaults.
Earlier D0 receipts belong to the preserved D0 image and do not validate these
new Part-owned changes. Hardware acceptance remains separate.

## Reproduce and accept

Build with `make bus REMIX=mattias-bus-degrees BUILD=DP`. The module's declared
image gates cover the codec, core, linked hooks and filesystem failure paths.
An interrupt-publication gate checks old-or-new root visibility, recorded KEY
identity, clear behavior, mask restoration and unmasked retention copying.
Run the complete carrier checks with `make check REMIX=mattias-bus-degrees
BUILD=DP`; use `OT_PROJECT` for the existing full-project/USB/concert gates.

Run the dedicated panel/files/playback suite with:

```sh
.venv/bin/python tools/verify/verify_harmony_degree_port.py --project /path/to/local/project
```

The project is copied into disposable fixtures; the source is only read. The
verifier freezes the firmware and linked symbols together, writes a receipt
per completed case, and removes regenerable virtual cards between cases.
`--frozen` resumes against that same image; `--case` selects one case group.
`--keep-fixtures` retains disposable cards for debugging. Do not run two copies
of this verifier in one worktree: they share its evidence directory.

C sources are authoritative; `python3 modules/harmony-degrees/generate.py`
regenerates their checked-in ColdFire assembly. `--check` refuses stale output.
No runtime C library or new firmware build dependency is introduced.

Follow the [hardware acceptance sequence](ACCEPTANCE.md) for the exact packaged
image. Stock-OFF output and native Part behavior must be checked on the exact image,
both with and without KITS.
