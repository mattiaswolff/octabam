/* Temporary receiver response: NEXT (0) or CHANGE (1).
 * CHANGE shifts currently owned sequencer voices when the ultimate source
 * changes root. Runs in the stock sequencer service, after pending releases
 * and before output. No synthetic trig, arp reset, recorder call or length
 * write: stock retains the original release deadline. Live source keys are
 * seen at the next service pass, without waiting for a receiver trig.
 */
    .text
    .include "remix.inc"
    .global bf_response_modes,bf_response_set,bf_response_get
    .global bf_response_tick,bf_response_observe,bf_response_anchor,bf_response_adjust

bf_response_get:
    cmpi.l #7,%d0
    bhi.s .get_zero
    lea bf_response_modes,%a0
    move.b (%a0,%d0.l),%d0
    andi.l #1,%d0
    rts
.get_zero:
    moveq #0,%d0
    rts
/* d0 track,d1 value; all registers preserved. Changes arm at the next note. */
bf_response_set:
    lea -8(%sp),%sp
    movem.l %d2/%a0,(%sp)
    cmpi.l #7,%d0
    bhi.s .set_done
    cmpi.l #1,%d1
    bhi.s .set_done
    lea bf_response_modes,%a0
    cmp.b (%a0,%d0.l),%d1
    beq.s .set_done
    move.b %d1,(%a0,%d0.l)
    moveq #-1,%d2
    lea bf_response_anchor,%a0
    move.l %d2,(%a0,%d0.l*4)
    lea bf_response_seen,%a0
    move.l %d2,(%a0,%d0.l*4)
    lea bf_response_pool,%a0
    move.l %d2,(%a0,%d0.l*4)
.set_done:
    movem.l (%sp),%d2/%a0
    lea 8(%sp),%sp
    rts

/* d0 receiver -> d0 effective root or -1, d1 source identity/pitch token.
 * d2-d4/a0-a1 preserved. Resolve chains; register, TRAN and Harmony snap
 * match the ordinary generator. The token also identifies changed routes.
 */
bf_response_target:
    lea -20(%sp),%sp
    movem.l %d2-%d4/%a0-%a1,(%sp)
    move.l %d0,%d3
    lea bf_sources,%a0
    moveq #0,%d1
    move.b (%a0,%d3.l),%d1
    moveq #8,%d2
.target_resolve:
    subq.l #1,%d1
    cmpi.l #7,%d1
    bhi.w .target_unknown
    move.l %d1,%d4
    moveq #0,%d1
    move.b (%a0,%d4.l),%d1
    beq.s .target_source
    subq.l #1,%d2
    bne.s .target_resolve
    bra.w .target_unknown
.target_source:
    move.l %d4,%d0
    move.l %d3,%d1
    jsr bf_register
    cmpi.l #256,%d0
    beq.w .target_unknown
    move.l %d3,%d2
    lsl.l #5,%d2
    lea 0x46c76fe0,%a0
    moveq #0,%d1
    move.b 12(%a0,%d2.l),%d1
    subi.l #64,%d1
    add.l %d1,%d0
    .ifdef HAVE_HARMONY
    move.l %d0,-(%sp)
    move.l %d3,%d0
    jsr mh_active
    tst.l %d0
    beq.s .target_no_arrange
    move.l (%sp)+,%d0
    lea 0x46c7a124,%a0
    moveq #0,%d1
    move.b (%a0,%d3.l),%d1
    add.l %d1,%d0
    bra.s .target_quant
.target_no_arrange:
    move.l (%sp)+,%d0
.target_quant:
    move.l %d3,%d1
    jsr mh_quant
    .endif
    cmpi.l #127,%d0
    bhi.s .target_unknown
    lea bf_pitches,%a0
    moveq #0,%d1
    move.b (%a0,%d4.l),%d1
    lsl.l #8,%d4
    or.l %d4,%d1
    bra.s .target_return
.target_unknown:
    moveq #-1,%d0
    moveq #-1,%d1
