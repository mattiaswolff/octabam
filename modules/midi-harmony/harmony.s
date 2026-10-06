/* MIDI Harmony for 1.40C. No stored note/chord lanes are rewritten.
 * TYPE/SPRD share eight battery bytes e2..e9; ea VOIC bits, eb version.
 * Native KEY/scale remains in the Part. Quantizer ec..ee are separate.
 */
    .text
    .include "remix.inc"
    .set MH_NV,0x100b14e2
    .set MH_VERSION,0x100b14eb
    .set MH_VOIC,0x100b14ea
    .global mh_get,mh_set,mh_source,mh_quant,mh_generate,mh_sequence
    .global mh_boot,mh_defaults,mh_load,mh_save,mh_arp_encoder,mh_note_encoder,mh_draw_type,mh_type_format,mh_keyboard

/* One byte per track: bits 0..1 TYPE, bits 2..3 SPRD (0..2). */
mh_get:
    cmpi.l #7,%d0
    bhi.s .get_off
    move.b MH_VERSION,%d1
    cmpi.b #0x4b,%d1
    bne.s .get_off
    lea MH_NV,%a0
    move.b (%a0,%d0.l),%d0
    andi.l #255,%d0
    cmpi.l #11,%d0
    bhi.s .get_off
    andi.l #3,%d0
    rts
.get_off:
    moveq #0,%d0
    rts
mh_set:
    cmpi.l #7,%d0
    bhi.s .set_done
    cmpi.l #3,%d1
    bhi.s .set_done
    lea MH_NV,%a0
    move.l %d2,-(%sp)
    moveq #0,%d2
    move.b (%a0,%d0.l),%d2
    andi.l #12,%d2
    or.l %d2,%d1
    move.l (%sp)+,%d2
    cmp.b (%a0,%d0.l),%d1
    beq.s .set_done
    move.b %d1,(%a0,%d0.l)
    lea mh_voice_history,%a0
    move.l %d0,%d1
    lsl.l #3,%d1
    clr.l 4(%a0,%d1.l)
.set_done:
    rts

/* SPRD CLOSE=0, OPEN=1, WIDE=2, in the existing track byte. */
    .global mh_sprd_get,mh_sprd_set
mh_sprd_get:
    cmpi.l #7,%d0
    bhi.s .sprd_off
    move.b MH_VERSION,%d1
    cmpi.b #0x4b,%d1
    bne.s .sprd_off
    lea MH_NV,%a0
    move.b (%a0,%d0.l),%d0
    andi.l #255,%d0
    cmpi.l #11,%d0
    bhi.s .sprd_off
    lsr.l #2,%d0
    rts
.sprd_off:
    moveq #0,%d0
    rts
mh_sprd_set:
    cmpi.l #7,%d0
    bhi.s .sprd_done
    cmpi.l #2,%d1
    bhi.s .sprd_done
    lea MH_NV,%a0
    move.l %d2,-(%sp)
    moveq #0,%d2
    move.b (%a0,%d0.l),%d2
    andi.l #3,%d2
    lsl.l #2,%d1
    or.l %d2,%d1
    move.l (%sp)+,%d2
    cmp.b (%a0,%d0.l),%d1
    beq.s .sprd_done
    move.b %d1,(%a0,%d0.l)
    lea mh_voice_history,%a0
    lsl.l #3,%d0
    clr.l 4(%a0,%d0.l)
.sprd_done:
    rts

/* One AUTO bit per track; ROOT=0. No new native Part/pattern fields. */
    .global mh_voic_get,mh_voic_set
mh_voic_get:
    cmpi.l #7,%d0
    bhi.s .voic_off
    move.b MH_VERSION,%d1
    cmpi.b #0x4b,%d1
    bne.s .voic_off
    moveq #0,%d1
    move.b MH_VOIC,%d1
    btst %d0,%d1
    beq.s .voic_off
    moveq #1,%d0
    rts
.voic_off:
    moveq #0,%d0
    rts
mh_voic_set:
    cmpi.l #7,%d0
    bhi.s .voic_set_done
    cmpi.l #1,%d1
    bhi.s .voic_set_done
    tst.l %d1
    beq.s .voic_clear_bit
    bset %d0,MH_VOIC
    bra.s .voic_clear_history
.voic_clear_bit:
    bclr %d0,MH_VOIC
