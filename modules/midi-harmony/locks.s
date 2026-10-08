    .include "remix.inc"
/* Dedicated CHRD locks: bank x pattern x MIDI track x step.
 * Native NOTE / NOT2-4 / CC bytes are never storage for this module.
 * 0xff is unlocked; only the reader resolves it to TRI (0).
 * The current bank has a dense CS1 mirror, with a generation ticket to
 * prevent an engine writer from committing over a preempting UI writer.
 * The manifest owns this SRAM and refuses composition with PLOCKS P2.
 */
    .set CH_BANK_BYTES,8192
    .set CH_BYTES,131072
    .set CH_NV,0x100f8600
    .set CH_MAGIC,0x43484e56
    .text
    .global ch_lock_init,ch_lock_ptr,ch_lock_get,ch_lock_set,ch_lock_table
    .global ch_nv_save,ch_nv_restore,ch_nv_bank,ch_lock_status
ch_lock_init:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    move.l ch_initialized,%d0
    cmpi.l #0x43485244,%d0
    beq.s .init_done
    lea ch_lock_table,%a0
    move.l #CH_BYTES/4,%d1
    moveq #-1,%d0
.init_fill:
    move.l %d0,(%a0)+
    subq.l #1,%d1
    bne.s .init_fill
    move.l #0x43485244,%d0
    move.l %d0,ch_initialized
.ifdef HAVE_DEGREES
    jsr hd_reset
.endif
.init_done:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    rts

/* d0 bank, d1 pattern, d2 track, d3 step -> a0 (0 for invalid).
 * All input registers preserved. No lazy init in an ISR lookup.
 */
ch_lock_ptr:
    suba.l %a0,%a0
    cmpi.l #15,%d0
    bhi.s .ptr_done
    cmpi.l #15,%d1
    bhi.s .ptr_done
    cmpi.l #7,%d2
    bhi.s .ptr_done
    cmpi.l #63,%d3
    bhi.s .ptr_done
    move.l %d4,-(%sp)
    move.l %d0,%d4
    lsl.l #4,%d4
    add.l %d1,%d4
    lsl.l #3,%d4
    add.l %d2,%d4
    lsl.l #6,%d4
    add.l %d3,%d4
    lea ch_lock_table,%a0
    adda.l %d4,%a0
    move.l (%sp)+,%d4
.ptr_done:
    rts
ch_lock_get:
    jsr ch_lock_ptr
    move.l %a0,%d0
    beq.s .get_default
    moveq #0,%d0
    move.b (%a0),%d0
    cmpi.l #7,%d0
    bls.s .get_done
.get_default:
    moveq #0,%d0
.get_done:
    rts

/* Same indices, d4=quality or 255. All registers preserved.
 * Invalid inputs have no writes. Caller marks the native bank dirty.
 */
ch_lock_set:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    cmpi.l #7,%d4
    bls.s .set_valid
    cmpi.l #255,%d4
    bne.s .set_done
.set_valid:
    jsr ch_lock_ptr
    move.l %a0,%d1
    beq.s .set_done
    move.b %d4,(%a0)
    cmp.l ch_nv_bank,%d0
    bne.s .set_done
    jsr ch_nv_save
.set_done:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    rts

/* d0=bank. Writes a full current-bank snapshot (no sparse capacity cap).
 * Header: magic committed last, version, bank, size, sum, generation.
 * A torn snapshot is rejected; the companion file is the recovery source.
 * Long interrupt masks would delay the audio ISR, so only ticket/commit
 * are protected. Generation mismatch restarts using the newest bank.
 */
ch_nv_save:
.ifdef HAVE_DEGREES
    jmp hd_nv_save
.endif
    cmpi.l #15,%d0
    bhi.w .nv_return
    lea -36(%sp),%sp
    movem.l %d0-%d6/%a0-%a1,(%sp)
    move.w %sr,%d6
    move.w #0x2700,%sr
    move.l %d0,ch_nv_bank
    addq.l #1,ch_nv_generation
    move.w %d6,%sr
.nv_restart:
    move.l ch_nv_generation,%d5
    move.l ch_nv_bank,%d0
    move.l %d0,%d4
    lsl.l #8,%d0
    lsl.l #5,%d0
    lea ch_lock_table,%a0
    adda.l %d0,%a0
    lea CH_NV,%a1
    clr.l (%a1)
    lea 32(%a1),%a1
    move.l #CH_BANK_BYTES/4,%d2
    moveq #0,%d3
