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

This candidate has not yet been packaged or tested on hardware. The delivered
D0 degree package remains a separate, unchanged build.