.voic_clear_history:
    lea mh_voice_history,%a0
    lsl.l #3,%d0
    clr.l 4(%a0,%d0.l)
.voic_set_done:
    rts

/* Effective native KEY, decoded to key<<2 | mode<<6; -1 for OFF.
 * Standalone Harmony uses stock Major/Minor. MIDI Scales adds five modes.
 */
    .global mh_active,mh_scale_record
mh_scale_record:
    bsr.w mh_source
    move.l %d0,%d1
    lsl.l #6,%d0
    lea 0x46c76df1,%a0
    adda.l %d0,%a0
    moveq #0,%d0
    move.b (%a0,%d1.l*4),%d0
.ifdef HAVE_SCALES
    jmp ms_decode
.else
    tst.l %d0
    beq.s .record_off
    cmpi.l #24,%d0
    bhi.s .record_off
    subq.l #1,%d0
    move.l %d0,%d1
    lsr.l #1,%d0
    lsl.l #2,%d0
    btst #0,%d1
    beq.s .record_done
    ori.l #320,%d0
.record_done:
    rts
.record_off:
    moveq #-1,%d0
    rts
.endif
mh_active:
    lea -8(%sp),%sp
    movem.l %d2-%d3,(%sp)
    move.l %d0,%d2
    bsr.w mh_get
    move.l %d0,%d3
    beq.s .active_done
    move.l %d2,%d0
    bsr.w mh_scale_record
    tst.l %d0
    bpl.s .active_done
    moveq #0,%d3
.active_done:
    move.l %d3,%d0
    movem.l (%sp),%d2-%d3
    lea 8(%sp),%sp
    rts

/* d0 track -> ultimate source, or original track on invalid/cyclic data.
 * Preserves d2+; usable without Follow in the build. */
mh_source:
.ifdef HAVE_FOLLOW
    lea -12(%sp),%sp
    movem.l %d1-%d2/%a0,(%sp)
    move.l %d0,%d2
    moveq #8,%d1
    lea bf_sources,%a0
.source_loop:
    cmpi.l #7,%d0
    bhi.s .source_bad
    tst.b (%a0,%d0.l)
    beq.s .source_done
    move.b (%a0,%d0.l),%d0
    andi.l #255,%d0
    subq.l #1,%d0
    subq.l #1,%d1
    bne.s .source_loop
.source_bad:
    move.l %d2,%d0
.source_done:
    movem.l (%sp),%d1-%d2/%a0
    lea 12(%sp),%sp
.endif
    rts

/* d0 MIDI pitch, d1 track -> d0 snapped pitch, or unchanged if TYPE OFF.
 * All other regs preserved. Nearest degree; exact ties choose lower.
 */
mh_quant:
    lea -28(%sp),%sp
    movem.l %d1-%d5/%a0-%a1,(%sp)
    move.l %d0,%d2
    cmpi.l #127,%d2
    bhi.w .quant_done
    move.l %d1,%d0
    bsr.w mh_active
    beq.w .quant_done
    move.l %d1,%d0  /* d1 was clobbered by getter; reload input track */
    move.l (%sp),%d0
    bsr.w mh_scale_record
    move.l %d0,%d3
    lsr.l #2,%d3
    andi.l #15,%d3
    lsr.l #6,%d0
    lea mh_masks,%a1
    moveq #0,%d4
    move.w (%a1,%d0.l*2),%d4
    moveq #0,%d5
.quant_search:
    move.l %d2,%d0
    sub.l %d5,%d0
    bmi.s .quant_upper
    bsr.s .is_degree
    bne.s .quant_found
.quant_upper:
    move.l %d2,%d0
    add.l %d5,%d0
    cmpi.l #127,%d0
    bhi.s .quant_next
    bsr.s .is_degree
    bne.s .quant_found
.quant_next:
    addq.l #1,%d5
    cmpi.l #12,%d5
    blt.s .quant_search
    bra.s .quant_done
.quant_found:
    move.l %d0,%d2
.quant_done:
    move.l %d2,%d0
    movem.l (%sp),%d1-%d5/%a0-%a1
    lea 28(%sp),%sp
    rts
/* d0 note,d3 tonic,d4 mask -> Z false if degree. */
.is_degree:
    move.l %d0,%d1
    sub.l %d3,%d1
    bpl.s .pc_mod
    addi.l #12,%d1
.pc_mod:
    cmpi.l #12,%d1
    blt.s .pc_test
    subi.l #12,%d1
    bra.s .pc_mod
