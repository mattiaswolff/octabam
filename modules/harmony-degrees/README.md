# Harmony degrees

Production replacement candidate for MIDI Harmony's root model. It is selected
separately while acceptance is in progress; the ordinary MIDI HARMONY selection
must retain its existing behavior and bytes. This is not a reduced prototype.

## Musical contract

OFF uses native NOTE and NOT2–4. HARM NOTE and CHORD use one degree/register
value, displayed as `1:3` (degree 1, tonic octave 3). Degree 7 advances to
degree 1 of the next tonic octave. Thus `7:3` is B-flat3 in C minor but C4 in
D minor. Octave names follow the native display (MIDI 60 = C4).

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

HARM remains project-wide per MIDI track. A transition covers the working
data for that track across all banks and patterns, resolving each pattern's
assigned Part KEY (or ultimate Follow source's Part KEY). Stored Part snapshots
are kept coherent with their corresponding degree defaults. This is not a
current-pattern-only rewrite. Loading/copying/restoring data must reconcile its
representation before playback. Native dirty flags and retained mirrors must
be updated when converting into NOTE.

Native pitch consumers and generated note ownership receive real pitches.
Recording captures degree identity at the event, not a later queue-consumption
KEY. Releases retain their original track and emitted pitches. Pending events
cannot mix old representation data with a new mode. UI reads do not regenerate
AUTO voicing or mutate musical state.

Copy, paste, undo, clear, new trigs, new projects, bank load/store/reload,
Part save/reload/copy, Save As and battery retention carry the degree data
alongside their native counterparts. Corrupt or mismatched storage cannot
publish partially validated data. A rejected working save cannot overwrite
the stored bank/companion backup. Native bank and companion writes remain
separate filesystem operations; arbitrary power-loss atomicity is not claimed.
No legacy degree migration is required. The candidate uses its own companion
identity so it cannot masquerade as the current module's CHRD format.

The candidate supports native Parts. KITS and MIDI SCENES require their own
degree-aware storage/interpolation contracts; the composition ledger rejects
those combinations. The personal-bus candidate does not select either module.

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

The isolated candidate builds. These automated component checks have passed:

- Codec: 10,752 encode cases, 7,056 decode cases, 84 display values, fallback,
  invalid inputs and register preservation.
- Bank conversion: 16 banks / 256 patterns, 128 Part defaults, 16,384 root
  positions, inheritance, Follow source selection and current-bank mirrors;
  every unrelated native byte compared.
- Combined retention: all 24,720 payload bytes round-trip; 16 malformed or
  mismatched snapshots rejected before either live table is overwritten.
- Linked native hooks: staging/pending/fire, KEY change before firing,
  OFF/NOTE/CHORD conversion, degree editing, clipboard copies across modes,
  CS1 copies and Part default save/reload.

Full-firmware port checks have also exercised real panel editing, live recording,
project Save/Reload/Save To New, new projects, unsaved retained-memory resume,
native Part Save/Reload/Clear, track/pattern/bank copy and undo, rejected-file
recovery, and HARM/OFF boundaries during sequence arp playback. The selected
remix gates and final immutable-image suite must complete before packaging.
Hardware acceptance remains separate.

## Reproduce and accept

Build with `make bus REMIX=mattias-bus-degrees BUILD=D0`. The module's declared
image gates cover the codec, core, linked hooks and filesystem failure paths.
Run the complete carrier checks with `make check REMIX=mattias-bus-degrees
BUILD=D0`; use `OT_PROJECT` for the existing full-project/USB/concert gates.

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
image. The ordinary `mattias-bus` selection is the control and must remain
byte-identical to the branch's original base when this module is omitted.
