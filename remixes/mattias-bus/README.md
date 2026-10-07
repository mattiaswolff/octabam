# mattias-bus

`mattias-bus` is a personal, bus-centred remix with a compact FX1 station
bank. It is pending validation for this specific selection; any completed
check for an earlier stock-FX1 selection does not apply.

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

## Deliberately excluded

- `SIDECHAIN_COMPRESSOR` cannot coexist with BusDelay or BusVerb: both designs
  claim the same DSP/shared-memory regions.
- Analog BD currently composes with stock DSP effects only, while this remix
  carries the bus DSP servers. Combining them requires new DSP composition
  work rather than a remix configuration change.
- Scale Quantizer, REPITCH and MUTE MODES: their required ColdFire code and
  menu tables do not fit alongside RLEN PLEN and this FX1 station bank.
- Octakit is omitted to keep this bus remix focused and preserve future
  flexibility for Analog BD work.

## Validation boundary

The source selection has not yet completed its local check for this exact
configuration. No real Octatrack, CompactFlash project, or firmware flash is
part of that check. Before any device use, back up the CompactFlash card and
follow the recovery process in `docs/guide/BUILDING.md`.