.pc_test:
    btst %d1,%d4
    rts

/* d0 track, d1 signed transpose, a0 four-byte stock scratch.
 * mh_generate resolves a followed root; mh_direct uses the supplied pitch.
 * Return 0 bypassed, 1 generated, -1 invalid root. Preserve other registers.
 * Transpose first, snap root, then stack scale thirds. Padding duplicates root
 * because stock's arp bitmap requires valid pitches and deduplicates them.
 */
mh_generate:
    lea -40(%sp),%sp
    movem.l %d1-%d7/%a0-%a1,(%sp)
    moveq #1,%d5
    bra.s .gen_start
    .global mh_direct
mh_direct:
    lea -40(%sp),%sp
    movem.l %d1-%d7/%a0-%a1,(%sp)
    moveq #0,%d5
.gen_start:
    move.l %d0,%d7
    move.l %a0,%a1
    bsr.w mh_active
    move.l %d0,%d6
    beq.w .gen_return
    moveq #0,%d2
    move.b (%a1),%d2
    cmpi.l #127,%d2
    bhi.w .gen_invalid
.ifdef HAVE_FOLLOW
    tst.l %d5
    beq.s .gen_own
    move.l %d7,%d0
    bsr.w mh_source
    cmp.l %d7,%d0
    beq.s .gen_own
    lea bf_roots,%a0
    move.b (%a0,%d0.l),%d0
    andi.l #255,%d0
    cmpi.l #127,%d0
    bhi.s .gen_own
    move.l %d0,%d2
.gen_own:
.endif
    add.l (%sp),%d2
    andi.l #255,%d2 /* Same byte arithmetic as stock TRAN/arranger. */
    cmpi.l #127,%d2
    bhi.w .gen_invalid
    move.l %d2,%d0
    move.l %d7,%d1
    bsr.w mh_quant
    move.l %d0,%d2
    move.b %d2,(%a1)
    move.b %d2,1(%a1)
    move.b %d2,2(%a1)
    move.b %d2,3(%a1)
    move.l %d7,%d0
    bsr.w mh_scale_record
    move.l %d0,%d5
    lsr.l #6,%d0
    lea mh_masks,%a0
    moveq #0,%d4
    move.w (%a0,%d0.l*2),%d4
    lsr.l #2,%d5
    andi.l #15,%d5
    /* d2 snapped root, d4 mask, d5 tonic. */
    move.l %d2,%d7
    moveq #1,%d0
    cmpi.l #1,%d6
    beq.s .gen_return
    addq.l #1,%d6
    move.l %d6,36(%sp)
    moveq #1,%d6 /* voice index */
.gen_voice:
    moveq #2,%d3
.gen_degree:
    addq.l #1,%d7
    move.l %d7,%d1
    sub.l %d5,%d1
    bpl.s .gen_mod
    addi.l #12,%d1
.gen_mod:
    cmpi.l #12,%d1
    blt.s .gen_test
    subi.l #12,%d1
    bra.s .gen_mod
.gen_test:
    btst %d1,%d4
    beq.s .gen_degree
    subq.l #1,%d3
    bne.s .gen_degree
    move.l %d7,%d1
    cmpi.l #127,%d1
    bhi.s .gen_end
    move.b %d1,(%a1,%d6.l)
    addq.l #1,%d6
    cmp.l 36(%sp),%d6
    blt.s .gen_voice
.gen_end:
    moveq #1,%d0
    bra.s .gen_return
.gen_invalid:
    clr.l (%a1) /* Safe bitmap input; sequence output is muted below. */
    moveq #-1,%d0
.gen_return:
    movem.l (%sp),%d1-%d7/%a0-%a1
    lea 40(%sp),%sp
    rts

mh_sequence:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    moveq #0,%d1
    move.b 0x22c(%a5),%d1
    subi.l #64,%d1
    lea 0x46c7a124,%a0
    moveq #0,%d0
    move.b (%a0,%d7.l),%d0
    add.l %d0,%d1
    move.l %d7,%d0
    lea -4(%fp),%a0
    bsr.w mh_generate
    tst.l %d0
    ble.s .sequence_not_voiced
    move.l %d0,-(%sp)
    move.l %d7,%d0
    bsr.w mh_voice
    move.l (%sp)+,%d0
