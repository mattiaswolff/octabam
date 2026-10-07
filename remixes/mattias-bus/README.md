# mattias-bus

`mattias-bus` is a personal, bus-centred remix with a compact FX1 station
bank. Source and emulator verification for this selection is recorded below;
physical hardware acceptance is still pending.

## Intended layout

| tracks | FX2 role | use |
|---|---|---|
| T1 | BusDelay | delay host and return; normally a trig-free THRU track |
| T2--T4 | SEND | dry track output plus per-track `DEL` and `REV` sends |
| T5 | BusVerb | reverb host and return; normally a trig-free THRU track |
| T6--T7 | SEND | dry track output plus per-track `DEL` and `REV` sends |
| T8 | stock DELAY | master track's existing delay / beat-repeat role |

The FX2 chooser is locked so the host assignments cannot be accidentally
changed on the unit. FX1 contains only `NONE`, Spectrum, Character and
Modulation. Spectrum replaces the stock Filter position, Character replaces
Lo-Fi, and Modulation replaces Chorus; other stock FX1 effects are not in
this firmware's FX1 chooser.

For an external A/B source, use a THRU track and its FX2 `SEND` controls to
set how much of the post-FX1 signal reaches the shared delay and reverb.  T1
and T5 can also be THRU tracks; their own `DEL` and `REV` controls send their
post-FX1 dry input to the shared engines.

## Included capabilities

- Shared BusDelay and BusVerb, with tempo-synchronised delay and the TEMPO
  window for engine controls.
- Spectrum (filter), Character (saturation/shape/compression), and
  Modulation (chorus/flanger/phaser/comb) as the FX1 station bank.
- Mode Defaults: changing a station or bus engine's mode also applies its
  matching useful parameter defaults.
- RLEN PLEN, to record one pattern-length pass with `TRIG ONE` and `QREC PLEN`.
- Tuner, opened with `UP + TEMPO`.
- MIDI Follow, MIDI Scales, and MIDI Harmony, including the Chord Play
  development extension. Chord Play is part of Harmony, not a fourth module.

## Deliberately excluded

- `SIDECHAIN_COMPRESSOR` cannot coexist with BusDelay or BusVerb: both designs
  claim the same DSP/shared-memory regions.
- Analog BD currently composes with stock DSP effects only, while this remix
  carries the bus DSP servers. Combining them requires new DSP composition
  work rather than a remix configuration change.
- Scale Quantizer, REPITCH, MUTE MODES, and KITS are not selected. The older
  remix's size and compatibility observations have not been remeasured on
  this upstream revision; omission is not a current incompatibility claim.

## Validation boundary

The selection has the source/emulator verification recorded below. No real
Octatrack, CompactFlash project, or firmware flash is part of this verification. Before any device use, back up the CompactFlash card
and follow the recovery process in `docs/guide/BUILDING.md`.

On 7 October 2026, the fork was organized on upstream `6f9e5bc9`. The three
standalone module images and the combined bus image built. Linked machine-code
gates passed for Follow, Scales, Harmony, Chord Play, and chord storage, both
in their applicable standalone selections and together in this remix. The
combined Chord Play gate covered all seven modes. Registry documentation,
test imports, and gate planning passed. Assembly sources were compared byte
for byte with the preserved development/checkpoint branches. These are
targeted development checks, not a full firmware or hardware acceptance run.

### Muted-source MIDI Follow, 7 October 2026

Follow now captures sequenced roots while the source is muted. The source's
MIDI output remains muted; followers keep their own independent mute state.
The firmware change removes only Follow's four-instruction mute check. No
new hook, stored setting, DSP code, or note-output path is introduced.

`make check REMIX=midi-follow` passed with a copied project. The combined
`make check REMIX=mattias-bus` completed its planned gates with targeted
retries after three local setup problems: an outdated shared DSP host lacked
`-pword`, the original mixer fixture lacked the bus hosts, and accumulated
virtual-card captures exhausted free disk space. An isolated matching DSP
host, a copied rig fixture with scenes/LFO modulation disabled, and removal
of this task's disposable card images resolved those problems. The corrected
project/TEMPO BUS tests and the complete MIDI Follow gate then passed against
the same combined image. The full command's earlier nonzero exit is retained
in the local validation receipt; it is not described as a single clean run.

The new UART suite passed 12 standalone and 28 combined cases: muted-start
sources, muted followers, mute/unmute with held notes, both track orders,
source arp, added scales, Harmony chords/arp and per-step chord choices.
All notes had balanced releases. The other combined gates, including Harmony,
Chord Play and storage, passed. Receipts and logs are in the integration
worktree's ignored `out/muted-source-delivery.json` and referenced files.
No flash package was made and no hardware was changed.

## Fork development

