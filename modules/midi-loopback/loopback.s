/* Experimental M1/channel-1 mirror. OFF by default, volatile lb_enabled.
 * Only proven sequencer send sites are sources. Incoming MIDI and audio
 * feedback therefore cannot recirculate. USB's entry detour stays intact.
 * Queue messages, not bytes: DIN running status is never touched.
 */
    .text
    .global lb_send, lb_receive, lb_capture, lb_next
    .global lb_enabled, lb_head, lb_tail, lb_accepted, lb_delivered
    .global lb_dropped, lb_highwater, lb_owned, lb_ring, lb_current
    .global lb_wake, lb_wake_pending, lb_external_turn

.set MIDI_Q, 0x46c7e974
.set POST, 0x40000c3c
.set RECEIVE, 0x40000d00

/* Inside midi_send, after its 20-byte save frame. Preserve its entire
 * input context; d7 is source track at the four admitted producer sites.
 */
lb_send:
    lea %sp@(-40),%sp
    moveml %d0-%d6/%a0-%a2,%sp@
    movel %sp@(60),%d0
    movel %d7,%d1
    movel %sp@(64),%d2
    moveal %sp@(68),%a0
    bsr lb_capture
    moveml %sp@,%d0-%d6/%a0-%a2
    lea %sp@(40),%sp
    moveal %sp@(28),%a2          /* displaced */
    tstl 0x460ba978             /* displaced; stock branch consumes flags */
    jmp 0x40010bda

/* d0=stock return PC, d1=source track, d2=len, a0=complete message.
 * Own one outstanding admission per note on fixed channel 1. OFF stops
 * new events but still admits releases for notes already mirrored.
 */
lb_capture:
    cmpil #3,%d2
    bne.w .capture_done
    mvzb %a0@,%d2
    cmpil #0x80,%d2
    beq.w .release_source
    cmpil #0x90,%d2
    beq.s .note_source
    cmpil #0xb0,%d2
    bne.w .capture_done
    tstl %d1
    bne.w .capture_done
    cmpil #0x4009fef2,%d0
    beq.s .new_event
    cmpil #0x4009ffbe,%d0
    bne.w .capture_done
    bra.s .new_event
.note_source:
    tstb %a0@(2)               /* stock sends releases as 90 note 00 */
    beq.s .release_source
    tstl %d1
    bne.w .capture_done
    cmpil #0x4009fbb2,%d0
    beq.s .new_event
    cmpil #0x4009fcfa,%d0
    bne.w .capture_done
.new_event:
    tstb lb_enabled
    beq.w .capture_done
    /* Fixed channel 1 is the proof boundary, not a channel remapper. */
    bra.s .admit
.release_source:
    /* Sequencer expiry, retrigger/steal, and end-of-pass cleanup sites.
     * Ownership is the old channel/note, not the newly configured route. */
    cmpil #0x4009f370,%d0        /* stock stop/track cleanup */
    beq.s .admit
    cmpil #0x4009f8c2,%d0
    beq.s .admit
    cmpil #0x4009fc54,%d0
    beq.s .admit
    cmpil #0x4009fcd8,%d0
    beq.s .admit
    cmpil #0x400a0074,%d0
    beq.s .admit
    cmpil #0x400a00e6,%d0
    bne.w .capture_done
.admit:
    mvzb %a0@(1),%d3
    cmpil #127,%d3
    bhi.w .capture_done
    mvzb %a0@(2),%d1
    cmpil #127,%d1
    bhi.w .capture_done
    movew %sr,%d6
    movew #0x2700,%sr
    lea lb_owned,%a1
    moveq #0,%d4                /* 0 CC, 1 on, 2 release */
    cmpil #0xb0,%d2
    beq.s .capacity
    cmpil #0x80,%d2
    beq.s .owned_release
    tstl %d1
    beq.s .owned_release
    tstb %a1@(0,%d3:l)
    bne.w .unlock              /* no duplicate held-count increment */
    moveq #1,%d4
    bra.s .capacity