.sequence_not_voiced:
    lea mh_muted,%a0
    clr.b (%a0,%d7.l)
    tst.l %d0
    bpl.s .sequence_ready
    moveq #1,%d0
    move.b %d0,(%a0,%d7.l)
.sequence_ready:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    move.l %fp,%d2
    subq.l #4,%d2
    move.l %d2,-(%sp)
    jmp 0x4009fa30

    .balign 2
mh_masks:
    .word 0xab5,0x6ad,0x5ab,0xad5,0x6b5,0x5ad,0x56b

/* Harmony replaces native key correction with its effective scale. */
    .global mh_scale
mh_scale:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    move.l %d7,%d0
    bsr.w mh_active
    beq.s .scale_stock
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    jmp 0x4009fad8
.scale_stock:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    move.b 49(%a0),%d0
    beq.s .scale_zero
    jmp 0x4009fade
.scale_zero:
    jmp 0x4009fad8

/* Follow captures raw NOTE + TRAN before snapping, in every HARM mode. */
    .global mh_prepare
mh_prepare:
    rts

/* Final correction also keeps stock arp step offsets inside the scale. */
    .global mh_final,mh_output
mh_final:
    jmp mh_quant

/* Harmony's arp pool already contains transposed, scale-built pitches.
 * Live pools contain the player's absolute pitches. Neither is transposed
 * again. OFF/KEY OFF replay stock arithmetic. Invalid sequenced roots are
 * muted after safely initializing the arp; live keyboard pools remain usable.
 */
    .global mh_transpose
mh_transpose:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    move.l %d7,%d0
    bsr.w mh_active
    beq.s .transpose_stock
    move.l %d7,%d0
    lsl.l #3,%d0
    lea 0x46c77b1e,%a0
    adda.l %d0,%a0
    move.l %d7,%d0
    add.l %d0,%d0
    move.b (%a0,%d0.l),%d0
    cmpi.b #1,%d0
    beq.s .transpose_ready
    lea mh_muted,%a0
    tst.b (%a0,%d7.l)
    bne.s .transpose_muted
.transpose_ready:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    jmp 0x4009fb58
.transpose_muted:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    jmp 0x4009fd2a
.transpose_stock:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    move.b 0x22c(%a5),%d0
    move.l %d1,%a1
    jmp 0x4009fb40

/* After stock transpose/scale and optional Follow, before note ownership. */
mh_output:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    moveq #0,%d0
    move.b (%a2),%d0
    move.l %d7,%d1
    bsr.w mh_final
    move.b %d0,(%a2)
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    move.b (%a2),%d1
    move.b %d1,%d3
    extb.l %d3
    move.l %d6,%d0
    add.l %d3,%d0
    jmp 0x4009fb8c

mh_reset:
    lea MH_NV,%a0
    clr.l (%a0)
    clr.l 4(%a0)
    clr.b 8(%a0)
    moveq #0x4b,%d0
    move.b %d0,MH_VERSION
    jsr mh_voice_clear
    rts
mh_defaults:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    bsr.s mh_reset
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    clr.l 0x100b14d8
    jmp 0x40025ace
mh_boot:
    lea -16(%sp),%sp
    movem.l %d0-%d2/%a0,(%sp)
    move.b MH_VERSION,%d1
    cmpi.b #0x4b,%d1
    beq.s .boot_valid
    cmpi.b #0x4a,%d1 /* Previous TYPE/VOIC layout: preserve, add CLOSE. */
    bne.s .boot_reset
    lea MH_NV,%a0
    moveq #8,%d2
.boot_migrate:
    move.b (%a0),%d1
    cmpi.b #3,%d1
    bls.s .boot_migrate_next
    clr.b (%a0)
.boot_migrate_next:
    addq.l #1,%a0
    subq.l #1,%d2
    bne.s .boot_migrate
    moveq #0x4b,%d1
    move.b %d1,MH_VERSION
    bra.s .boot_valid
.boot_reset:
    bsr.w mh_reset
.boot_valid:
    moveq #0,%d2
.boot_track:
    move.l %d2,%d0
    lea MH_NV,%a0
    move.b (%a0,%d2.l),%d1
    cmpi.b #11,%d1
    bls.s .boot_next
    clr.b (%a0,%d2.l)
.boot_next:
    addq.l #1,%d2
    cmpi.l #8,%d2
    bne.s .boot_track
    jsr mh_voice_clear
    movem.l (%sp),%d0-%d2/%a0
    lea 16(%sp),%sp
    move.b 0x100b14ae,%d0
    extb.l %d0
    jmp 0x4001022a

