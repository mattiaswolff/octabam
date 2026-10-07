/* RFOL D press: receiver MODE and OCT. Native modal/input-layer pattern.
 * Transport/chromatic keys pass through; settings affect subsequent trigs. */
    .text
    .global bf_page_open,bf_page_close,bf_page_noop,bf_page_encoder
    .global bf_page_win,bf_page_track,bf_page_draw
bf_page_open:
    tst.l bf_page_win
    bne.w bf_page_close
    moveq #0,%d0
    move.b 0x100b14cc,%d0
    cmpi.l #7,%d0
    bhi.s bf_page_noop
    move.l %d0,bf_page_track
    pea bf_page_close
    pea 5 /* stock modal class, shared with TEMPO/Tuner */
    clr.l -(%sp)
    clr.l -(%sp)
    pea 60
    pea 120
    jsr 0x4005829c
    lea 24(%sp),%sp
    move.l %d0,bf_page_win
    beq.s bf_page_noop
    move.l %d0,-(%sp)
    jsr 0x40056f4c
    addq.l #4,%sp
    pea bf_page_layer
    jsr 0x40031494
    addq.l #4,%sp
    bra.w bf_page_draw
bf_page_noop:
    rts
bf_page_close:
    tst.l bf_page_win
    beq.s bf_page_noop
    pea bf_page_win
    jsr 0x40055db4
    addq.l #4,%sp
    pea bf_page_layer
    jsr 0x4003146c
    addq.l #4,%sp
    rts

bf_page_encoder:
    lea -12(%sp),%sp
    movem.l %d0-%d2,(%sp)
    move.l bf_page_track,%d0
    move.l 16(%sp),%d1
    move.l 20(%sp),%d2
    jsr bf_reg_change
    movem.l (%sp),%d0-%d2
    lea 12(%sp),%sp
    bra.w bf_page_draw

bf_page_draw:
    lea -44(%sp),%sp
    movem.l %d2-%d3/%a2/%a5,(%sp)
    lea 16(%sp),%a2
    move.l bf_page_win,%d0
    beq.w .page_done
    move.l %d0,%a5
    lea 36(%a5),%a5
    move.l %a5,-(%sp)
    jsr 0x40035624
    addq.l #4,%sp
    moveq #12,%d0
    moveq #52,%d1
    lea .mode_label,%a0
    bsr.w .page_text
    moveq #51,%d0
    moveq #52,%d1
    lea .oct_label,%a0
    bsr.w .page_text
    move.l bf_page_track,%d0
    jsr bf_mode_get
    lea .fixed,%a0
    tst.l %d0
    beq.s .mode_text
    lea .source,%a0
.mode_text:
    moveq #9,%d0
    moveq #36,%d1
    bsr.w .page_text
    move.l bf_page_track,%d0
    jsr bf_oct_get
    move.l %d0,-(%sp)
    pea .number
    move.l %a2,-(%sp)
    jsr 0x40013a08
    lea 12(%sp),%sp
    moveq #55,%d0
    moveq #36,%d1
    move.l %a2,%a0
    bsr.w .page_text
    /* Two control cells aligned with physical A/B, plus native footer. */
    pea 1
    pea 58
    pea 38
    pea 12
    pea 38
    move.l %a5,-(%sp)
    jsr 0x40012254
    lea 24(%sp),%sp
    pea 1
    pea 12
    pea 115
    pea 12
    clr.l -(%sp)
    move.l %a5,-(%sp)
    jsr 0x40012254
    lea 24(%sp),%sp
    move.l bf_page_track,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea .title
    move.l %a2,-(%sp)
    jsr 0x40013a08
    lea 12(%sp),%sp
    moveq #4,%d0
    moveq #4,%d1
    move.l %a2,%a0
    bsr.w .page_text
    moveq #85,%d0
    moveq #4,%d1
    lea .back,%a0
    bsr.w .page_text
    moveq #1,%d0
    move.l %d0,0x46c7c72c
.page_done:
    movem.l (%sp),%d2-%d3/%a2/%a5
    lea 44(%sp),%sp
    rts
.page_text: /* d0=x,d1=y,a0=string,a5=surface; native C ABI */
    move.l %a0,-(%sp)
    pea -1
    move.l %d1,-(%sp)
    move.l %d0,-(%sp)
    move.l %a5,-(%sp)
    pea 0x400ba876
    jsr 0x40012bd8
    lea 24(%sp),%sp
    rts
.mode_label: .asciz "MODE"
.oct_label: .asciz "OCT"
.fixed: .asciz "FIXED"
.source: .asciz "SOURCE"
.number: .asciz "%d"
.title: .asciz "FOLLOW T%d"
.back: .asciz "NO:BACK"
    .balign 4
bf_page_layer:
    .long 0,bf_page_keys,bf_page_encs,0,0,-1,-1
bf_page_keys:
    /* The opening D key's release is consumed; only a new press closes. */
    .irp key,0x31,0x32,0x3b,0x22,0x23,0x24,0x25,0x26,0x35,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17
    .byte \key,0
    .long bf_page_close,0,0,0,0
    .word 0,0
    .endr
    /* Held knob pushes must not commit stock NOTE SETUP values. */
    .irp key,0x38,0x39,0x3a,0x3c,0x3d
    .byte \key,0
    .long 0,0,0,0,0
    .word 0,0
    .endr
    .byte 0xff,0
    .long 0,0,0,0,0
    .word 0,0
bf_page_encs:
    .irp knob,0,1,2,3,4,5,6
    .byte \knob,0
    .long bf_page_encoder,0,0,0,0
    .endr
    .byte 0xff,0
    .long 0,0,0,0,0
    .balign 4
bf_page_win: .long 0
bf_page_track: .long 0
