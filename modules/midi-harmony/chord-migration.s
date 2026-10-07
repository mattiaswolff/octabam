/* Old TYPE=3 is materialized only on existing NOTE trigs when a bank has
 * no companion. Keep eligibility in project comments and the CS1 header:
 * reloading a still-old stored bank must not silently lose its sevenths.
 * A present valid companion is always authoritative; damaged data is never
 * guessed. New/unlocked steps retain the fixed TRI fallback.
 */
    .text
    .global ch_legacy7_mask,ch_legacy_set,ch_migrate_settings,ch_migrate_bank
ch_legacy_set: /* d0 track, d1 bool; preserve both */
    cmpi.l #7,%d0
    bhi.s .ls_done
    cmpi.l #1,%d1
    bhi.s .ls_done
    lea -8(%sp),%sp
    movem.l %d2/%a0,(%sp)
    move.l ch_legacy7_mask,%d2
    bclr %d0,%d2
    tst.l %d1
    beq.s .ls_save
    bset %d0,%d2
    /* Preserve the old live seventh choice too; sequencer fallback remains TRI. */
    lea ch_base,%a0
    move.b %d1,(%a0,%d0.l)
    lea ch_live,%a0
    move.b %d1,(%a0,%d0.l)
    lea ch_current,%a0
    move.b %d1,(%a0,%d0.l)
.ls_save:
    move.l %d2,ch_legacy7_mask
    movem.l (%sp),%d2/%a0
    addq.l #8,%sp
.ls_done:
    rts
ch_migrate_settings:
    lea -16(%sp),%sp
    movem.l %d0-%d2/%a0,(%sp)
    moveq #0,%d0
    lea 0x100b14e2,%a0
.ms_track:
    moveq #0,%d2
    move.b (%a0,%d0.l),%d2
    andi.l #3,%d2
    cmpi.l #3,%d2
    bne.s .ms_next
    move.b (%a0,%d0.l),%d2
    bclr #0,%d2
    move.b %d2,(%a0,%d0.l)
    moveq #1,%d1
    bsr.w ch_legacy_set
.ms_next:
    addq.l #1,%d0
    cmpi.l #8,%d0
    bne.s .ms_track
    movem.l (%sp),%d0-%d2/%a0
    lea 16(%sp),%sp
    rts
ch_migrate_bank: /* d0 bank; preserve all */
    lea -36(%sp),%sp
    movem.l %d0-%d6/%a0-%a1,(%sp)
    cmpi.l #15,%d0
    bhi.s .mb_done
    move.l ch_legacy7_mask,%d6
    beq.s .mb_done
    move.l #0x9b340,%d1
    mulu.l %d0,%d1
    lea 0x400e21e0+0x48d0,%a1
    adda.l %d1,%a1
    lsl.l #8,%d0
    lsl.l #5,%d0
    lea ch_lock_table,%a0
    adda.l %d0,%a0
    moveq #16,%d5
.mb_pattern:
    moveq #0,%d4
.mb_track:
    btst %d4,%d6
    beq.s .mb_next_track
    moveq #0,%d3
.mb_step:
    move.l %d3,%d1
    lsr.l #3,%d1
    eori.l #7,%d1 /* native 64-bit trig bitmap is big endian */
    moveq #0,%d2
    move.b (%a1,%d1.l),%d2
    move.l %d3,%d1
    andi.l #7,%d1
    btst %d1,%d2
    beq.s .mb_next_step
    moveq #1,%d0
    move.b %d0,(%a0,%d3.l)
.mb_next_step:
    addq.l #1,%d3
    cmpi.l #64,%d3
    bne.s .mb_step
.mb_next_track:
    lea 64(%a0),%a0
    adda.l #0x8b0,%a1
    addq.l #1,%d4
    cmpi.l #8,%d4
    bne.s .mb_track
    adda.l #0x8ed8-8*0x8b0,%a1
    subq.l #1,%d5
    bne.s .mb_pattern
.mb_done:
    movem.l (%sp),%d0-%d6/%a0-%a1
    lea 36(%sp),%sp
    rts
    .balign 4
ch_legacy7_mask: .long 0