/* Comments are ignored by stock firmware. Parse-only passes never write.
 * Adjacent, non-overlapping hooks coexist with Quantizer's project hooks.
 */
mh_load:
    cmpi.l #35,%d0
    bne.w .load_stock
    lea -32(%sp),%sp
    movem.l %d0-%d3/%d5/%a0-%a1,(%sp)
    clr.l 28(%sp) /* 0=TYPE comment, 1=VOIC comment, 2=SPRD comment */
    move.l %d3,%a0
    lea mh_key,%a1
.load_prefix:
    moveq #0,%d0
    move.b (%a1)+,%d0
    beq.s .load_track
    cmp.b (%a0)+,%d0
    bne.s .load_other_prefix
    bra.s .load_prefix
.load_other_prefix:
    addq.l #1,28(%sp)
    move.l 28(%sp),%d5
    cmpi.l #2,%d5
    bhi.w .load_done
    move.l %d3,%a0
    lea mh_voic_key,%a1
    bne.s .load_prefix
    lea mh_sprd_key,%a1
    bra.s .load_prefix
.load_track:
    moveq #0,%d2
    move.b (%a0)+,%d2
    subi.l #49,%d2
    cmpi.l #7,%d2
    bhi.w .load_done
    move.b (%a0)+,%d0
    cmpi.b #61,%d0
    bne.s .load_done
    moveq #0,%d1
    moveq #0,%d3
.load_digit:
    moveq #0,%d0
    move.b (%a0)+,%d0
    subi.l #48,%d0
    cmpi.l #9,%d0
    bhi.s .load_end
    addq.l #1,%d3
    cmpi.l #3,%d3
    bhi.s .load_done
    move.l %d1,%d5
    lsl.l #2,%d1
    add.l %d5,%d1
    add.l %d1,%d1
    add.l %d0,%d1
    bra.s .load_digit
.load_end:
    tst.l %d3
    beq.s .load_done
    addi.l #48,%d0
    beq.s .load_validate
    cmpi.l #13,%d0
    beq.s .load_validate
    cmpi.l #10,%d0
    bne.s .load_done
.load_validate:
    cmpi.l #3,%d1
    bhi.s .load_done
    tst.l 90(%sp) /* loader's parse-only flag at original sp+58 */
    bne.s .load_done
    move.l %d2,%d0
    tst.l 28(%sp)
    beq.s .load_type
    move.l 28(%sp),%d5
    cmpi.l #2,%d5
    beq.s .load_sprd
    bsr.w mh_voic_set /* independently validates 0..1 */
    bra.s .load_done
.load_sprd:
    bsr.w mh_sprd_set /* independently validates 0..2 */
    bra.s .load_done
.load_type:
    bsr.w mh_set
.load_done:
    movem.l (%sp),%d0-%d3/%d5/%a0-%a1
    lea 32(%sp),%sp
    jmp 0x40088224
.load_stock:
    cmp.l %d0,%d5
    beq.s .load_comment
    jmp 0x400867b0
.load_comment:
    jmp 0x40088224

mh_save:
    move.l %d7,-(%sp)
    moveq #0,%d7
.save_track:
    move.l %d7,%d0
    bsr.w mh_get
    move.l %d0,-(%sp)
    move.l %d7,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea mh_fmt
    move.l %d2,-(%sp)
    jsr (%a4)
    move.l %d2,-(%sp)
    jsr (%a3)
    move.l %d0,-(%sp)
    move.l %d2,-(%sp)
    move.l %d3,-(%sp)
    jsr (%a2)
    lea 32(%sp),%sp
    tst.l %d0
    bmi.w .save_fail
    move.l %d7,%d0
    bsr.w mh_voic_get
    move.l %d0,-(%sp)
    move.l %d7,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea mh_voic_fmt
    move.l %d2,-(%sp)
    jsr (%a4)
    move.l %d2,-(%sp)
    jsr (%a3)
    move.l %d0,-(%sp)
    move.l %d2,-(%sp)
    move.l %d3,-(%sp)
    jsr (%a2)
    lea 32(%sp),%sp
    tst.l %d0
    bmi.w .save_fail
    move.l %d7,%d0
    bsr.w mh_sprd_get
    move.l %d0,-(%sp)
    move.l %d7,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea mh_sprd_fmt
    move.l %d2,-(%sp)
    jsr (%a4)
    move.l %d2,-(%sp)
    jsr (%a3)
    move.l %d0,-(%sp)
    move.l %d2,-(%sp)
    move.l %d3,-(%sp)
    jsr (%a2)
    lea 32(%sp),%sp
    tst.l %d0
    bmi.w .save_fail
    addq.l #1,%d7
    cmpi.l #8,%d7
    bne.w .save_track
    move.l (%sp)+,%d7
    move.b 0x8000004e,%d0
    extb.l %d0
    jmp 0x40088888
