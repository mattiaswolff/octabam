    .include "remix.inc"
/* CHRD travels beside native MIDI staging/pending locks, never in them.
 * The builder resolves the exact bank/pattern/track/step before scheduling.
 * A fired pending record publishes its own quality, including TRI on an
 * unlocked step. UI bank and currently selected live chord are irrelevant.
 */
    .text
    .global ch_stage_fill,ch_stage_copy_a,ch_stage_copy_b,ch_pending_fire
ch_stage_fill:
    lea -28(%sp),%sp
    movem.l %d0-%d4/%a0-%a1,(%sp)
    move.l %d3,%d2 /* track before native multiply below */
    move.l %d7,%d3 /* exact scheduled step */
    move.l 76(%sp),%d0 /* bank: original sp+48 */
    move.l %a3,%d1
    .ifdef HAVE_DEGREES
    move.l 88(%sp),%d4
    jsr hd_stage
    .endif
    jsr ch_lock_get
    move.l 88(%sp),%d1 /* pending slot: original sp+60 */
    lea ch_staged,%a0
    tst.l %d1
    bmi.s .stage_ready
    cmpi.l #3,%d1
    bhi.s .stage_done
    lsl.l #3,%d1
    lea ch_pending,%a0
    adda.l %d1,%a0
.stage_ready:
    move.b %d0,(%a0,%d2.l)
.stage_done:
    movem.l (%sp),%d0-%d4/%a0-%a1
    lea 28(%sp),%sp
    move.l %d3,%d1
    lsl.l #5,%d1
    lea (%a5,%d1.l),%a0
    jmp 0x4009d188
ch_stage_copy_a:
    lea -8(%sp),%sp
    movem.l %d0/%a0,(%sp)
    .ifdef HAVE_DEGREES
    move.l %d2,%d0
    jsr hd_stage_copy
    .endif
    lea ch_staged,%a0
    move.b (%a0,%d2.l),%d0
    lea ch_pending,%a0
    move.b %d0,(%a0,%d2.l)
    movem.l (%sp),%d0/%a0
    addq.l #8,%sp
    adda.l #0x46c78960,%a0
    jmp 0x4009b922
ch_stage_copy_b:
    lea -8(%sp),%sp
    movem.l %d0/%a0,(%sp)
    .ifdef HAVE_DEGREES
    move.l %d1,%d0
    jsr hd_stage_copy
    .endif
    lea ch_staged,%a0
    move.b (%a0,%d1.l),%d0
    lea ch_pending,%a0
    move.b %d0,(%a0,%d1.l)
    movem.l (%sp),%d0/%a0
    addq.l #8,%sp
    adda.l #0x46c78960,%a0
    jmp 0x4009c10e
ch_pending_fire:
    lea -12(%sp),%sp
    movem.l %d0/%a0/%a1,(%sp)
    move.l %a0,%d0
    subi.l #0x46c78960,%d0
    lsr.l #5,%d0
    cmpi.l #31,%d0
    bhi.s .fire_done
    .ifdef HAVE_DEGREES
    jsr hd_fire
    .endif
    lea ch_pending,%a0
    move.b (%a0,%d0.l),%d0
    lea ch_sequence_quality,%a0
    move.b %d0,(%a0,%d5.l)
.fire_done:
    movem.l (%sp),%d0/%a0/%a1
    lea 12(%sp),%sp
    movem.l (%a0),%d1-%d4/%d6-%d7/%a4-%a5
    movem.l %d1-%d4/%d6-%d7/%a4-%a5,(%a1)
    jmp 0x400a19e2
    .balign 4
ch_staged: .space 8,0
ch_pending: .space 32,0
