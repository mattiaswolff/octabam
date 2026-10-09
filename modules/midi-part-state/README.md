# MIDI Part state

Shared support for MIDI Follow and MIDI Harmony. Include `MIDI PART STATE`
with either module; the repository's remix selections already do so. It adds
no panel control and does not require KITS. One owner supplies the
native hooks whether Follow, Harmony or both are selected.

Working native Parts are the authority. UI access uses the selected working
Part; engine access uses the playing context of each MIDI track. Custom writes
update native working bytes, the current-bank CS1 mirror and native dirty bits.
Native Save/Reload and KITS carry these bytes through their existing storage.
There is no legacy decoder, migration store or persistent shadow copy.

Small ROM entry gates preserve stock behavior before the platform runtime is
loaded. The native call immediately after the verified loader enables their
DRAM targets, preserving the stock callee's original return address.

While native memcpy or Part initialization replaces a resident bank's working
Parts, readers see a complete outgoing snapshot of all four MIDI SETUP arrays
(1,152 bytes). The single native UI writer publishes the incoming settings by
clearing the active snapshot pointer after the operation. Snapshot preparation
and the native operation leave interrupts enabled. Final epoch/settings publication
uses a short interrupt mask, with no native copying or callbacks inside it. Native copy arguments,
register returns and interrupt level are preserved; condition codes are not
part of the C calling contract. Nested stock operations retain the outer
snapshot. Bulk operations crossing bank boundaries are outside this live Part
boundary and require stopped-project lifecycle validation.

`mp_read` and `mp_read_key` use the snapshot. Direct native memory readers do
not; new MIDI consumers must use the explicit-context API. Runtime held-note
ownership is separate and must keep the original release identity. Each replaced Part advances a runtime-only epoch. Follow uses that epoch to
wait for the new Part's next ordinary trig before LIVE response can act;
Harmony uses it to discard the outgoing Part's AUTO history. Existing note
release ownership and deadlines remain unchanged. Ordinary setting edits do
not advance the epoch.

DEG receives one `hd_part_before` callback per affected Part after snapshot
publication and must consult the affected-Part mask to defer reattachment.
The degree integration gate covers that combined path, including interrupted
replacement with all eight tracks and four pending-event slots per track.

The linked-code gates exercise explicit contexts, bounded writes, native
copy/initialization byte and ABI equivalence, and interruption while settings
are partially replaced. Full firmware checks below cover native Part and
project persistence separately. Neither layer establishes hardware acceptance.

SETUP offset 12 is a shared flags byte: bit 0 Follow MODE, bit 1 Follow
TRIG/LIVE response. This module owns its native range (0..3) and byte claim.
Each writer preserves the other flag. Fresh Parts initialize both flags to zero.

The image gates cover explicit-context reads, native copy/clear equivalence,
interrupted publication and NOTE SETUP staging. Full firmware persistence tests
are supplied by consumers when they add their panel and project controls.

NOTE SETUP YES refreshes RFOL/HARM staging from the selected Part before
stock confirms all six fields. This preserves immediately applied module
edits without replaying mode conversion or changing stock staged controls.
