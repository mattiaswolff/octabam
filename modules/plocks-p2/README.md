# `plocks-p2` — PLOCKS P2

Parameter locks on page 2 of FX1 and FX2. `Kind.CF_PATCH`: two DRAM
units, 52 detours, nothing on the DSP. Requires SCENES P2.

## Use

Open the FX1 or FX2 SETUP page, hold one or more trigs and turn a knob:
each held step gets that slot's page-2 lock. FUNC held while turning
removes it. The trig plays the lock and the next trig puts the Part's
value back, as page 1 does.

## Measured

Under the port, 2 Oct 2026, `tools/verify/verify_plocksp2.py` on
`plocks-p2` and on bottleservice with PLOCKS P2 added (Octakit, the bus, the FX1
stations, SCENES P2 KITS), project OCTABAM89_setgate:

- A held trig and knob A on the FX2 SETUP page lock step 1's page-2
  slot 0; stock's page-1 locks of step 1 stay 0xff.
- Trig copy and paste, clear a trig's locks, pattern copy and paste,
  clear pattern and its undo each carry or clear the page-2 locks with
  the stock data.
- T1 step 1 locked to 99 with trigs on steps 1 and 2: the live lane reads
  99 after step 1 and the Part's value after step 2; no other track's
  page-2 lane byte moves. The DSP record follows the lane (both pings,
  measured by hand the same day).
- SAVE PROJECT writes `p2lk03.work` and `p2lk03.strd` with the lock; a
  second boot of that card has it in the table after the load.
