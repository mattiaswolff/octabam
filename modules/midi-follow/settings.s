/* Project-scoped Follow configuration. Stock-compatible project comments.
 * CS1 0x100f85e8..0x100f8600: 24-byte gap after KITS, before CHRD/PLOCKS P2.
 * See docs/firmware/STEP_LOCKS.md: stock leaves this tail alone except init.
 * magic + eight packed words + checksum. Publish magic last; no roots/voices.
 * Packed V1: source[3:0], mode[4], fixed[8:5], (source offset + 2)[11:9].
 */
    .text
    .global bf_pack,bf_unpack,bf_reset,bf_persist,bf_restore
    .global bf_load,bf_save,bf_defaults,bf_boot
    .set BF_NV,0x100f85e8
    .set BF_MAGIC,0x42465031

/* d0 track -> d0 packed value. Caller supplies a valid track. */
bf_pack:
    lea -12(%sp),%sp
    movem.l %d1-%d2/%a0,(%sp)
    move.l %d0,%d2
    lea bf_reg_offsets,%a0
    move.b (%a0,%d2.l),%d0
    extb.l %d0
    addq.l #2,%d0
    lsl.l #4,%d0
    lea bf_reg_fixed,%a0
    moveq #0,%d1
    move.b (%a0,%d2.l),%d1
    or.l %d1,%d0
    add.l %d0,%d0
    lea bf_reg_modes,%a0
    move.b (%a0,%d2.l),%d1
    or.l %d1,%d0
    lsl.l #4,%d0
    lea bf_sources,%a0
    move.b (%a0,%d2.l),%d1
    or.l %d1,%d0
    movem.l (%sp),%d1-%d2/%a0
    lea 12(%sp),%sp
    rts

/* d0 track, d1 packed -> d0 success. Validate every field and routing cycle
 * before publishing any byte. No dependence on project line order. */
bf_unpack:
    lea -24(%sp),%sp
    movem.l %d2-%d5/%a0-%a1,(%sp)
    move.l %d0,%d2
    move.l %d1,%d3
    moveq #0,%d0
    cmpi.l #7,%d2
    bhi.w .unpack_done
    cmpi.l #4095,%d3
    bhi.w .unpack_done
    move.l %d3,%d4
    lsr.l #8,%d4
    lsr.l #1,%d4
    cmpi.l #4,%d4
    bhi.w .unpack_done
    move.l %d3,%d5
    lsr.l #5,%d5
    andi.l #15,%d5
    cmpi.l #10,%d5
    bhi.w .unpack_done
    move.l %d3,%d1
    andi.l #15,%d1
    cmpi.l #8,%d1
    bhi.w .unpack_done
    lea bf_sources,%a0
    moveq #8,%d5
.cycle:
    tst.l %d1
    beq.s .unpack_store
    subq.l #1,%d1
    cmp.l %d2,%d1
    beq.w .unpack_done
    cmpi.l #7,%d1
    bhi.w .unpack_done
    move.b (%a0,%d1.l),%d1
    andi.l #255,%d1
    subq.l #1,%d5
    bne.s .cycle
    bra.w .unpack_done
.unpack_store:
    move.l %d3,%d1
    andi.l #15,%d1
    move.b %d1,(%a0,%d2.l)
    move.l %d3,%d1
    lsr.l #4,%d1
    andi.l #1,%d1
    lea bf_reg_modes,%a0
    move.b %d1,(%a0,%d2.l)
    move.l %d3,%d1
    lsr.l #5,%d1
    andi.l #15,%d1
    lea bf_reg_fixed,%a0
    move.b %d1,(%a0,%d2.l)
    subq.l #2,%d4
    lea bf_reg_offsets,%a0
    move.b %d4,(%a0,%d2.l)
    moveq #1,%d0
.unpack_done:
    movem.l (%sp),%d2-%d5/%a0-%a1
    lea 24(%sp),%sp
    rts

/* Reset configuration and runtime root/response history at project boundaries.
 * Stock owns sounding-note releases; never restore or clear its voice records. */
bf_reset:
    lea -12(%sp),%sp
    movem.l %d0-%d1/%a0,(%sp)
    lea bf_sources,%a0
    clr.l (%a0)
    clr.l 4(%a0)
    lea bf_reg_modes,%a0
    clr.l (%a0)
    clr.l 4(%a0)
    lea bf_reg_fixed,%a0
    move.l #0x03030303,%d0
    move.l %d0,(%a0)
    move.l %d0,4(%a0)
    lea bf_reg_offsets,%a0
    clr.l (%a0)
    clr.l 4(%a0)
    lea bf_roots,%a0
    moveq #-1,%d0
    move.l %d0,(%a0)
    move.l %d0,4(%a0)
    lea bf_pitches,%a0
    move.l %d0,(%a0)
    move.l %d0,4(%a0)
    moveq #7,%d1
.reset_response:
    lea bf_response_anchor,%a0
    move.l %d0,(%a0,%d1.l*4)
    lea bf_response_seen,%a0
    move.l %d0,(%a0,%d1.l*4)
    lea bf_response_pool,%a0
    move.l %d0,(%a0,%d1.l*4)
    subq.l #1,%d1
    bpl.s .reset_response
    movem.l (%sp),%d0-%d1/%a0
    lea 12(%sp),%sp
    rts