.owned_release:
    tstb %a1@(0,%d3:l)
    beq.w .unlock
    moveq #2,%d4
.capacity:
    movel lb_head,%d5
    subl lb_tail,%d5
    andil #255,%d5
    cmpil #2,%d4
    beq.s .append              /* 128 reserved slots for 128 owned notes */
    cmpil #127,%d5
    bcc.w .drop
.append:
    movel lb_head,%d0
    lea lb_ring,%a2
    lea %a2@(0,%d0:l:4),%a2
    moveb %d2,%a2@
    moveb %d3,%a2@(1)
    moveb %d1,%a2@(2)
    clrb %a2@(3)
    addql #1,%d0
    andil #255,%d0
    movel %d0,lb_head
    addql #1,lb_accepted
    addql #1,%d5
    cmpl lb_highwater,%d5
    bls.s .ownership
    movel %d5,lb_highwater
.ownership:
    tstl %d4
    beq.s .notify
    cmpil #1,%d4
    bne.s .clear_owned
    moveq #1,%d0
    moveb %d0,%a1@(0,%d3:l)
    bra.s .notify
.clear_owned:
    clrb %a1@(0,%d3:l)
.notify:
    tstb lb_wake_pending
    bne.s .unlock
    /* No stock-queue overflow: a full queue already keeps MIDI runnable.
     * lb_next checks our queue between stock messages. */
    movel MIDI_Q+4,%d0
    cmpl MIDI_Q+16,%d0
    bhi.s .unlock
    moveq #1,%d0
    moveb %d0,lb_wake_pending
    pea lb_wake
    pea MIDI_Q
    jsr POST
    addql #8,%sp
    bra.s .unlock
.drop:
    addql #1,lb_dropped
.unlock:
    movew %d6,%sr
.capture_done:
    rts

/* Replace pea MIDI_Q / jsr a3, preserving the argument the stock task
 * removes after dispatch. lb_next runs only in the MIDI task. */
lb_receive:
    pea MIDI_Q
    bsr lb_next
    jmp 0x40005560

/* Return a complete message pointer in d0. Alternate native/internal
 * work when both queues are busy. Copy into a stable consumer slot before
 * releasing ring capacity; handlers finish before the next receive call.
 */
lb_next:
    lea %sp@(-16),%sp
    moveml %d2-%d3/%a2-%a3,%sp@
.next_again:
    movew %sr,%d3
    movew #0x2700,%sr
    movel lb_tail,%d0
    cmpl lb_head,%d0
    beq.s .native
    tstb lb_external_turn
    beq.s .internal
    tstl MIDI_Q+4
    bne.s .native
.internal:
    lea lb_ring,%a0
    movel %a0@(0,%d0:l:4),%d1
    movel %d1,lb_current
    addql #1,%d0
    andil #255,%d0
    movel %d0,lb_tail
    addql #1,lb_delivered
    moveq #1,%d0
    moveb %d0,lb_external_turn
    movew %d3,%sr
    movel #lb_current,%d0
    bra.s .next_done
.native:
    movew %d3,%sr
    pea MIDI_Q
    jsr RECEIVE
    addql #4,%sp
    cmpil #lb_wake,%d0
    bne.s .native_done
    /* Wake token never reaches the MIDI parser/handler table. */
    clrb lb_wake_pending
    clrb lb_external_turn
    bra.s .next_again
.native_done:
    clrb lb_external_turn
.next_done:
    moveml %sp@,%d2-%d3/%a2-%a3
    lea %sp@(16),%sp
    rts

    .balign 4
lb_enabled: .byte 0
lb_wake_pending: .byte 0
lb_external_turn: .byte 0
    .byte 0
lb_head: .long 0
lb_tail: .long 0
lb_accepted: .long 0
lb_delivered: .long 0
lb_dropped: .long 0
lb_highwater: .long 0
lb_current: .long 0
lb_wake: .long 0
lb_owned: .space 128,0
lb_ring: .space 1024,0