- Power cycles (`ot_emu --cs1-in` with the first run's CS1, `--no-post`
  for the firmware's own power-up load): a saved lock, a lock never saved,
  and a saved lock with the CS1 copy cleared (read from `p2lk03.work`)
  are each in the table after the power-up.

ColdFire compression gate, 9 Oct 2026:

- 34 round trips from the original upstream P2NV writer and through the
  compressed codec, including the exact 15,464-byte worst case.
- All 16 banks; all 128 values; 88 malformed/truncated cases; 36 interrupted
  writes; 50 injected same/different-bank preemptions, including density
  changes and overflow. Registers, stack and interrupt mask checked.
- The ledger accepts reuse of all 15,256 released bytes and rejects a
  one-byte overlap. After full legacy migration, overwriting the released
  tail leaves subsequent restore/save intact.

## On the unit

Not flashed.

## Open

- The CS1 copy holds 10,234 locks; a current bank with more has no copy
  and a power cut loses its page-2 locks back to the last save.
- That CS1 keeps its contents over a power-off on the unit is read from
  stock's use of it (the power-up check and restore), not measured here.
- Bank reload and project reload (the `.strd` → `.work` copies) are
  hooked and not exercised by the gate.
- The dial draw with trigs held (SCENES P2's dial hooks call `plk_dial`;
  the port's LCD was not decoded).
- Page 2 has no slide: a slide trig moves page 1 only.
- A held step with no trig takes a page-2 lock that never plays (stock
  makes a lock trig from a page-1 lock; not mirrored).
- On the unit.

## Retained snapshot compression and compatibility

Only the current-bank snapshot in battery SRAM changes. Existing
`p2lkNN.work` / `p2lkNN.strd` files remain **P2LK version 1**, byte for
byte in the same format. Older projects load directly; no conversion or
resave is required. New saves can also be read by the previous module.

The reader accepts both the original **P2NV** retained snapshots and the
new **P2R1** representation. P2R1 stores ascending slot gaps using Rice
coding with k=3 (unary quotient, 3 remainder bits), followed by each
7-bit value, MSB first with zero padding. Both formats have the original
16-byte big-endian header: magic, bank, count, sum of decoded entries.
The writer chooses P2NV when its three bytes per lock are no larger.
It validates all input before publishing magic, and the reader validates
bounds, ordering, padding and checksum before changing the runtime table.
Invalid or interrupted snapshots use the existing project-file fallback.

The old source's capacity is **10,234**, not the previously documented
10,229: `(30,720 - 16) // 3`. That capacity is unchanged. For n locks
among 98,304 slots, Rice uses at most
`11*n + floor((98,304-n)/8)` bits. At n=10,234 that is **15,464 bytes
including the header**, versus 30,718 bytes for P2NV. The gate constructs
locations that attain this bound; it does not assume sparse music.
Overflow still invalidates the entire retained snapshot, as before.

The SRAM reservation is now **15,464 bytes**,
`0x100f8600..0x100fc268` (end exclusive). New writes stay within it;
`0x100fc268..0x100ffe00` (**15,256 bytes**) is available to other modules.
The legacy P2NV reader may inspect the former 30,720-byte window during
upgrade, then rewrites the accepted snapshot compactly before returning.
A sharing bridge must restore PLOCKS P2 before writing that tail
if it promises migration of unsaved legacy state. It must also coordinate
the existing shared hooks; compression alone does not make Harmony
composable. This ordering is not required for saved projects: both old
and new firmware read the unchanged P2LK v1 files. Downgrading firmware
cannot restore P2R1 unsaved state; saved project files remain compatible.

### Writer ordering

UI and engine tasks can preempt one another. `nv_save` records the latest
bank and increments `NVGEN` under SR `0x2700`. One outer writer owns the
payload; a nested request invalidates magic and returns immediately.
The outer writer retries the latest bank if the generation changed, and
publishes magic only under the short final masked check. Neither task
spins waiting for a preempted task; scanning and encoding remain unmasked.
Writes stay bounded even when a nested edit changes density between the
size scan and encoding. Busy/generation state is transient, not retained.

`retention.c` is authoritative; run
`python3 modules/plocks-p2/generate_retention.py` to regenerate its linked
ColdFire assembly, following the existing Euclid workflow. The gate checks
that generated assembly matches before executing it.

`read_bank` still rejects a `p2lkNN` header whose version is not 1.

## Gates

- `tools/verify/verify_plocksp2.py`: panel/playback/save/reload, legacy
  P2LK v1 files across all 16 banks, compressed power-up and P2NV upgrade.
- `tools/verify/verify_plocksp2_retention.py`: actual ColdFire codec and
  pre-change writer, full-capacity migration, exact worst case, all banks,
  invalid/truncated input, interrupted publication, register/stack/mask
  preservation and injected UI/engine preemption. No stock image needed.

## What stock does

`docs/firmware/STEP_LOCKS.md`. A step record is 32 lock bytes, page 1 of
the five pages. A trig's record goes from the step through a per-track
staging record and a pending slot to the frame ISR, which writes each
lock into the track's live lane and restores the Part's value at the next
trig. Nothing carries page 2, and every byte of the pattern data is used.

## What this adds

- **The table** (`.bss`, 1,572,864 B): 12 bytes a step for every bank,
  pattern, track and step; byte j = FX1 page-2 slot j, 6 + j = FX2's;
  0xff = no lock. `plk_init` fills it at the first use. The platform build
  refuses a `.bss` that ends past the arena reserve's ceiling.
- **Recording.** With a SETUP window open (`0x460d175c`) on the FX1 or
  FX2 page (`0x460d1684` = 3 / 4) and trigs held (`0x460d174a`), stock
  sends a knob turn to the page-1 lock editor `0x400508e4`, which locks
  the page-1 slot behind the window. `plk_edit` takes the turn instead:
  the slot's encoder hook and clamp from its descriptor, stock's edited
  marks (`DB + 0x9b332`, `0x100f8598`, `0x40027e00`), the slot's redraw.
- **Playback**, beside stock's stages: the record builder `0x4009d1e8`'s
  two fill paths (staging or pending slot n), the two staging → pending
  copies, the pending reset, the frame ISR's pending → trig record copy
  and a MIDI note's own record, and the join of the restore and apply
  paths (`0x4000c59e`), which writes the page-2 locks into the lane
  (`0x80000810 + 72t + 50 + j`) and restores the Part's bytes the last
  trig locked. SCENES P2's morph reads the lane as the knob.
- **Operations**: placing a trig, clearing locks, clearing a track or a
  pattern, trig copy and paste, and every memcpy site that moves a
  pattern (`0x8ed8`) or a track (`0x91a`) between the bank RAM, the
  clipboard (`0x460c8122`) and the undo buffer (`0x460bf218`): page 2
  follows in the same shape (two 6,144 B mirrors for the buffers). memcpy
  itself runs before the loader has placed the runtime, so its call sites
  are hooked, not its entry.
- **The current bank over a power-off.** Stock keeps the current bank in
  CS1 (`0x10000000`): `0x4000faf0` copies a bank there, edits write
  through, and at power-up `0x40025770` checks it, `0x4000fbb4` restores
  the bank and the firmware's load reads only the other banks from the
  card. The page-2 locks follow in CS1's unused top
  (`0x100f8600..0x100ffe00`), using the compatible retained formats above.
  The snapshot is rewritten when stock copies a bank into CS1 and after
  every change to that bank; at power-up it is applied after stock's
  restore, or the bank's `p2lkNN.work` is read at the first bank load.
  Before 2 Oct 2026 nothing read the current bank at power-up, so its
  page-2 locks came back empty even when saved (measured under the port).
- **Files**: `p2lkNN.work` / `p2lkNN.strd` beside `bankNN.*` in the
  project directory, 16 bytes of header (`P2LK`, version 1, bank, length)
  and the bank's 98,304 B. Written where stock writes `bankNN.work`
  (`0x400918aa`), copied where stock copies `.work` ↔ `.strd` (bank store
  and reload, the project store and reload loops), read at the project
  load and the masked bank loads, and emptied for a new project. A missing
  source copies as an empty file.

## KITS

KITS (in bottleservice beside this module since 6 Oct 2026) hooks the
file routines' own entries (`0x40090504`, `0x400905d4`, `0x400909d8`,
`0x400917c8`, `0x4008ee74`, `0x4008f180`) where this module hooks their
call sites, so the two share no site. Its CS1 ranges (`0x100f85a0..e8`,
`0x100ffe00..ff00`) sit on either side of this module's.
