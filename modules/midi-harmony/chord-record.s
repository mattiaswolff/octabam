    .include "remix.inc"
/* A queued native message contains a pointer, not a copied struct. Own the
 * physical-key messages until consumption so each retrigger keeps the
 * quality and track selected at the instant it was played. Native fields
 * remain unchanged; the two metadata bytes live after the native 12 bytes.
 */
    .text
    .global ch_record_post,ch_record_free,ch_record_on,ch_record_commit
ch_record_post:
    lea -20(%sp),%sp
    movem.l %d0-%d1/%a0-%a2,(%sp)
    move.l %d5,%d0
    jsr mh_get
    .ifdef HAVE_DEGREES
    tst.l %d0
    beq.w .post_done
    .else
    cmpi.l #2,%d0
    bcs.w .post_done
    .endif
    lea ch_messages,%a1
    move.l #256,%d1
.post_scan:
    tst.b 14(%a1)
    beq.s .post_found
    lea 16(%a1),%a1
    subq.l #1,%d1
    bne.s .post_scan
    /* Never overwrite a queued message. Visible diagnostic for a gate. */
    addq.l #1,ch_record_overflow
    bra.s .post_done
.post_found:
    moveq #1,%d0
    move.b %d0,14(%a1)
    lea 0x46c77bea,%a0
    move.l (%a0),(%a1)
    move.l 4(%a0),4(%a1)
    move.l 8(%a0),8(%a1)
    move.b %d5,13(%a1)
    lea ch_live,%a2
    move.b (%a2,%d5.l),%d0
    move.b %d0,12(%a1)
    .ifdef HAVE_DEGREES
    moveq #0,%d0
    move.b 2(%a1),%d0
    move.l %d5,%d1
    jsr hd_capture
    jsr hd_capture_transition
    move.b %d0,15(%a1)
    .endif
    move.l %a1,56(%sp) /* original sp+36: posted pointer argument */
.post_done:
    movem.l (%sp),%d0-%d1/%a0-%a2
    lea 20(%sp),%sp
    movem.l (%sp),%d2-%d7/%a2
    lea 28(%sp),%sp
    jmp 0x40000c3c

/* Called at the end of the common key-event consumer, while a2 still
 * identifies its message. Validate range and alignment before freeing. */
ch_record_free:
    move.l %a2,%d0
    subi.l #ch_messages,%d0
    cmpi.l #4095,%d0
    bhi.s .free_done
    moveq #15,%d1
    and.l %d0,%d1
    bne.s .free_done
    clr.b 14(%a2)
.free_done:
    jmp 0x40045614

/* Wrapper around native live recorder, called with its four arguments.
 * Active quality is scoped to this call, never a later unrelated record. */
ch_record_on:
    lea -8(%sp),%sp
    movem.l %d2/%a2,(%sp)
    moveq #-1,%d2
    .ifdef HAVE_DEGREES
    move.l %d2,hd_record_active
    .endif
    move.l %a2,%d0
    subi.l #ch_messages,%d0
    cmpi.l #4095,%d0
    bhi.s .on_call
    moveq #15,%d1
    and.l %d0,%d1
    bne.s .on_call
    moveq #0,%d2
    move.b 12(%a2),%d2
    .ifdef HAVE_DEGREES
    moveq #0,%d0
    move.b 15(%a2),%d0
    move.l %d0,hd_record_active
    .endif
    moveq #0,%d0
    move.b 13(%a2),%d0
    move.l %d0,12(%sp) /* captured track */
.on_call:
    move.l %d2,ch_record_active
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    move.l 24(%sp),-(%sp)
    jsr 0x40041bc4
    lea 16(%sp),%sp
    moveq #-1,%d0
    move.l %d0,ch_record_active
    .ifdef HAVE_DEGREES
    move.l %d0,hd_record_active
    .endif
    movem.l (%sp),%d2/%a2
    addq.l #8,%sp
    rts

/* Native recorder has resolved bank/pattern/quantized step and made the
 * note trig. Replace NOTE for a CHRD event even when another physical
 * key/change landed on this same step. Never append generated NOT2-4.
 */
ch_record_commit:
    move.l ch_record_active,%d0
    cmpi.l #7,%d0
    bhi.w .commit_stock
    lea -36(%sp),%sp
    movem.l %d0-%d7/%a0,(%sp)
    move.l %d0,%d4
    move.l %d6,%d0
    move.l %d5,%d1
    move.l 8(%fp),%d2
    move.l %a3,%d3
    jsr ch_lock_set
    .ifdef HAVE_DEGREES
    move.w %sr,%d0
    move.l %d0,-(%sp)
    move.w #0x2700,%sr
    .endif
    /* NOTE + velocity in the native bank and its current-bank mirror. */
    move.l %d6,%d0
    move.l #0x9b340,%d1
    mulu.l %d1,%d0
    lea 0x400e21e0,%a0
    adda.l %d0,%a0
    move.l %d5,%d0
    move.l #0x8ed8,%d1
    mulu.l %d1,%d0
    move.l 8(%fp),%d2
    move.l #0x8b0,%d1
    mulu.l %d1,%d2
    add.l %d2,%d0
    move.l %a3,%d2
    lsl.l #5,%d2
    add.l %d2,%d0
    addi.l #0x4900,%d0
    move.l %a4,%d1
    move.b %d1,(%a0,%d0.l)
    move.l 16(%fp),%d2
    move.b %d2,1(%a0,%d0.l)
    moveq #0,%d3
    move.b 0x80000002,%d3
    cmp.l %d6,%d3
    bne.s .commit_done
    lea 0x1001614e,%a0
    move.b %d1,(%a0,%d0.l)
    move.b %d2,1(%a0,%d0.l)