.nv_copy:
    cmp.l ch_nv_generation,%d5
    bne.s .nv_restart
    move.l (%a0)+,%d1
    add.l %d1,%d3
    move.l %d1,(%a1)+
    subq.l #1,%d2
    bne.s .nv_copy
    move.w %sr,%d6
    move.w #0x2700,%sr
    cmp.l ch_nv_generation,%d5
    bne.s .nv_retry
    lea CH_NV,%a1
    moveq #1,%d0
    move.l %d0,4(%a1)
    move.l %d4,8(%a1)
    move.l #CH_BANK_BYTES,%d0
    move.l %d0,12(%a1)
    move.l %d3,16(%a1)
    move.l %d5,20(%a1)
    lea ch_lock_status,%a0
    moveq #0,%d0
    move.b (%a0,%d4.l),%d0
    lsl.l #8,%d0
    or.l ch_legacy7_mask,%d0
    move.l %d0,24(%a1)
    not.l %d0
    move.l %d0,28(%a1)
    move.l #CH_MAGIC,%d0
    move.l %d0,(%a1)
    move.w %d6,%sr
    movem.l (%sp),%d0-%d6/%a0-%a1
    lea 36(%sp),%sp
.nv_return:
    rts
.nv_retry:
    move.w %d6,%sr
    bra.w .nv_restart

/* d0 bank -> d0=1 restored, 0 invalid; other registers preserved.
 * Validate the whole payload before changing any live table byte.
 */
ch_nv_restore:
.ifdef HAVE_DEGREES
    jmp hd_nv_restore
.endif
    lea -28(%sp),%sp
    movem.l %d1-%d5/%a0-%a1,(%sp)
    move.l %d0,%d4
    cmpi.l #15,%d4
    bhi.w .restore_bad
    lea CH_NV,%a0
    move.l (%a0),%d1
    cmpi.l #CH_MAGIC,%d1
    bne.w .restore_bad
    move.l 4(%a0),%d1
    cmpi.l #1,%d1
    bne.w .restore_bad
    cmp.l 8(%a0),%d4
    bne.w .restore_bad
    move.l 12(%a0),%d1
    cmpi.l #CH_BANK_BYTES,%d1
    bne.w .restore_bad
    move.l 24(%a0),%d1
    cmpi.l #0x4ff,%d1 /* low byte legacy mask, next byte diagnostic */
    bhi.w .restore_bad
    not.l %d1
    cmp.l 28(%a0),%d1
    bne.w .restore_bad
    move.l 16(%a0),%d5
    lea 32(%a0),%a0
    moveq #0,%d3
    move.l #CH_BANK_BYTES/4,%d2
.restore_sum:
    add.l (%a0)+,%d3
    subq.l #1,%d2
    bne.s .restore_sum
    cmp.l %d5,%d3
    bne.s .restore_bad
    lea CH_NV+32,%a0
    move.l #CH_BANK_BYTES,%d2
.restore_validate:
    moveq #0,%d1
    move.b (%a0)+,%d1
    cmpi.l #7,%d1
    bls.s .restore_next
    cmpi.l #255,%d1
    bne.s .restore_bad
.restore_next:
    subq.l #1,%d2
    bne.s .restore_validate
    move.l %d4,%d0
    lsl.l #8,%d0
    lsl.l #5,%d0
    lea ch_lock_table,%a1
    adda.l %d0,%a1
    lea CH_NV+32,%a0
    move.l #CH_BANK_BYTES/4,%d2
.restore_copy:
    move.l (%a0)+,(%a1)+
    subq.l #1,%d2
    bne.s .restore_copy
    move.l CH_NV+24,%d0
    move.l %d0,%d1
    andi.l #255,%d0
    move.l %d0,ch_legacy7_mask
    lsr.l #8,%d1
    lea ch_lock_status,%a0
    move.b %d1,(%a0,%d4.l)
    move.l %d4,ch_nv_bank
    moveq #1,%d0
    bra.s .restore_done
.restore_bad:
    moveq #0,%d0
.restore_done:
    movem.l (%sp),%d1-%d5/%a0-%a1
    lea 28(%sp),%sp
    rts
    .balign 4
ch_initialized: .long 0
ch_nv_bank: .long -1
ch_nv_generation: .long 0
ch_lock_status: .space 16,0
    .bss
    .balign 4
ch_lock_table: .space CH_BYTES