.save_fail:
    move.l (%sp)+,%d7
    jmp 0x40089638
mh_key: .asciz "#MIDI_HARMONY_TYPE_V1_T"
mh_fmt: .asciz "#MIDI_HARMONY_TYPE_V1_T%d=%d\r\n"
mh_sprd_key: .asciz "#MIDI_HARMONY_SPRD_V1_T"
mh_sprd_fmt: .asciz "#MIDI_HARMONY_SPRD_V1_T%d=%d\r\n"
mh_voic_key: .asciz "#MIDI_HARMONY_VOIC_V1_T"
mh_voic_fmt: .asciz "#MIDI_HARMONY_VOIC_V1_T%d=%d\r\n"
    .balign 2
/* NOTE SETUP F TYPE. Follow's shared callback forwards every non-D knob
 * here; without Follow the stock callback pointer already names this entry.
 */
mh_note_encoder:
    move.l 4(%sp),%d0
    cmpi.l #5,%d0
    beq.s .type_ours
    lea -16(%sp),%sp
    movem.l %d2-%d3/%a2-%a3,(%sp)
    jmp 0x4003a8f0
.type_ours:
    move.l %d2,-(%sp)
    moveq #0,%d2
    move.b 0x100b14cc,%d2
    move.l %d2,%d0
    bsr.w mh_get
    move.l 12(%sp),%d1
    cmpi.l #3,%d1
    ble.s .type_delta_low
    moveq #3,%d1
.type_delta_low:
    cmpi.l #-3,%d1
    bge.s .type_add
    moveq #-3,%d1
.type_add:
    add.l %d1,%d0
    bpl.s .type_max
    moveq #0,%d0
.type_max:
    cmpi.l #3,%d0
    ble.s .type_set
    moveq #3,%d0
.type_set:
    move.l %d0,%d1
    move.l %d2,%d0
    bsr.w mh_set
    move.l (%sp)+,%d2
    jmp 0x40036548

mh_draw_type:
    cmpi.l #5,%d4
    bne.s .draw_type_done
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    moveq #0,%d0
    move.b 0x100b14cc,%d0
    bsr.w mh_get
    move.l %d0,%d3
    move.l %d3,60(%sp) /* compare to own value, never a pending Part edit */
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
.draw_type_done:
    move.l %d1,%d0
    lsl.l #4,%d0
    move.l %d0,%a0
    jmp 0x40036688
mh_type_format:
    move.l 4(%sp),%a0
    move.l 8(%sp),%d0
    cmpi.l #3,%d0
    bls.s .type_format_ok
    moveq #0,%d0
.type_format_ok:
    lea mh_types,%a1
    move.l (%a1,%d0.l*4),%a1
.type_copy:
    move.b (%a1)+,(%a0)+
    bne.s .type_copy
    rts
    .balign 4
mh_types: .long .off,.note,.triad,.seventh
.off: .asciz "OFF"
.note: .asciz "NOTE"
.triad: .asciz "TRI"
.seventh: .asciz "7TH"
    .balign 2

/* No new controls on ARP SETUP. Its native KEY is read-only on followers. */
mh_arp_encoder:
    move.l 4(%sp),%d0
    cmpi.l #5,%d0
    bne.s .arp_native
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    moveq #0,%d0
    move.b 0x100b14cc,%d0
    move.l %d0,%d1
    bsr.w mh_source
    cmp.l %d1,%d0
    beq.s .arp_local
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    jmp 0x40079d48
.arp_local:
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
.arp_native:
    lea -36(%sp),%sp
    movem.l %d2-%d7/%a2-%a4,(%sp)
    jmp 0x4007a2f4