.target_return:
    movem.l (%sp),%d2-%d4/%a0-%a1
    lea 20(%sp),%sp
    rts

/* Keep cached Harmony arp pools relative to their last ordinary trig.
 * Shift only the outgoing scratch, leaving the arp clock/order intact. */
bf_response_adjust:
    .ifdef HAVE_HARMONY
    lea -16(%sp),%sp
    movem.l %d0-%d2/%a0,(%sp)
    lea bf_response_modes,%a0
    tst.b (%a0,%d7.l)
    beq.s .adjust_done
    move.l %d7,%d0
    jsr mh_active
    beq.s .adjust_done
    tst.b (%a2)
    bmi.s .adjust_done
    lea bf_response_pool,%a0
    move.l (%a0,%d7.l*4),%d2
    tst.l %d2
    bmi.s .adjust_done
    move.l %d7,%d0
    bsr.w bf_response_target
    tst.l %d0
    bmi.s .adjust_invalid
    sub.l %d2,%d0
    moveq #0,%d1
    move.b (%a2),%d1
    add.l %d1,%d0
    cmpi.l #127,%d0
    bls.s .adjust_store
.adjust_invalid:
    moveq #-1,%d0
.adjust_store:
    move.b %d0,(%a2)
.adjust_done:
    movem.l (%sp),%d0-%d2/%a0
    lea 16(%sp),%sp
    .endif
    rts

/* Called at the ordinary note boundary: d7 receiver, d4 voice, a2 pitch.
 * Capture the logical anchor and velocity, not an arp tone or inversion. */
bf_response_observe:
    tst.l %d4
    bne.s .observe_return
    tst.b (%a2)
    bmi.s .observe_return
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    lea bf_response_modes,%a0
    tst.b (%a0,%d7.l)
    beq.s .observe_done
    move.l %d7,%d0
    bsr.w bf_response_target
    lea bf_response_anchor,%a0
    move.l %d0,(%a0,%d7.l*4)
    lea bf_response_seen,%a0
    move.l %d1,(%a0,%d7.l*4)
    move.b 0x400d807e,%d0
    lea bf_response_velocity,%a0
    move.b %d0,(%a0,%d7.l)
.observe_done:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
.observe_return:
    rts

/* d0 stock trigger/release mask, d1 stock effective mute mask.
 * All regs preserved. Skip tracks with a scheduled edge on this pass. */
bf_response_tick:
    lea -80(%sp),%sp
    movem.l %d0-%d7/%a0-%a5,(%sp)
    move.l %d0,56(%sp)
    move.l %d1,60(%sp)
    moveq #0,%d7
.tick_track:
    lea bf_response_modes,%a0
    tst.b (%a0,%d7.l)
    beq.w .tick_next
    move.l %d7,%d0
    bsr.w bf_response_target
    move.l 56(%sp),%d2
    btst %d7,%d2
    beq.s .tick_pool_ready
    lea bf_response_pool,%a0
    move.l %d0,(%a0,%d7.l*4)
.tick_pool_ready:
    lea bf_response_seen,%a0
    move.l (%a0,%d7.l*4),%d2
    move.l %d1,(%a0,%d7.l*4)
    cmp.l %d2,%d1
    beq.w .tick_next
    tst.l %d0
    bmi.w .tick_forget
    tst.l %d2
    bmi.w .tick_next
    /* A routing change primes the new source; it is not a root gesture. */
    eor.l %d1,%d2
    andi.l #0xffffff00,%d2
    bne.w .tick_forget
    lea bf_response_anchor,%a0
    move.l (%a0,%d7.l*4),%d6
    tst.l %d6
    bmi.w .tick_next
    sub.l %d0,%d6
    neg.l %d6 /* delta from the sounding logical root */
    beq.w .tick_next
    move.l %d0,(%a0,%d7.l*4)
    move.l #0x10101,%d0
    lsl.l %d7,%d0
    and.l 56(%sp),%d0
    bne.w .tick_next
    move.l 60(%sp),%d0
    btst %d7,%d0
    bne.w .tick_next
    lea 0x80006676,%a0
    move.b (%a0,%d7.l),%d0
    cmpi.b #-1,%d0
    beq.w .tick_next
    lea 0x8000666e,%a0
    move.b (%a0,%d7.l),%d0
    cmpi.b #-1,%d0
    beq.w .tick_next
    move.l %d7,%d0
    moveq #68,%d1
    muls.l %d1,%d0
    lea 0x46c76de0,%a0
    tst.b (%a0,%d0.l)
    beq.w .tick_next
    move.l %d7,%d0
    lsl.l #5,%d0
    lea 0x46c77a16,%a3
    adda.l %d0,%a3
    lea 64(%sp),%a4 /* four proposed pitches; -1 means no owned voice */
    lea 0x46c78152,%a5
    moveq #0,%d4
