/* Adapter to pinned MIDISC2.1 data/ensure entry; no upstream bytes altered.
 * The oracle gate pins its source. Our scene gate exercises these addresses
 * through its real editor/pack/morph code. Absent Scenes, every entry is inert. */
    .include "remix.inc"
    .text
    .global hd_scene_memory_c,hd_scene_ensure_c,hd_scene_invalidate_c
hd_scene_memory_c:
.if HD_SCENES
    move.l #msc21_ram,%d0
.else
    moveq #0,%d0
.endif
    rts
hd_scene_ensure_c:
.if HD_SCENES
    lea -44(%sp),%sp
    movem.l %d2-%d7/%a2-%a6,(%sp)
    jsr msc21_b+0x1bc
    movem.l (%sp),%d2-%d7/%a2-%a6
    lea 44(%sp),%sp
.endif
    rts
hd_scene_invalidate_c:
.if HD_SCENES
    moveq #-1,%d0
    move.b %d0,h_400d6c84+0x60
    clr.l msc21_b+0x43e8
.endif
    rts

    .macro HOLD symbol,side
    .global \symbol
\symbol:
    jsr 0x4006dbcc
.if HD_SCENES
    tst.l %d0
    bne.s 1f
    lea -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    move.l %d6,-(%sp)
    move.l %d3,-(%sp)
    pea \side
    jsr hd_scene_delta_c
    lea 12(%sp),%sp
    move.l %d0,%d6
    movem.l (%sp),%d0-%d1/%a0-%a1
    lea 16(%sp),%sp
    cmpi.l #0x80000000,%d6
    bne.s 1f
    moveq #1,%d0 /* skip dormant NOT2-4 in HARM, using native guard result */
1:
.endif
    rts
    .endm
    HOLD hd_scene_hold_a,0
    HOLD hd_scene_hold_b,1

/* PR #647's written-byte gas port leaves the -16 stack displacement's
 * untouched 0xff high byte as a zero-filled gap: its hook advances SP by
 * 240+16=256. Supply that exact pinned hook with a reserved stack window
 * and its real continuation at the resulting return slot. No instruction
 * in MIDI SCENES is rewritten. Our linked gate pins the displacement and
 * verifies SP, callee registers and both context-publication branches. */
    .global hd_scene_commit_stack
hd_scene_commit_stack:
    move.l %d0,0x80006628
.if HD_SCENES
    lea -256(%sp),%sp
    move.l #0x400a44fa,%a1
    move.l %a1,252(%sp)
.endif
    jmp 0x400a44f4