/* Live keyboard: remember generated notes per physical pitch until release.
 * Shared chord tones are reference-counted, so releasing one key cannot stop
 * a tone still held by another. Changes to TYPE/KEY/SCALE never change offs.
 * Stock keeps channel/note ownership and handles arp insertion/removal.
 */
mh_keyboard:
    lea -44(%sp),%sp
    movem.l %d2-%d7/%a2-%a5,(%sp)
    move.l 48(%sp),%d2 /* track */
    move.l 52(%sp),%d3 /* physical pitch */
    move.l 56(%sp),%d4 /* velocity */
    move.l 60(%sp),%d5 /* recorder flag */
    cmpi.l #7,%d2
    bhi.w .keyboard_stock
    cmpi.l #127,%d3
    bhi.w .keyboard_stock
    move.l %d2,%d0
    lsl.l #7,%d0
    add.l %d3,%d0
    lea mh_held,%a3
    lea (%a3,%d0.l*4),%a3
    move.l %d2,%d0
    lsl.l #7,%d0
    lea mh_refs,%a4
    adda.l %d0,%a4
    move.l (%a3),%d0
    cmpi.l #0xfeffffff,%d0 /* This key was pressed while Harmony was bypassed. */
    beq.w .keyboard_was_stock
    cmpi.l #-1,%d0
    beq.s .keyboard_new
    bsr.w mh_release
    tst.l %d4
    beq.w .keyboard_done
.keyboard_new:
    move.l %d2,%d0
    bsr.w mh_active
    beq.w .keyboard_passthrough
    move.l %d0,%d6
    tst.l %d4
    beq.w .keyboard_done
    lea 40(%sp),%a2
    move.b %d3,(%a2)
    /* All keyboard modes choose an absolute root and inherit only scale. */
    move.l %d2,%d0
    moveq #0,%d1
    move.l %a2,%a0
    bsr.w mh_direct
.ifdef HAVE_FOLLOW
    moveq #0,%d0
    move.b (%a2),%d0
    move.l %d2,%d1
    bsr.w mh_final
    cmpi.l #127,%d0
    bhi.s .keyboard_no_root
.keyboard_mod:
    cmpi.l #12,%d0
    blt.s .keyboard_latch
    subi.l #12,%d0
    bra.s .keyboard_mod
.keyboard_latch:
    addi.l #36,%d0
    lea bf_roots,%a1
    move.b %d0,(%a1,%d2.l)
.keyboard_no_root:
.endif
    /* The root latch above must see the musical root, never the inversion. */
    move.l %d2,%d0
    move.l %a2,%a0
    bsr.w mh_voice
    /* Record the physical key once, independently of snapping/live voices. */
    move.l %d5,-(%sp)
    move.l %d4,-(%sp)
    move.l %d3,-(%sp)
    move.l %d2,-(%sp)
    bsr.w mh_record_key
    lea 16(%sp),%sp
    moveq #0,%d6
.keyboard_voice:
    moveq #0,%d0
    move.b (%a2,%d6.l),%d0
    move.l %d2,%d1
    bsr.w mh_final
    moveq #-1,%d1
    move.b %d1,(%a3,%d6.l)
    cmpi.l #127,%d0
    bhi.s .keyboard_next
    /* Deduplicate the generator's padding; count only one owner per key. */
    moveq #0,%d1
.keyboard_duplicate:
    cmp.l %d6,%d1
    beq.s .keyboard_send
    cmp.b (%a3,%d1.l),%d0
    beq.s .keyboard_next
    addq.l #1,%d1
    bra.s .keyboard_duplicate
.keyboard_send:
    move.b %d0,(%a3,%d6.l)
    moveq #0,%d1
    move.b (%a4,%d0.l),%d1
    addq.l #1,%d1
    move.b %d1,(%a4,%d0.l)
    cmpi.b #1,%d1
    bne.s .keyboard_next
    clr.l -(%sp) /* Generated voices sound, but never enter the recorder. */
    move.l %d4,-(%sp)
    move.l %d0,-(%sp)
    move.l %d2,-(%sp)
    bsr.w mh_stock_key
    lea 16(%sp),%sp
.keyboard_next:
    addq.l #1,%d6
    cmpi.l #4,%d6
    bne.w .keyboard_voice
    bra.s .keyboard_done