.tick_release:
    moveq #-1,%d0
    move.l %d0,(%a4,%d4.l*4)
    move.l 4(%a3),%d2
    cmpi.l #127,%d2
    bhi.s .release_next
    move.l (%a3),%d5
    andi.l #15,%d5
    lsl.l #7,%d5
    add.l %d2,%d5
    move.l %d7,%d3
    lsl.l #2,%d3
    add.l %d4,%d3
    cmp.b (%a5,%d5.l),%d3
    bne.s .release_next /* Never release another track or live key owner. */
    move.l %d2,%d0
    add.l %d6,%d0
    move.l %d0,(%a4,%d4.l*4)
    moveq #-1,%d0
    move.b %d0,(%a5,%d5.l)
    move.l %d0,4(%a3)
    move.l (%a3),%d0
    move.l %d2,%d1
    moveq #0,%d2
    bsr.w .send
.release_next:
    addq.l #1,%d4
    addq.l #8,%a3
    cmpi.l #4,%d4
    bne.s .tick_release
    lea -32(%a3),%a3
    moveq #0,%d4
.tick_on:
    move.l (%a4,%d4.l*4),%d1
    cmpi.l #127,%d1
    bhi.s .on_next /* MIDI underflow/overflow becomes silence. */
    move.l (%a3),%d5
    andi.l #15,%d5
    lsl.l #7,%d5
    add.l %d1,%d5
    move.b (%a5,%d5.l),%d0
    cmpi.b #-1,%d0
    bne.s .on_next /* Preserve existing channel/note ownership. */
    lea bf_response_velocity,%a0
    moveq #0,%d2
    move.b (%a0,%d7.l),%d2
    beq.s .on_next
    move.l %d1,4(%a3)
    move.l %d7,%d3
    lsl.l #2,%d3
    add.l %d4,%d3
    move.b %d3,(%a5,%d5.l)
    move.l (%a3),%d0
    bsr.s .send
.on_next:
    addq.l #1,%d4
    addq.l #8,%a3
    cmpi.l #4,%d4
    bne.s .tick_on
    bra.s .tick_next
.tick_forget:
    lea bf_response_anchor,%a0
    moveq #-1,%d0
    move.l %d0,(%a0,%d7.l*4)
.tick_next:
    addq.l #1,%d7
    cmpi.l #8,%d7
    bne.w .tick_track
    movem.l (%sp),%d0-%d7/%a0-%a5
    lea 80(%sp),%sp
    rts
/* Local packet, native MIDI queue. Stock sequencer status is signed 0x9n. */
.send:
    lea -4(%sp),%sp
    move.b %d0,(%sp)
    move.b %d1,1(%sp)
    move.b %d2,2(%sp)
    move.l %sp,%a0
    move.l %a0,-(%sp)
    pea 3
    jsr 0x40010bc8
    lea 12(%sp),%sp
    rts
    .balign 4
bf_response_modes: .space 8,0
bf_response_anchor: .space 32,0xff
bf_response_seen: .space 32,0xff
bf_response_velocity: .space 8,0
bf_response_pool: .space 32,0xff
