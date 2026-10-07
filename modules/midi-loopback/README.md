# MIDI Loopback prototype

Experimental internal MIDI routing from sequencer M1 on channel 1 to the
normal MIDI receiver. It mirrors outgoing notes and CCs; the physical
output is retained. The receiver's audio channel assignments, CC receive
switch and note mapping still determine the result.

This is the first proof from the [design sketch](DESIGN.md), not the finished
per-track EXT / INT / BOTH feature. There is no panel control or saved setting.
The volatile `lb_enabled` byte defaults to zero; the emulator gate enables it
after project load. No hardware use or flash is claimed.

## Scope

The captured sources are the two stock sequenced note-on call sites and the
two sequenced CC send sites, with source track 0 and output channel 1.
Both note-off encodings are accepted at the stock expiry, retrigger/steal,
cleanup and stop sites, but only for notes previously admitted internally.
Turning the prototype OFF blocks new events while those releases continue.

CC numbers are not filtered: the fixture proves CC 46 for level, and the
stock handler decides the meaning of every admitted CC. No claim is made yet
for all audio CCs, live keys, CC LFOs, pitch bend, pressure, program changes,
other source tracks or channels, or Harmony/Follow/Scales integration.
Clock, transport and SysEx are never copied by this prototype.

Use a dedicated channel without external notes on the same channel/pitch.
Stock's incoming-note bookkeeping is shared by channel and note; separate
internal/external ownership at that receiver is not implemented. Project and
Part changes, changing receive channels while held, and automatic reset of
the enable switch on project load are also outside this prototype.

## Implementation

Two detours reach one ColdFire DRAM unit:

| Hook | Purpose |
|---|---|
| `0x40010bd0` | Inside `midi_send`, after its save frame and USB-MIDI's entry hook. Classify the original caller and source track; copy an eligible complete message; replay stock instructions and keep external output. |
| `0x40005558` | MIDI task receive loop. Alternate native and internal messages, then use the existing installed dispatch table and handlers. |

The input byte parser is untouched. A 256-entry ring stores complete messages;
the consumer copies each to a stable slot before releasing its ring entry.
One coalesced wake token wakes the MIDI task through its normal queue. The
token is consumed internally, never interpreted as MIDI. If that queue is
full, no extra token is posted; its pending work already keeps the task
runnable and the receive hook checks the internal queue between messages.

Admission stops new note-ons and CCs at 127 pending messages. Up to 128
additional releases fit for the 128 possible owned pitches on the one
channel. Whole-message drop and queue high-water counters expose overload.
Caller filtering excludes received-MIDI echo and audio parameter feedback;
it does not claim protection against every possible MIDI-triggered sequence
action or project-wide control cycle.

The unit uses the existing platform reserve, which takes approximately 10 MB
of sample memory when introducing the DRAM platform into a stock-only image.
The standalone unit occupies 1,812 bytes of code and state and needs no DSP
effect slot. Runtime symbol addresses depend on the remix;
always read them from that build's `out/platform/runtime/runtime.elf`.

## Verification

Measured under the emulator on 7 October 2026: the five project scenarios
(OFF, internal, UART reference, OFF while held, STOP while held) completed.
The internal run admitted and delivered three messages with zero drops:
T1 level became 70, note 84 was held then released, and the incoming held-note
count returned to zero. Its external MIDI event sequence matched OFF.

`make check REMIX=midi-loopback` passed all runnable checks. The generic
project/audio gate was skipped without `OT_PROJECT`; the explicit project
command below supplied the five loopback scenarios separately. USB
enumeration, MIDI receive, MIDI transmit and all five loopback project
scenarios also passed with the `midi-loopback-usb` remix. Those receipts live
under `out/midi-loopback-usb/`. These checks do not measure simultaneous USB load
and loopback timing.

The gate executes the built detours and runtime machine code, including the
stock MIDI sender, queue routines and receive handlers. It checks filtering,
OFF, release ownership, queue fairness, saturation, wraparound, register
preservation and unchanged UART output. Direct stock-handler calls are the
reference for level, held-note state, gate state and note count.

With a disposable project copy, the ColdFire port runs the real sequencer,
RTOS, MIDI dispatch and UART input. The fixture sends note 84, CC 46 value 70,
and the note's release. Internal delivery is compared with UART input and an
OFF baseline. Additional runs cover OFF during a note and STOP during an
indefinitely held note. Receipts and captures stay under `out/midi-loopback/`.

```sh
make bus REMIX=midi-loopback
.venv/bin/python tools/verify/verify_midi_loopback.py midi-loopback
.venv/bin/python tools/verify/verify_midi_loopback.py midi-loopback --project /path/to/source-project
make check REMIX=midi-loopback
```

The source project is only read; fixture changes are confined to `out/`.
The project gate checks ColdFire audio-control state, not rendered sound,
hardware playback, sample-accurate timing or electrical MIDI timing.

## Remaining work

Trace live and LFO producers, then decide how to retain source identity for
the full routing feature. Extend coverage to the rest of the receive surface
and the MIDI modules before implementing internal-only output, menus or
persistence. The existing receiver's response to simultaneous audio locks,
scenes and looped CCs still needs musical and timing tests.