.commit_done:
    .ifdef HAVE_DEGREES
    move.l %d6,%d0
    move.l %d5,%d1
    move.l 8(%fp),%d2
    move.l %a3,%d3
    move.l hd_record_active,%d4
    jsr hd_record
    move.l (%sp)+,%d0
    move.w %d0,%sr
    /* Retention is deliberately outside the root-publication mask. */
    moveq #0,%d0
    move.b 0x80000002,%d0
    jsr hd_nv_save
    .endif
    movem.l (%sp),%d0-%d7/%a0
    lea 36(%sp),%sp
    jmp 0x400420fa
.commit_stock:
    lea 0x400e6ae0,%a0
    jmp 0x40041f78
    .balign 4
ch_record_active: .long -1
.ifdef HAVE_DEGREES
hd_record_active: .long -1
.endif
    .global ch_record_overflow
ch_record_overflow: .long 0
    .bss
    .balign 4
ch_messages: .space 4096

    .text
    .global ch_record_off,ch_record_grid_off
/* The UI can change tracks between enqueue and consume. Off messages must
 * use the same captured owner as on messages, including native grid entry. */
ch_record_off:
    bsr.s .off_owner
    jmp 0x40041784
ch_record_grid_off:
    bsr.s .off_owner
    jmp 0x4004ef54
.off_owner:
    move.l %a2,%d0
    subi.l #ch_messages,%d0
    cmpi.l #4095,%d0
    bhi.s .off_owner_done
    moveq #15,%d1
    and.l %d0,%d1
    bne.s .off_owner_done
    moveq #0,%d0
    move.b 13(%a2),%d0
    move.l %d0,8(%sp)
.off_owner_done:
    rts

.ifdef HAVE_DEGREES
/* d0 track,d1 new mode. Enqueued HARM roots cross the same representation
 * boundary as their sequence; native physical key and release bytes stay put.
 * The UI consumer is serialized with the setter. ISR enqueue handles an
 * in-progress transition before publishing its new message. */
    .global hd_record_modes
hd_record_modes:
    lea -32(%sp),%sp
    movem.l %d0-%d5/%a0-%a1,(%sp)
    move.l %d0,%d4
    move.l %d1,%d5
    jsr mh_scale_record
    move.l %d0,%d3
    lea ch_messages,%a1
    move.l #256,%d2
.record_mode_loop:
    tst.b 14(%a1)
    beq.s .record_mode_next
    cmp.b 13(%a1),%d4
    bne.s .record_mode_next
    moveq #0,%d0
    move.b 15(%a1),%d0
    move.l %d3,%d1
    tst.l %d5
    beq.s .record_mode_off
    btst #7,%d0
    beq.s .record_mode_next
    andi.l #127,%d0
    jsr hd_encode
    bra.s .record_mode_store
.record_mode_off:
    btst #7,%d0
    bne.s .record_mode_next
    move.l %d0,-(%sp)
    jsr hd_decode
    tst.l %d0
    bpl.s .record_mode_absolute
    moveq #0,%d0
    move.l (%sp),%d1
    cmpi.l #7,%d1
    bcs.s .record_mode_absolute
    moveq #127,%d0
.record_mode_absolute:
    addq.l #4,%sp
    ori.l #128,%d0
.record_mode_store:
    move.b %d0,15(%a1)
.record_mode_next:
    lea 16(%a1),%a1
    subq.l #1,%d2
    bne.s .record_mode_loop
    movem.l (%sp),%d0-%d5/%a0-%a1
    lea 32(%sp),%sp
    rts
/* d0 captured degree,d1 track; entering messages already obey the target
 * mode while an interruptible OFF conversion is visiting existing messages. */
hd_capture_transition:
    lea -20(%sp),%sp
    movem.l %d1-%d3/%a0-%a1,(%sp)
    lea hd_busy,%a0
    tst.b (%a0,%d1.l)
    beq.s .capture_transition_done
    lea hd_target,%a0
    tst.b (%a0,%d1.l)
    bne.s .capture_transition_done
    move.l %d0,%d2
    move.l %d1,%d0
    jsr mh_scale_record
    move.l %d0,%d1
    move.l %d2,%d0
    jsr hd_decode
    tst.l %d0
    bpl.s .capture_transition_absolute
    moveq #0,%d0
    cmpi.l #7,%d2
    bcs.s .capture_transition_absolute
    moveq #127,%d0
.capture_transition_absolute:
    ori.l #128,%d0
.capture_transition_done:
    movem.l (%sp),%d1-%d3/%a0-%a1
    lea 20(%sp),%sp
    rts
.endif
