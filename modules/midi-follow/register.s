/* Receiver register policy. Project-scoped per-track settings, like RFOL.
 * Keep absolute source pitches independently of the historical bass latch.
 * Register selection precedes receiver TRAN and Harmony root snapping.
 */
    .text
    .global bf_register,bf_reg_change,bf_mode_get,bf_oct_get
    .global bf_reg_modes,bf_reg_fixed,bf_reg_offsets
/* d0=ultimate source track, d1=receiver -> d0=signed pitch or 256 (unknown).
 * A relative octave can temporarily go outside MIDI; TRAN may bring it back.
 * All other registers are preserved; callers validate after adding TRAN.
 */
bf_register:
    lea -16(%sp),%sp
    movem.l %d1-%d3/%a0,(%sp)
    cmpi.l #7,%d0
    bhi.w .reg_unknown
    cmpi.l #7,%d1
    bhi.w .reg_unknown
    lea bf_reg_modes,%a0
    move.b (%a0,%d1.l),%d3
    cmpi.b #1,%d3
    beq.s .reg_source
    lea bf_roots,%a0
    moveq #0,%d2
    move.b (%a0,%d0.l),%d2
    cmpi.l #127,%d2
    bhi.w .reg_unknown
    subi.l #36,%d2
    lea bf_reg_fixed,%a0
    moveq #0,%d0
    move.b (%a0,%d1.l),%d0
    cmpi.l #10,%d0
    bls.s .reg_octave
    moveq #3,%d0
    bra.s .reg_octave
.reg_source:
    lea bf_pitches,%a0
    moveq #0,%d2
    move.b (%a0,%d0.l),%d2
    cmpi.l #127,%d2
    bhi.w .reg_unknown
    lea bf_reg_offsets,%a0
    move.b (%a0,%d1.l),%d0
    extb.l %d0
    cmpi.l #-2,%d0
    blt.s .reg_offset_bad
    cmpi.l #2,%d0
    ble.s .reg_octave
.reg_offset_bad:
    moveq #0,%d0
.reg_octave:
    moveq #12,%d3
    muls.l %d3,%d0
    add.l %d2,%d0
    bra.s .reg_return
.reg_unknown:
    move.l #256,%d0
.reg_return:
    movem.l (%sp),%d1-%d3/%a0
    lea 16(%sp),%sp
    rts

/* UI getters: d0 track -> value. d1/a0 scratch only. */
bf_mode_get:
    cmpi.l #7,%d0
    bhi.s .mode_default
    lea bf_reg_modes,%a0
    move.b (%a0,%d0.l),%d0
    andi.l #255,%d0
    cmpi.l #1,%d0
    bls.s .mode_done
.mode_default:
    moveq #0,%d0
.mode_done:
    rts
bf_oct_get:
    cmpi.l #7,%d0
    bhi.s .oct_default
    move.l %d0,%d1
    bsr.s bf_mode_get
    tst.l %d0
    bne.s .oct_relative
    lea bf_reg_fixed,%a0
    moveq #0,%d0
    move.b (%a0,%d1.l),%d0
    cmpi.l #10,%d0
    bls.s .oct_done
.oct_default:
    moveq #3,%d0
    rts
.oct_relative:
    lea bf_reg_offsets,%a0
    move.b (%a0,%d1.l),%d0
    extb.l %d0
.oct_done:
    rts

/* d0 track, d1 control (0 mode, 1 octave), d2 signed delta.
 * Independent fixed/relative values survive mode switches. Preserve all regs.
 */
bf_reg_change:
    lea -28(%sp),%sp
    movem.l %d0-%d5/%a0,(%sp)
    cmpi.l #7,%d0
    bhi.w .change_done
    cmpi.l #1,%d1
    bhi.w .change_done
    move.l %d0,%d3
    moveq #0,%d4
    moveq #1,%d5
    lea bf_reg_modes,%a0
    tst.l %d1
    beq.s .change_unsigned
    bsr.w bf_mode_get
    tst.l %d0
    bne.s .change_relative
    lea bf_reg_fixed,%a0
    moveq #10,%d5
.change_unsigned:
    moveq #0,%d0
    move.b (%a0,%d3.l),%d0
    bra.s .change_clamp
.change_relative:
    lea bf_reg_offsets,%a0
    moveq #-2,%d4
    moveq #2,%d5
    move.b (%a0,%d3.l),%d0
    extb.l %d0
.change_clamp:
    cmpi.l #16,%d2
    ble.s .change_low_delta
    moveq #16,%d2
.change_low_delta:
    cmpi.l #-16,%d2
    bge.s .change_add
    moveq #-16,%d2
.change_add:
    add.l %d2,%d0
    cmp.l %d4,%d0
    bge.s .change_max
    move.l %d4,%d0
.change_max:
    cmp.l %d5,%d0
    ble.s .change_store
    move.l %d5,%d0
.change_store:
    move.b %d0,(%a0,%d3.l)
    jsr bf_persist
.change_done:
    movem.l (%sp),%d0-%d5/%a0
    lea 28(%sp),%sp
    rts
    .balign 4
bf_reg_modes: .space 8,0
bf_reg_fixed: .space 8,3
bf_reg_offsets: .space 8,0