/* FNV-1a over the sixteen payload bytes. */
.checksum:
    lea BF_NV+4,%a0
    move.l #0x811c9dc5,%d0
    moveq #15,%d2
.checksum_byte:
    moveq #0,%d1
    move.b (%a0)+,%d1
    eor.l %d1,%d0
    move.l #0x01000193,%d1
    mulu.l %d1,%d0
    subq.l #1,%d2
    bpl.s .checksum_byte
    rts

bf_persist:
    lea -24(%sp),%sp
    movem.l %d0-%d3/%a0-%a1,(%sp)
    clr.l BF_NV
    lea BF_NV+4,%a1
    moveq #0,%d3
.persist_track:
    move.l %d3,%d0
    bsr.w bf_pack
    move.w %d0,(%a1)+
    addq.l #1,%d3
    cmpi.l #8,%d3
    bne.s .persist_track
    bsr.s .checksum
    move.l %d0,BF_NV+20
    move.l #BF_MAGIC,%d0
    move.l %d0,BF_NV
    movem.l (%sp),%d0-%d3/%a0-%a1
    lea 24(%sp),%sp
    rts

bf_restore:
    lea -24(%sp),%sp
    movem.l %d0-%d3/%a0-%a1,(%sp)
    bsr.w bf_reset
    move.l BF_NV,%d0
    cmpi.l #BF_MAGIC,%d0
    bne.s .restore_done
    bsr.w .checksum
    cmp.l BF_NV+20,%d0
    bne.s .restore_done
    lea BF_NV+4,%a1
    moveq #0,%d3
.restore_track:
    move.l %d3,%d0
    moveq #0,%d1
    move.w (%a1)+,%d1
    bsr.w bf_unpack
    addq.l #1,%d3
    cmpi.l #8,%d3
    bne.s .restore_track
.restore_done:
    bsr.w bf_persist
    movem.l (%sp),%d0-%d3/%a0-%a1
    lea 24(%sp),%sp
    rts

bf_defaults:
    bsr.w bf_reset
    bsr.w bf_persist
    move.b %d0,0x100b14dc
    jmp 0x40025ad4
bf_boot:
    bsr.w bf_restore
    tst.b 0x100b14af
    jmp 0x40010240

/* Before the other modules' comment readers. The strlen argument is still
 * on the stack at the hook; pop it exactly as stock, even for empty lines. */
bf_load:
    addq.l #4,%sp
    tst.l %d0
    ble.w .load_empty
    lea -28(%sp),%sp
    movem.l %d0-%d4/%a0-%a1,(%sp)
    move.l %d3,%a0
    lea .key,%a1
.prefix:
    moveq #0,%d0
    move.b (%a1)+,%d0
    beq.s .load_track
    cmp.b (%a0)+,%d0
    bne.w .load_done
    bra.s .prefix
.load_track:
    moveq #0,%d2
    move.b (%a0)+,%d2
    subi.l #49,%d2
    cmpi.l #7,%d2
    bhi.w .load_done
    move.b (%a0)+,%d0
    cmpi.b #61,%d0
    bne.w .load_done
    moveq #0,%d1
    moveq #0,%d3
.digit:
    moveq #0,%d0
    move.b (%a0)+,%d0
    subi.l #48,%d0
    cmpi.l #9,%d0
    bhi.s .end_digits
    addq.l #1,%d3
    cmpi.l #4,%d3
    bhi.s .load_done
    moveq #10,%d4
    mulu.l %d4,%d1
    add.l %d0,%d1
    bra.s .digit
.end_digits:
    tst.l %d3
    beq.s .load_done
    addi.l #48,%d0
    beq.s .load_value
    cmpi.l #13,%d0
    beq.s .load_value
    cmpi.l #10,%d0
    bne.s .load_done
.load_value:
    tst.l 86(%sp) /* original storing/parse-only flag at sp+58 */
    bne.s .load_done
    move.l %d2,%d0
    bsr.w bf_unpack
    tst.l %d0
    beq.s .load_done
    bsr.w bf_persist
.load_done:
    movem.l (%sp),%d0-%d4/%a0-%a1
    lea 28(%sp),%sp
    jmp 0x400867a2
.load_empty:
    jmp 0x40088232

bf_save:
    move.l %d7,-(%sp)
    moveq #0,%d7
.save_track:
    move.l %d7,%d0
    bsr.w bf_pack
    move.l %d0,-(%sp)
    move.l %d7,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea .format
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
    bmi.s .save_fail
    addq.l #1,%d7
    cmpi.l #8,%d7
    bne.s .save_track
    move.l (%sp)+,%d7
    move.b 0x8000004d,%d1
    extb.l %d1
    jmp 0x40088860
.save_fail:
    move.l (%sp)+,%d7
    jmp 0x40089638
.key: .asciz "#MIDI_FOLLOW_V1_T"
.format: .asciz "#MIDI_FOLLOW_V1_T%d=%d\r\n"
    .balign 4