.keyboard_was_stock:
    moveq #-1,%d0
    move.l %d0,(%a3)
    tst.l %d4
    beq.s .keyboard_stock
    move.l %d2,%d0
    bsr.w mh_active
    beq.s .keyboard_passthrough
    /* Repeated press: release the old stock note before changing ownership. */
    move.l %d5,-(%sp)
    clr.l -(%sp)
    move.l %d3,-(%sp)
    move.l %d2,-(%sp)
    bsr.w mh_stock_key
    lea 16(%sp),%sp
    bra.w .keyboard_new
.keyboard_passthrough:
    tst.l %d4
    beq.s .keyboard_stock
    move.l #0xfeffffff,(%a3)
    bra.s .keyboard_stock
.keyboard_done:
    movem.l (%sp),%d2-%d7/%a2-%a5
    lea 44(%sp),%sp
    rts
.keyboard_stock:
    movem.l (%sp),%d2-%d7/%a2-%a5
    lea 44(%sp),%sp
mh_stock_key:
    lea -28(%sp),%sp
    movem.l %d2-%d7/%a2,(%sp)
    jmp 0x4009e9b0
/* Stock recorder tail, without transmitting or owning a MIDI voice.
 * Same four arguments and saved-register frame as mh_stock_key. Resolve
 * the native Part channel exactly as 0x4009e9c0..0x4009e9f8, then enter its
 * recorder handoff. Additional chord voices must not enqueue more roots.
 */
    .global mh_record_key
mh_record_key:
    lea -28(%sp),%sp
    movem.l %d2-%d7/%a2,(%sp)
    move.l 44(%sp),%d7
    tst.l %d7
    beq.s .record_key_done
    move.l 32(%sp),%d5
    move.l 36(%sp),%d3
    move.l 40(%sp),%d6
    move.l 0x46c82456,%a1
    moveq #0,%d0
    move.b 0x100b14cf,%d0
    move.l %d5,%d1
    lsl.l #5,%d1
    move.l %d1,%a2
    lea (%a2,%d5.l*4),%a0
    move.l #0x18b2,%d2
    muls.l %d2,%d0
    adda.l %d0,%a0
    lea (%a1,%a0.l),%a0
    adda.l #0x8f262,%a0
    moveq #0,%d4
    move.b (%a0),%d4
    beq.s .record_key_handoff /* Stock permits recording with CHAN OFF. */
    subq.l #1,%d4
    andi.l #15,%d4
.record_key_handoff:
    jmp 0x4009eb7a
.record_key_done:
    movem.l (%sp),%d2-%d7/%a2
    lea 28(%sp),%sp
    rts

mh_release:
    moveq #0,%d0
    move.b (%a3),%d0
    cmpi.l #127,%d0
    bhi.s .release_begin
    move.l %d5,-(%sp)
    clr.l -(%sp)
    move.l %d3,-(%sp) /* Same physical pitch as the recorder note-on. */
    move.l %d2,-(%sp)
    bsr.w mh_record_key
    lea 16(%sp),%sp
.release_begin:
    moveq #0,%d6
.release_voice:
    moveq #0,%d0
    move.b (%a3,%d6.l),%d0
    cmpi.l #127,%d0
    bhi.s .release_next
    moveq #-1,%d1
    move.b %d1,(%a3,%d6.l)
    tst.b (%a4,%d0.l)
    beq.s .release_next
    moveq #0,%d1
    move.b (%a4,%d0.l),%d1
    subq.l #1,%d1
    move.b %d1,(%a4,%d0.l)
    bne.s .release_next
    clr.l -(%sp) /* Recorder release was emitted once, above. */
    clr.l -(%sp)
    move.l %d0,-(%sp)
    move.l %d2,-(%sp)
    bsr.w mh_stock_key
    lea 16(%sp),%sp
.release_next:
    addq.l #1,%d6
    cmpi.l #4,%d6
    bne.s .release_voice
    rts
    .balign 4
mh_muted: .space 8,0
mh_held: .space 4096,255
mh_refs: .space 1024,0


    .global mh_draw_key
mh_draw_key:
    move.b (%a0),%d4
    cmpi.l #5,%d3
    bne.s .draw_key_done
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    moveq #0,%d0
    move.b 0x100b14cc,%d0
    bsr.w mh_source
    move.l %d0,%d1
    lsl.l #6,%d0
    lea 0x46c76df1,%a0
    adda.l %d0,%a0
    move.b (%a0,%d1.l*4),%d4
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
.draw_key_done:
    move.l %d3,%d0
    moveq #3,%d2
    jmp 0x4007a1b6
