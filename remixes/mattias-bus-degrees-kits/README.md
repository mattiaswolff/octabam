# Mattias bus: degrees and Kits

Production integration candidate combining the personal bus rig with
[Harmony degrees](../../modules/harmony-degrees/README.md) and
[KITS](../../modules/kits/README.md). All musical defaults are native Part
settings. Patterns retain explicit DEG and CHRD locks. The modules work
independently of KITS; the library carries ordinary native Parts.

Fresh DEG is `1:3` and CHRD is TRI. HARM-to-OFF conversion preserves the
outgoing root; an explicit C-minor `1:3` becomes native C3 even when the
incoming OFF Kit has D-minor KEY. Unlocked steps use the incoming Kit's own
default. No legacy degree or settings migration is provided.

Build with `BUILD=DK make bus REMIX=mattias-bus-degrees-kits`. Acceptance
requires the selected `make check` with `OT_PROJECT`, the degree firmware
lifecycle suite, native Part transition matrix and KITS library scenarios.
See [the coordination and evidence record](../../modules/harmony-degrees/KITS.md).

Prepare the shared KITS gate's project assumptions in a separate copy:

```sh
.venv/bin/python tools/verify/prepare_degree_kits_fixture.py --project /path/to/project --out out/degree-kits-fixture/new
OT_PROJECT="$PWD/out/degree-kits-fixture/new/project" make check-shared REMIXES=mattias-bus-degrees-kits BUILD=DK
OT_PROJECT=/path/to/audio-rig make check-remix REMIX=mattias-bus-degrees-kits BUILD=DK
```

The helper refuses an existing output directory and leaves the source project
untouched. Its receipt hashes every prepared project file. The musical recall
matrix uses `tools/verify/verify_harmony_degree_kits_port.py --project /path/to/project`
after building this remix; it freezes the image and symbols for all 18 cases.
The audio-rig fixture supplies BusDelay/BusVerb hosts, sends and sample routing
for the project and TEMPO BUS checks. These two targets are the shared and
per-remix halves of `make check`, with the appropriate fixture for each.

The DK firmware passes the degree lifecycle suite, all 18 Kit mode transitions
and the selected module gates. The MIDI-only fixture initially lacked TEMPO
BUS audio hosts; that check and the project gate pass on the original audio
rig, with the original failure and rerun retained in the receipts. Hardware
acceptance remains pending. The delivered D0 package is unchanged.
