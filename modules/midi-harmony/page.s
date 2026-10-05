/* Harmony window: native window/input-layer pattern from the Tuner module.
 * NOTE SETUP F press opens it; A=HARM, B=VOIC. Native ARP KEY stays put.
 * Track is fixed while open. Track/page keys close the window; a subsequent
 * press selects the track/page. Transport and chromatic keys pass through.
 * No UI-task/ISR hook: redraw only on open or an encoder edit.
 */
    .text
    .global mh_page_open,mh_page_close,mh_page_noop,mh_page_encoder
    .global mh_page_win,mh_page_track,mh_page_draw
mh_page_open:
    tst.l mh_page_win
    bne.w mh_page_close
    moveq #0,%d0
    move.b 0x100b14cc,%d0
    cmpi.l #7,%d0
    bhi.s mh_page_noop
    move.l %d0,mh_page_track
    pea mh_page_close
    pea 5 /* stock modal class, shared with TEMPO/Tuner */
    clr.l -(%sp)
    clr.l -(%sp)
    pea 60
    pea 120
    jsr 0x4005829c
    lea 24(%sp),%sp
    move.l %d0,mh_page_win
    beq.s mh_page_noop
    move.l %d0,-(%sp)
    jsr 0x40056f4c
    addq.l #4,%sp
    pea mh_page_layer
    jsr 0x40031494
    addq.l #4,%sp
    bra.w mh_page_draw
mh_page_noop:
    rts
mh_page_close:
    tst.l mh_page_win
    beq.s mh_page_noop
    pea mh_page_win
    jsr 0x40055db4
    addq.l #4,%sp
    pea mh_page_layer
    jsr 0x4003146c
    addq.l #4,%sp
    rts

mh_page_encoder:
    lea -12(%sp),%sp
    movem.l %d2-%d4,(%sp)
    move.l 16(%sp),%d2 /* knob */
    move.l 20(%sp),%d3 /* signed detents */
    cmpi.l #1,%d2
    bhi.s .page_encoder_done
    move.l mh_page_track,%d4
    move.l %d4,%d0
    tst.l %d2
    bne.s .page_voic
    jsr mh_get
    /* Clamp delta before addition to prevent signed overflow. */
    cmpi.l #3,%d3
    ble.s .page_harm_low
    moveq #3,%d3
.page_harm_low:
    cmpi.l #-3,%d3
    bge.s .page_harm_add
    moveq #-3,%d3
.page_harm_add:
    add.l %d3,%d0
    bpl.s .page_harm_max
    moveq #0,%d0
.page_harm_max:
    cmpi.l #3,%d0
    ble.s .page_harm_set
    moveq #3,%d0
.page_harm_set:
    move.l %d0,%d1
    move.l %d4,%d0
    jsr mh_set
    bra.s .page_encoder_draw
.page_voic:
    tst.l %d3
    beq.s .page_encoder_done
    bgt.s .page_voic_on
    moveq #0,%d1
    bra.s .page_voic_set
.page_voic_on:
    moveq #1,%d1
.page_voic_set:
    jsr mh_voic_set
.page_encoder_draw:
    jsr mh_page_draw
.page_encoder_done:
    movem.l (%sp),%d2-%d4
    lea 12(%sp),%sp
    rts

mh_page_draw:
    lea -44(%sp),%sp
    movem.l %d2-%d3/%a2/%a5,(%sp)
    lea 16(%sp),%a2 /* 28-byte text scratch */
    move.l mh_page_win,%d0
    beq.w .page_draw_done
    move.l %d0,%a5
    lea 36(%a5),%a5
    move.l %a5,-(%sp)
    jsr 0x40035624
    addq.l #4,%sp
    move.l mh_page_track,%d0
    addq.l #1,%d0
    move.l %d0,-(%sp)
    pea .page_title
    move.l %a2,-(%sp)
    jsr 0x40013a08
    lea 12(%sp),%sp
    moveq #5,%d0
    moveq #44,%d1
    move.l %a2,%a0
    bsr.w .page_text
    moveq #8,%d0
    moveq #30,%d1
    lea .page_harm_label,%a0
    bsr.w .page_text
    moveq #65,%d0
    moveq #30,%d1
    lea .page_voic_label,%a0
    bsr.w .page_text
    move.l mh_page_track,%d0
    jsr mh_get
    move.l %d0,-(%sp)
    move.l %a2,-(%sp)
    jsr mh_type_format
    addq.l #8,%sp
    moveq #8,%d0
    moveq #19,%d1
    move.l %a2,%a0
    bsr.w .page_text
    move.l mh_page_track,%d0
    jsr mh_voic_get
    lea .page_root,%a0
    tst.l %d0
    beq.s .page_voice_text
    lea .page_auto,%a0
.page_voice_text:
    moveq #65,%d0
    moveq #19,%d1
    bsr.w .page_text
    moveq #5,%d0
    moveq #4,%d1
    lea .page_back,%a0
    bsr.w .page_text
    moveq #1,%d0
    move.l %d0,0x46c7c72c
.page_draw_done:
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
.page_title: .asciz "HARMONY T%d"
.page_harm_label: .asciz "A HARM"
.page_voic_label: .asciz "B VOIC"
.page_root: .asciz "ROOT"
.page_auto: .asciz "AUTO"
.page_back: .asciz "NO:BACK"
    .balign 4
mh_page_layer:
    .long 0,mh_page_keys,mh_page_encs,0,0,-1,-1
mh_page_keys:
    /* The opening F key's release is consumed; only a new press closes. */
    .irp key,0x31,0x32,0x3d,0x22,0x23,0x24,0x25,0x26,0x35,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17
    .byte \key,0
    .long mh_page_close,0,0,0,0
    .word 0,0
    .endr
    /* Held knob pushes must not commit stock NOTE SETUP values. */
    .irp key,0x38,0x39,0x3a,0x3b,0x3c
    .byte \key,0
    .long 0,0,0,0,0
    .word 0,0
    .endr
    .byte 0xff,0
    .long 0,0,0,0,0
    .word 0,0
mh_page_encs:
    .irp knob,0,1,2,3,4,5,6
    .byte \knob,0
    .long mh_page_encoder,0,0,0,0
    .endr
    .byte 0xff,0
    .long 0,0,0,0,0
    .balign 4
mh_page_win: .long 0
mh_page_track: .long 0
