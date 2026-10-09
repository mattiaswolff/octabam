# MIDI CPU measurements

Opt-in instruction counts against the exact H3 image
`45516f678f793cf09b276db5fcd6adc58552019697ce10a8e279221a1f9163da`.
This is a before/after comparison of our implementation. It is not a stock
feature comparison, hardware CPU percentage, cycle count or latency estimate.

The linked firmware runs in the existing ColdFire Unicorn harness. Each case
runs twice from an identical fixture; instruction counts, maximum continuous
interrupt-masked spans and observable result hashes must repeat exactly.
Comparison also refuses changed result hashes. The tests for musical behavior,
corruption, reentrant publication, module combinations and full firmware remain
separate requirements; matching benchmark fixtures alone is not acceptance.

| Operation | H3 instructions | Optimized | Change |
|---|---:|---:|---:|
| Retain empty bank | 567,686 | 385,542 | -32.1% |
| Retain 8 explicit steps | 715,840 | 523,370 | -26.9% |
| Retain all 8,192 steps | 788,204 | 494,598 | -37.3% |
| AUTO voicing, four-chord progression | 9,159 | 7,261 | -20.7% |
| ROOT voicing, same progression | 2,860 | 2,684 | -6.2% |
| Scale KEY 84 quantization, all 128 pitches | 18,856 | 10,792 | -42.8% |
| C-major degree decoding, all 84 degrees | 6,573 | 3,621 | -44.9% |
| Degree encoding, all 128 C-major pitches | 15,446 | 15,574 | +0.83% |

The small encoding increase is one instruction per call to expose the
normalized scale index to the decoder. The common inherited tonic-root
tick/prepare fixture also adds one instruction per track (+0.17%/+0.18%).
This tradeoff is explicit: other degrees avoid scanning the scale mask.
Retained saves keep their 36-instruction maximum masked span; the bulk
packing and checksum run with interrupts enabled. Counts include callees.

Follow and shared Part-state code are measured by the same fixtures. With
eight tracks, the unchanged Follow TRIG steady tick is 1,104 instructions,
LIVE steady tick 2,024, longest routing-chain sweep 3,321, and eight Part
field reads 336. These measure these specific states, not global worst cases.

Implementation changes are bounded: immutable scale/mirror lookup tables,
four ten-bit packed tokens emitted as five bytes, and a chord sort that stops
once sorted and omits the already sorted tail. No live-state cache, persistence
format change, sparse capacity limit or additional retained SRAM is introduced.
The fixed 10,400-byte HDP3/HDN3 reservation and validation remain intact.
The linked runtime grows by 8,664 bytes including layout padding; runtime BSS
is unchanged. The main OS image grows by 564 bytes in the measured build.

## Repeat

Build the selected remix first. Preserve `mainos_bus.bin`,
`platform/layout.json`, `platform/runtime/runtime.elf` and
`platform/runtime/runtime.bin` under a baseline directory with that layout.
Then use the same benchmark source for both images:

```sh
.venv/bin/python tools/verify/benchmark_midi.py \
  --artifacts out/cpu/baseline --output out/cpu/before.json
make bus REMIX=mattias-bus BUILD=H5
.venv/bin/python tools/verify/benchmark_midi.py \
  --output out/cpu/after.json --compare out/cpu/before.json
```

The JSON includes image and benchmark-source hashes, per-case counts,
interrupt-masked spans, result hashes and the hottest instruction labels.
Benchmarking is deliberately outside ordinary `make check`.
