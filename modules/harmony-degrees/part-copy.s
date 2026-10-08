/* Native memcpy entry: capture outgoing scale provenance before a complete
 * Part can be replaced by ANY caller. This includes native Part operations
 * and library callers, without a KITS reference or alternate copy path.
 * Other copies replay the original prologue and continue stock immediately.
 * The C callback further restricts the destination to actual working Parts.
 */
    .text
    .global hd_native_copy
hd_native_copy:
    move.l 12(%sp),%d0
    cmpi.l #0x18b2,%d0
    bne.s .native
    lea -16(%sp),%sp
    movem.l %d0-%d1/%a0-%a1,(%sp)
    move.l 20(%sp),-(%sp)
    jsr hd_part_before_c
    addq.l #4,%sp
    movem.l (%sp),%d0-%d1/%a0-%a1
    lea 16(%sp),%sp
.native:
    move.l %d2,-(%sp)
    move.l 8(%sp),%a1
    jmp 0x4002089e
