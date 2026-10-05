/* Compact automatic voice leading. d0=track, a0=four generated pitches.
 * Called only AFTER Follow captures the harmonic root. Never touches NOTE,
 * recorder arguments, or bf_roots. Preserves all input registers.
 *
 * Enumerate each inversion at octave offsets 0,-12,+12, rejecting pitches
 * outside MIDI and bass notes more than an octave from the requested root.
 * Cost = 8 * sum(abs(new[i]-previous[i])) + number of moving voices.
 * This first minimizes total movement, then maximizes held common voices.
 * Exact ties prefer root position, then the earlier inversion/offset.
 * First chord/context change seeds root position. Incomplete top-of-MIDI
 * chords keep the generator's omission behavior and invalidate history.
 */
    .text
    .global mh_voice,mh_voice_history,mh_voice_clear
mh_voice_clear:
    lea mh_voice_history,%a0
    moveq #16,%d0
.vc_loop:
    clr.l (%a0)+
    subq.l #1,%d0
    bne.s .vc_loop
    rts

mh_voice:
    lea -76(%sp),%sp
    movem.l %d0-%d7/%a0-%a4,(%sp)
    cmpi.l #7,%d0
    bhi.w .voice_done
    move.l %d0,%d7
    move.l %a0,%a4
    lea mh_voice_history,%a2
    lsl.l #3,%d0
    adda.l %d0,%a2
    move.l %d7,%d0
    jsr mh_voic_get
    tst.l %d0
    beq.w .voice_reset
    move.l %d7,%d0
    jsr mh_active
    cmpi.l #2,%d0
    blt.w .voice_reset
    move.l %d0,%d6
    addq.l #1,%d6 /* 3 or 4 voices */
    move.l %d7,%d0
    jsr mh_scale_record
    move.l %d0,%d5
    move.l %d7,%d0
    jsr mh_source
    lsl.l #8,%d0
    lsl.l #2,%d0
    or.l %d0,%d5
    move.l %d6,%d0
    swap %d0
    or.l %d0,%d5 /* token = count<<16 | source<<10 | effective scale */
    move.l %d5,72(%sp)
    move.l (%a4),52(%sp) /* immutable root-position input */
    move.l (%a4),56(%sp) /* best chord */
    lea 52(%sp),%a3
    moveq #0,%d3
    moveq #-1,%d1
.voice_validate:
    moveq #0,%d0
    move.b (%a3,%d3.l),%d0
    cmpi.l #127,%d0
    bhi.w .voice_reset
    cmp.l %d1,%d0
    ble.w .voice_reset
    move.l %d0,%d1
    addq.l #1,%d3
    cmp.l %d6,%d3
    blt.s .voice_validate
    cmp.l 4(%a2),%d5
    bne.w .voice_remember
    moveq #0,%d0
    move.b (%a3),%d0
    move.l %d0,68(%sp) /* anchor root */
    move.l #0x7fffffff,%d0
    move.l %d0,64(%sp)
    moveq #0,%d4 /* inversion */
.voice_inversion:
    moveq #0,%d5 /* octave offset, ordered 0,-12,+12 */
.voice_candidate:
    moveq #0,%d2 /* score */
    moveq #0,%d3 /* voice */
.voice_pitch:
    move.l %d4,%d1
    add.l %d3,%d1
    moveq #0,%d0
    cmp.l %d6,%d1
    blt.s .voice_unwrapped
    sub.l %d6,%d1
    moveq #12,%d0
.voice_unwrapped:
    add.l %d5,%d0
    moveq #0,%d7
    move.b (%a3,%d1.l),%d7
    add.l %d7,%d0
    cmpi.l #127,%d0
    bhi.s .voice_next_octave /* unsigned comparison rejects negatives too */
    tst.l %d3
    bne.s .voice_distance
    move.l %d0,%d1
    sub.l 68(%sp),%d1
    bpl.s .voice_anchor
    neg.l %d1
.voice_anchor:
    cmpi.l #12,%d1
    bgt.s .voice_next_octave
.voice_distance:
    lea 60(%sp),%a0
    move.b %d0,(%a0,%d3.l)
    moveq #0,%d1
    move.b (%a2,%d3.l),%d1
    sub.l %d1,%d0
    beq.s .voice_same
    bpl.s .voice_positive
    neg.l %d0
.voice_positive:
    lsl.l #3,%d0
    addq.l #1,%d0
    add.l %d0,%d2
.voice_same:
    addq.l #1,%d3
    cmp.l %d6,%d3
    blt.s .voice_pitch
    cmp.l 64(%sp),%d2
    bge.s .voice_next_octave
    move.l %d2,64(%sp)
    move.l 60(%sp),56(%sp)
.voice_next_octave:
    tst.l %d5
    bgt.s .voice_next_inversion
    beq.s .voice_lower
    moveq #12,%d5
    bra.w .voice_candidate
.voice_lower:
    moveq #-12,%d5
    bra.w .voice_candidate
.voice_next_inversion:
    addq.l #1,%d4
    cmp.l %d6,%d4
    blt.w .voice_inversion
.voice_remember:
    cmpi.l #3,%d6
    bne.s .voice_copy
    move.b 56(%sp),59(%sp) /* triad padding duplicates lowest voice */
.voice_copy:
    move.l 56(%sp),(%a4)
    move.l 56(%sp),(%a2)
    move.l 72(%sp),4(%a2)
    bra.s .voice_done
.voice_reset:
    clr.l 4(%a2)
.voice_done:
    movem.l (%sp),%d0-%d7/%a0-%a4
    lea 76(%sp),%sp
    rts
    .balign 4
mh_voice_history: .space 64,0
