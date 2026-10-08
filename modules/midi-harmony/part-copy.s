/* Publish native Part replacement coherently without masking interrupts
 * throughout a native copy/clear. While a bank is being replaced, shared
 * readers see its complete outgoing MIDI SETUP snapshot. The single UI
 * writer publishes the incoming bytes by clearing the snapshot pointer.
 * No KITS dependency. Nested stock calls retain the outer transaction.
 */
    .include "remix.inc"
    .if MP_DEFINE
    .text
    .global mp_native_copy,mp_native_init,mp_snapshot_bank,mp_snapshot
mp_native_copy:
    lea -24(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    move.l 28(%sp),%d0
    move.l 36(%sp),%d1
    bsr.w .begin
    move.l %d0,16(%sp)
    movem.l (%sp),%d0-%d1/%a0-%a1
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    move.l 36(%sp),-(%sp)
    bsr.w .copy_stock
    lea 12(%sp),%sp
    bra.s .finish
mp_native_init:
    lea -24(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    move.l 28(%sp),%d0
    move.l #0x18b2,%d1
    bsr.w .begin
    move.l %d0,16(%sp)
    movem.l (%sp),%d0-%d1/%a0-%a1
    move.l 28(%sp),-(%sp)
    bsr.w .init_stock
    addq.l #4,%sp
.finish:
    tst.l 16(%sp)
    beq.s .finished
    clr.l mp_snapshot_bank
.finished:
    lea 24(%sp),%sp
    rts
.copy_stock:
    move.l %d2,-(%sp)
    move.l 8(%sp),%a1
    jmp 0x4002089e
.init_stock:
    lea -88(%sp),%sp
    movem.l %d2-%d7/%a2-%a6,(%sp)
    jmp 0x40005640

/* d0 destination,d1 length. Only resident bank writes intersecting working
 * Parts need a snapshot. Native copies spanning multiple banks are not a
 * live Part operation. Snapshot preparation only reads unchanged bytes:
 * interrupts remain enabled, including throughout native initialization.
 */
.begin:
    lea -28(%sp),%sp
    movem.l %d1-%d5/%a0-%a1,(%sp)
    tst.l mp_snapshot_bank
    bne.w .no_begin
    tst.l %d1
    beq.w .no_begin
    move.l %d0,%d2
    subi.l #0x400e21e0,%d2
    cmpi.l #16*0x9b340,%d2
    bcc.w .no_begin
    move.l %d2,%d3
    move.l #0x9b340,%d4
    divu.l %d4,%d3
    mulu.l %d3,%d4
    sub.l %d4,%d2
    add.l %d2,%d1
    bcs.w .no_begin
    cmpi.l #0x9b340,%d1
    bhi.w .no_begin
    cmpi.l #0x8ed80,%d1
    bls.s .no_begin
    cmpi.l #0x95048,%d2
    bcc.s .no_begin
    addi.l #0x400e21e0,%d4
    move.l %d4,%d5
    move.l %d4,%a0
    adda.l #0x8ed80+0x4e2,%a0
    lea mp_snapshot,%a1
    moveq #4,%d3
.snapshot_part:
    moveq #72,%d4
.snapshot_words:
    move.l (%a0)+,(%a1)+
    subq.l #1,%d4
    bne.s .snapshot_words
    adda.l #0x18b2-288,%a0
    subq.l #1,%d3
    bne.s .snapshot_part
    move.l %d5,mp_snapshot_bank
    moveq #1,%d0
    bra.s .begin_done
.no_begin:
    moveq #0,%d0
.begin_done:
    movem.l (%sp),%d1-%d5/%a0-%a1
    lea 28(%sp),%sp
    rts
    .balign 4
mp_snapshot_bank: .long 0
mp_snapshot: .space 4*288
    .endif
