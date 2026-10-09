# Mattias bus: degrees, Kits and MIDI Scenes

Compatibility candidate using the latest native Part-owned DEG/CHRD implementation,
unchanged KITS from the DK handoff, and unchanged MIDI SCENES from upstream
[PR #647](https://github.com/sambanks/octabam/pull/647), commit `83a9d6c1`,
MIDISC2.1 submodule `52eaab0`.

Build: `BUILD=DS make bus REMIX=mattias-bus-degrees-scenes`.

Validation is in progress. This is not yet a test package or a hardware result.
Harmony publishes pending degree/chord identity before the native copy boundary
owned by MIDI SCENES. Both modules retain their own processing and continuations.

DEG scene roots transpose with KEY. CHRD remains a Part/pattern setting.
See the [compatibility contract and current evidence](../../modules/harmony-degrees/SCENES.md).
