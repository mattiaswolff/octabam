# Mattias's fork and package workflow

`origin` is `mattiaswolff/octabam`; `upstream` is `sambanks/octabam`.
This fork keeps upstream source, module development, contribution review and
the complete app separate. A package always builds from **one checkout**;
`mattias-bottleservice` selects the modules in that checkout.

## Branches

| Branch | Role |
|---|---|
| `main` | Exact upstream mirror, advanced by fast-forward only. No personal changes. |
| `codex/remix/integrated` | Permanent source of the complete, validated app. |
| `codex/modules/midi-scales` | MIDI Scales development. |
| `codex/modules/midi-follow` | MIDI Follow development. |
| `codex/modules/midi-harmony` | Harmony, degree roots, SIZE and direct CHORD PLAY development. |
| `codex/modules/plocks-p2-compression` | Full-capacity compressed PLOCKS P2 development. |
| `codex/modules/midi-part-state`, `codex/modules/midi-sram`, `codex/modules/harmony-plocks` | Shared MIDI integration modules. |
| `codex/support/store-clients`, `codex/support/midi-test-support`, `codex/support/sram-ledger` | Shared infrastructure development. |
| `codex/pr/*` | Focused review snapshots; extract/rebase the intended change against its declared base before opening a PR. |
| `octabam82`, subsequent `octabam<N>` tags | Immutable source used for each validated package. |
| `codex/checkpoints/*` | Preserved history, not active package inputs. |

Module branches include their prerequisites and may have an older upstream
base than the integrated app. They are not independent package ingredients
and are not automatically merged merely because somebody commits to them.
The four original module branches were refreshed with the exact prepared
contribution trees; their old heads remain merge ancestors and checkpoints.
Their module directories match OCTABAM82. The integration branch records
those baselines so future approved module changes can merge normally.

Older `codex/features/*`, `codex/upstream/*`, dated release/remix branches,
`harmony-default-degree` and `midi-follow-project-settings` are historical
work. Their maintained functionality is consolidated above. MIDI Loopback
remains outside this app. Strum stays removed; PAGE uses the native handler.

## Recurring upstream update

1. Fetch both remotes. Verify the URLs and preserve unrelated working changes.
   Advance `origin/main` to `upstream/main` with a normal fast-forward push.
   Update local `main` only if it is not checked out elsewhere. A divergence
   requires investigation, never a force-push. The original shared checkout
   was preserved on `codex/checkpoints/local-main-20261012`; work in a worktree.
2. Compare `upstream/main` with the integrated branch and latest release
   receipt. If already incorporated and no package is pending, do nothing.
   Resume an unfinished candidate before creating another.
3. Prepare a temporary candidate worktree from `origin/codex/remix/integrated`
   and merge `origin/main`. Resolve integration in the shared facilities and
   bridges; preserve upstream KITS/MIDI SCENES ownership and full capacities.
   Do not add unrequested module-development commits or features.
4. Build and validate below. Fix ordinary integration failures within scope.
   For unresolved conflicts, regressions or changes requiring a new contract,
   retain the candidate and evidence and report the blocker. Keep the published
   integration branch and release tags at their last validated commits.
5. Once gates pass, fast-forward and push `codex/remix/integrated`, then create
   and push `octabam<N>` for the exact source. Check remote heads before pushing;
   if another writer advanced them, integrate and validate the new state first.
   Tags and existing packages are never moved or overwritten.

The scheduled task reports a new package, failure or decision needed, and is
quiet when nothing changed. It builds locally; it does not copy to the card,
install firmware, open PRs, or upload firmware bytes to GitHub.

## Build and validation recipe

Read [BUILDING.md](BUILDING.md) and the repository working rules. Use the
worktree's own emulator and current toolchain patches. Never symlink `out/emu`.
Choose the next unused build number from both release tags and local artifacts.
Set `BUILD=<N>`, `OCTABAM_PGO=0` and `PYTHONUNBUFFERED=1` for the whole run.
Commit the candidate source before validation and record its full SHA.

Prepare a fresh fixture root from an existing local Octatrack project. The
helper copies the source, normalizes mixer/UI state, creates a hosted THRU
rig and supplies the exact Part assignment used by the MIDI Scenes gate:

```sh
.venv/bin/python3 tools/verify/prepare_mattias_fixture.py SOURCE_PROJECT out/release-fixtures
make check-shared REMIXES=mattias-bottleservice
.venv/bin/python3 tools/verify/check_shards.py --jobs 3 --no-cache mattias-bottleservice
make image REMIX=mattias-bottleservice BUILD="$BUILD"
```

Capture every command, exit status and log. Shared tests can overwrite the
root image; the `make image` above restores the exact selected package before
the focused runs. Freeze its MAIN OS hash and symbols. Run the following
tools with `.venv/bin/python3 tools/verify/<tool>`; fixture paths below are
relative to `out/release-fixtures`. All project writes target disposable copies.

| Tool | Arguments |
|---|---|
| `verify_midi_boot.py` | none |
| `verify_integrated_retention_port.py` | `--project BASE` |
| `verify_harmony_degree_kits_port.py` | `--project BASE --scenes --size-four` |
| `verify_harmony_size_scenes_port.py` | `--project BASE` |
| `verify_midi_concert_port.py` | `--project BASE` |
| `verify_harmony_degree_port.py` | `--project BASE` |
| `verify_scenesp2.py` | `mattias-bottleservice --project BASE` |
| `verify_plocksp2.py` | `mattias-bottleservice --project BASE` |
| `verify_set.py` | `mattias-bottleservice --project HOSTED` |
| `verify_modedefaults.py` | `mattias-bottleservice --project HOSTED` |
| `verify_tempobus.py` | `mattias-bottleservice` (uses the preceding staged set) |
| `verify_fx2lock.py` | `mattias-bottleservice --project HOSTED` |
| `verify_scenes.py` | `mattias-bottleservice --project MIDI_SCENES --persist --jobs 2` |
| `verify_reserve_writes.py` | `mattias-bottleservice --project out/integrated-retention/dense/project` |

`BASE`, `HOSTED`, `MIDI_SCENES` mean `out/release-fixtures/base`,
`out/release-fixtures/hosted`, `out/release-fixtures/midi-scenes` respectively.
Do not weaken assertions to accommodate inherited fixture settings. Record
all skips: the full upstream KITS suite needs additional author-specific
fixtures, and the focused recall tests do not replace all of that coverage.
For upstream PRs, follow the separate `make reach BASE=upstream/main` contract.

## Package and evidence

Rebuild with `make image` after the gates and require the resulting MAIN OS
hash to equal every focused run's frozen image hash. If source or test inputs
change, rerun the affected checks; never reuse results based on a branch name.
OCTABAM82's local `release.json` and `evidence/` are the initial receipt example.

Save each release under the parent workspace's ignored
`artifacts/firmware/OCTABAM<N>/`, with its BIN, SYX, RMX, README, source/upstream
SHAs, module selection, command results, coverage gaps and SHA-256 manifest.
Decode the BIN and verify its length-prefixed ELEK payload and checksum.
Validate SYX checksums and extract section 3 with the firmware tool; require
that section and the RMX to equal the tested MAIN OS. ZIP the package and
verify its CRCs and every archived file against the manifest. Keep firmware,
stock inputs, virtual cards and generated binary dumps out of Git.

Report deterministic linked-code and full-firmware emulator results separately
from inference and physical-device acceptance. The first-power-on logo hang
is unresolved; no USB-readable on-device boot log is implemented. A passing
package is not evidence of a physical boot fix or a device installation.