`origin` is `mattiaswolff/octabam`; `upstream` is `sambanks/octabam`.
Push development commits to `origin`. Pushing does not open a PR or change
upstream. Keep the fork's `main` aligned with upstream and develop in the
worktrees below. The original local `main` checkout is preserved at its old
revision; use these worktrees for new development.

Paths below are relative to the Octabam repository's `.claude/worktrees/`.

| Purpose | Branch | Worktree |
| --- | --- | --- |
| MIDI Follow | `codex/modules/midi-follow` | `fork-midi-follow` |
| MIDI Scales | `codex/modules/midi-scales` | `fork-midi-scales` |
| MIDI Harmony, including ROOT controls | `codex/modules/midi-harmony` | `fork-midi-harmony` |
| Chord Play extension of Harmony | `codex/features/chord-play` | `fork-chord-play` |
| Personal selection and combined testing | `codex/remix/mattias-bus` | `fork-mattias-bus` |
| Shared MIDI verification helpers and interactive capture | `codex/support/midi-verification` | `fork-midi-verification` |

The three module branches each contain only their own new firmware module.
They share the small verification-support base. Chord Play depends on the
Harmony branch. The remix integrates Follow, Scales, and Harmony with Chord
Play, plus the original bus selection. Minimal `midi-follow`, `midi-scales`,
and `midi-harmony` test remixes isolate the individual modules;
`midi-harmony-follow` combines them on stock effects to isolate the MIDI
work from the bus selection. Earlier `mattias-midi-*` test selections are
retained for existing verification scripts.

Make module fixes in their module worktree, commit and push there, then
merge those commits into this remix worktree. Harmony fixes also flow into
the Chord Play branch before that branch is integrated. Change the personal
selection here; do not bury module fixes here. Commit unfinished experiments
as explicit checkpoints rather than claiming they passed acceptance.

The old worktrees remain available, with their original uncommitted files.
The `codex/checkpoints/*-20261007` branches preserve the pre-organization
source and history in the fork. They are reference snapshots, not the new
development branches. Build outputs, supplied stock firmware, virtual CF
images, and local dependencies are not included in those source backups.

Fetch upstream at planned checkpoints, integrate it in a module worktree,
resolve conflicts, and rerun verification before propagating that version
into the remix. Do not rebase or change a worktree while another task is
using it. Do not rewrite a published hardware candidate's source reference.

The upstream guides assume that `origin` names upstream. In this fork setup,
pass the actual base explicitly, including test remixes:

```sh
git fetch upstream
make reach BASE=upstream/main TESTS=1
make reach BASE=upstream/main TESTS=1 RUN=1 KEEP=1
```

The first command after fetching only lists the gates; the second runs them.
`make reach` refuses a branch that does not contain the specified base.
Passing the plan alone is not verification. Check the parent branch of any
stacked contribution before opening a PR. Shared support can be reviewed
first; each module can then be reviewed separately. No PR is opened by this
workflow setup.

Build the emulator in each worktree with `make emu-cf`; never symlink
`out/emu`. The original local `.venv` and `vendor` links point to the preserved
`mattias-bus` worktree's tools. For muted-source validation, this integration
worktree uses a private vendor overlay with a matching `dsp_host`; its source,
binary and original vendor location are recorded in `out/mute-host/toolchain.json`. Do not remove that worktree or rebuild shared
tools from a different revision while another task is using them. A change
to toolchain patches or DSP host code requires an isolated, matching tool
build, as described in `AGENTS.md`.

## Hardware candidates

Use this worktree and `REMIX=mattias-bus` for combined hardware candidates.
The branch setup and an assembled image do not establish hardware readiness.

1. Commit the exact source and selection. Record the commit, upstream base,
   integrated module commits, and module list. Push the source to the fork.
2. Choose an unused `BUILD` number after checking `CHANGELOG.md` and the
   local hardware receipts. Run `make check REMIX=mattias-bus BUILD=N`, with
   the appropriate local project fixture, and the additional gates listed by
   `make reach`. Record failures and skipped checks explicitly. Verify that
   shared tool versions match this tree before trusting the results.
3. Only after the required checks pass, run
   `make image REMIX=mattias-bus BUILD=N` from the same clean commit. Keep the
   image, its SHA-256, commands, results, and source references together in a
   local candidate directory. Never commit or upload firmware images.
4. Give the candidate an immutable source tag after verification. Preserve
   the previous working image and project/card backup. Flash manually using
   the build guide, then record the actual device, displayed build, scenarios,
   and observations. Source/emulator checks are not hardware results.
5. Fix failures on the responsible feature branch, integrate the fix here,
   and prepare a new numbered candidate. Keep the earlier record unchanged.

Chord Play adds project companion files. Back up the whole project with its
companions, and review [Harmony's storage notes](../../modules/midi-harmony/README.md#chrd-storage-and-migration)
before testing save, reload, or migration. No existing card or hardware
project is modified by setting up these branches.
