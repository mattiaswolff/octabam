/* Derive the displayed name from the unvoiced chord intervals, before
 * global inversion/spread/OMIT. Flat pitch spellings are enharmonic labels.
 * UI-only scratch; the audio/recording path never calls this routine.
 */
    .text
    .global ch_chord_name
ch_chord_name: /* d0 track -> a0 name; d0/d1/a1 volatile */
    lea -40(%sp),%sp
    movem.l %d2-%d7/%a2-%a3,(%sp)
    move.l %d0,%d7
    lea ch_name_text,%a2
    lea ch_last_root,%a0
    moveq #0,%d2
    move.b (%a0,%d7.l),%d2
    cmpi.l #127,%d2
    bhi.w .name_idle
    move.l %d2,%d0
    move.l %d7,%d1
    jsr mh_quant
    move.l %d0,%d2
.name_pc:
    cmpi.l #12,%d0
    bcs.s .name_pitch
    subi.l #12,%d0
    bra.s .name_pc
.name_pitch:
    lea .pitch_names,%a0
    move.l (%a0,%d0.l*4),%a0
    bsr.w .append
    move.l %d7,%d0
    jsr mh_active
    cmpi.l #2,%d0
    bcs.w .name_done
    move.l %d7,%d0
    jsr mh_scale_record
    move.l %d0,%d3
    lsr.l #2,%d3
    andi.l #15,%d3
    lsr.l #6,%d0
    lea .name_masks,%a0
    moveq #0,%d4
    move.w (%a0,%d0.l*2),%d4
    lea ch_live,%a0
    moveq #0,%d6
    move.b (%a0,%d7.l),%d6
    move.l %d2,%d0
    move.l %d6,%d1
    move.l %d2,36(%sp)
    move.l %d4,%d2
    lea 32(%sp),%a0
    jsr ch_build
    move.l 36(%sp),%d2
    /* Near the MIDI ceiling, build at a lower octave for the name. */
    cmpi.l #100,%d2
    bls.s .name_intervals
    subi.l #24,%d2
    move.l %d2,%d0
    move.l %d2,36(%sp)
    move.l %d4,%d2
    jsr ch_build
    move.l 36(%sp),%d2
.name_intervals:
    moveq #0,%d3
    move.b 33(%sp),%d3
    sub.l %d2,%d3
    moveq #0,%d4
    move.b 34(%sp),%d4
    sub.l %d2,%d4
    cmpi.l #3,%d6
    beq.w .name_sus2
    cmpi.l #4,%d6
    beq.w .name_sus4
    /* Triad identity: major, minor, diminished. Explicit qualities share it. */
    moveq #0,%d5
    cmpi.l #3,%d3
    bne.s .name_triad
    moveq #1,%d5
    cmpi.l #6,%d4
    bne.s .name_triad
    moveq #2,%d5
.name_triad:
    cmpi.l #1,%d6
    beq.s .name_seventh
    cmpi.l #7,%d6
    beq.s .name_seventh
    lea .triad_names,%a0
    move.l (%a0,%d5.l*4),%a0
    bsr.w .append
    cmpi.l #2,%d6
    bne.w .name_done
    moveq #0,%d0
    move.b 35(%sp),%d0
    sub.l %d2,%d0
    lea .add9,%a0
    cmpi.l #13,%d0
    bne.s .name_suffix
    lea .addb9,%a0
    bra.s .name_suffix
.name_seventh:
    lea .half_dim,%a0
    cmpi.l #2,%d5
    beq.s .name_suffix
    lea .minor7,%a0
    tst.l %d5
    bne.s .name_suffix
    moveq #0,%d0
    move.b 35(%sp),%d0
    sub.l %d2,%d0
    lea .dominant,%a0
    cmpi.l #11,%d0
    bne.s .name_suffix
    lea .major7,%a0
    bra.s .name_suffix
.name_sus2:
    lea .sus2,%a0
    cmpi.l #1,%d3
    bne.s .name_sus_fifth
    lea .susb2,%a0
    bra.s .name_sus_fifth
.name_sus4:
    lea .sus4,%a0
    cmpi.l #6,%d3
    bne.s .name_sus_fifth
    lea .sussharp4,%a0
.name_sus_fifth:
    bsr.s .append
    cmpi.l #6,%d4
    bne.s .name_done
    lea .flat5,%a0
.name_suffix:
    bsr.s .append
    bra.s .name_done
.name_idle:
    lea .idle,%a0
    bsr.s .append
.name_done:
    clr.b (%a2)
    lea ch_name_text,%a0
    movem.l (%sp),%d2-%d7/%a2-%a3
    lea 40(%sp),%sp
    rts
.append:
    move.b (%a0)+,%d0
    beq.s .append_done
    move.b %d0,(%a2)+
    bra.s .append
.append_done:
    rts
    .balign 4
.pitch_names: .long .c,.db,.d,.eb,.e,.f,.gb,.g,.ab,.a,.bb,.b
.triad_names: .long .major,.minor,.dim
.name_masks: .word 0xab5,0x6ad,0x5ab,0xad5,0x6b5,0x5ad,0x56b
.c: .asciz "C"
.db: .asciz "Db"
.d: .asciz "D"
.eb: .asciz "Eb"
.e: .asciz "E"
.f: .asciz "F"
.gb: .asciz "Gb"
.g: .asciz "G"
.ab: .asciz "Ab"
.a: .asciz "A"
.bb: .asciz "Bb"
.b: .asciz "B"
.major: .asciz ""
.minor: .asciz "m"
.dim: .asciz "dim"
.half_dim: .asciz "m7b5"
.minor7: .asciz "m7"
.dominant: .asciz "7"
.major7: .asciz "maj7"
.add9: .asciz "(add9)"
.addb9: .asciz "(addb9)"
.sus2: .asciz "sus2"
.susb2: .asciz "susb2"
.sus4: .asciz "sus4"
.sussharp4: .asciz "sus#4"
.flat5: .asciz "b5"
.idle: .asciz "PLAY A ROOT"
    .bss
ch_name_text: .space 32
