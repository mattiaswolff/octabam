# Mattias bus with Harmony degrees

Separate hardware-validation candidate for the
[Harmony degree replacement](../../modules/midi-harmony/degrees/README.md), using
the same audio effects and MIDI modules as [mattias-bus](../mattias-bus/README.md).

This selection is a production implementation candidate, not a reduced prototype.
It is not merged into the current module or release. D0 is the separately
packaged hardware-validation candidate; hardware acceptance remains open.
Use a complete copy of a project for acceptance. Existing CHRD companions are
not imported; this selection writes its own `hdegNN.work` / `hdegNN.strd` files.

The local package contains BIN/SYX images, SHA-256 checksums, source and toolchain
provenance, validation logs/receipts, and the [hardware acceptance sequence](../../modules/midi-harmony/degrees/ACCEPTANCE.md).
Build with `make image REMIX=mattias-bus-degrees BUILD=D0 SYX=/path/to/stock.syx`.
The source tag is `mattias-bus-degrees-D0`; firmware artifacts remain local.
