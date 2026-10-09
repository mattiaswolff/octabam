/* DEG interpretation of unchanged MIDISC2.1 scene storage.
 * The scene module still owns scene editing, persistence and ordinary MIDI
 * parameters. Read endpoints in the captured engine Part, never UI context.
 * No private MIDI SCENES executable or data-layout patch is applied. */
#include "core.h"
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define LONG(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define SCENE_BYTES 144u
#define SPARSE_OFFSET 0x17a2u

typedef struct { uint8_t assigned[2], sparse[SCENE_BYTES]; } HdSceneSnapshot;
static HdSceneSnapshot outgoing[64];
extern volatile uint32_t mp_snapshot_bank, mp_snapshot_parts;

static uintptr_t part(unsigned context) {
    return 0x400e21e0u+(context/4)*0x9b340u+0x8ed80u+(context%4)*0x18b2u;
}
void hd_scene_before_c(unsigned context) {
    if (!hd_scenes_c() || context>=64) return;
    uintptr_t p=part(context);
    for (unsigned i=0;i<2;++i) outgoing[context].assigned[i]=BYTE(p+0x10+i);
    for (unsigned i=0;i<SCENE_BYTES;++i) outgoing[context].sparse[i]=BYTE(p+SPARSE_OFFSET+i);
}

/* Build the complete bank snapshot BEFORE shared publication. A playback
 * interrupt during this copy still reads the untouched native Part. */
void hd_scenes_before_c(uintptr_t bank) {
    if (!hd_scenes_c() || bank<0x400e21e0u) return;
    unsigned offset=(unsigned)(bank-0x400e21e0u);
    if (offset>=16u*0x9b340u || offset%0x9b340u) return;
    unsigned context=(offset/0x9b340u)*4;
    for (unsigned i=0;i<4;++i) hd_scene_before_c(context+i);
}

/* Exactly the existing 32-active-flat limit, ordered track then flat.
 * Both endpoints of one parameter consume one slot, not two. */
int hd_scene_value_c(unsigned context, unsigned track, unsigned flat, int base) {
    if (!hd_scenes_c() || context>=64 || track>=8 || flat!=0) return base;
    uintptr_t p=part(context);
    const volatile uint8_t *assigned=(const volatile uint8_t *)(p+0x10);
    const volatile uint8_t *sparse=(const volatile uint8_t *)(p+SPARSE_OFFSET);
    if (mp_snapshot_bank==0x400e21e0u+(context/4)*0x9b340u &&
        (mp_snapshot_parts & (1u<<(context%4)))) {
        assigned=outgoing[context].assigned;
        sparse=outgoing[context].sparse;
    }
    if (sparse[0]!=0x4d || sparse[1]!=0x53 || sparse[2]>46) return base;
    unsigned a=assigned[0], b=assigned[1], target=track*32+flat;
    unsigned seen[8]={0};
    int va=-1,vb=-1;
    unsigned maximum=hd_part_type_c(context/4,context%4,track) ? 83u : 127u;
    for (unsigned i=0;i<sparse[2];++i) {
        unsigned offset=4+i*3, index=(unsigned)sparse[offset]*256+sparse[offset+1];
        unsigned scene=index>>8, param=index&255u, value=sparse[offset+2];
        if (scene>=16 || param%32>=30 || value>=128) continue;
        if ((a==255 || scene!=(a&15)) && (b==255 || scene!=(b&15))) continue;
        seen[param/32] |= 1u<<(param%32);
        if (param!=target || value>maximum) continue;
        if (a!=255 && scene==(a&15)) va=(int)value;
        if (b!=255 && scene==(b&15)) vb=(int)value;
    }
    if (va<0 && vb<0) return base;
    unsigned before=0;
    for (unsigned t=0;t<=track;++t) {
        unsigned mask=seen[t];
        if (t==track) mask &= (1u<<flat)-1u;
        while (mask) { mask &= mask-1; ++before; }
    }
    if (before>=32) return base;
    if (va<0) va=base;
    if (vb<0) vb=base;
    unsigned weight=127u-(LONG(0x460d16c8)&127u);
    if (!weight) return va;
    if (weight==127) return vb;
    /* Match MIDISC2.1's signed ASR, including descending sweeps. */
    return va+(((vb-va)*(int)weight)>>7);
}

/* Explicit HARM edits convert only NOTE scene endpoints. Saved Part/Kit
 * copies keep their own mode and representation. Native mirrors and dirty
 * bookkeeping are updated by the same degree-owned writer as other data. */
void hd_scene_mode_c(unsigned context, unsigned track, unsigned old, unsigned mode, int scale) {
    if (!hd_scenes_c() || context>=64 || track>=8 || (!old==!mode)) return;
    const volatile uint8_t *s=(const volatile uint8_t *)(part(context)+SPARSE_OFFSET);
    if (s[0]!=0x4d || s[1]!=0x53 || s[2]>46) return;
    unsigned changed=0;
    for (unsigned i=0;i<s[2];++i) {
        unsigned offset=4+i*3, index=(unsigned)s[offset]*256+s[offset+1], value=s[offset+2];
        if (index>=4096 || (index&255u)!=track*32 || value>127) continue;
        int next;
        if (mode) next=hd_encode_c((int)value,scale);
        else {
            if (value>=84) continue;
            next=hd_decode_c((int)value,scale);
            if (next<0) next=value<7 ? 0 : 127;
        }
        if (next>=0 && (unsigned)next!=value) {
            hd_scene_part_byte_c(context,SPARSE_OFFSET+offset+2,(unsigned)next);
            changed=1;
        }
    }
    if (changed) hd_scene_invalidate_c();
}

/* Native scene hold dispatch supplies its ordinary encoder delta.
 * Seed a missing DEG lock from the Part DEG, not its dormant native NOTE;
 * upstream still performs the write, pack, dirty marking, morph and redraw. */
int hd_scene_delta_c(unsigned side, unsigned flat, int delta) {
    if (!hd_scenes_c() || side>1 || !delta || !LONG(0x80000012) || LONG(0x460d1684)) return delta;
    int context=hd_ui_context_c();
    unsigned track=BYTE(0x100b14cc);
    if (context<0 || track>=8 || !hd_part_type_c((unsigned)context/4,(unsigned)context%4,track)) return delta;
    /* CHRD has its own Part/pattern store. Dormant native NOT2-4 are not
     * CHRD scene endpoints; do not create misleading locks on those knobs. */
    if (flat>=3 && flat<=5) return (-2147483647-1);
    if (flat) return delta;
    unsigned scene=BYTE(part((unsigned)context)+0x10+side);
    if (scene==255) return delta;
    hd_scene_ensure_c();
    volatile uint8_t *slot=(volatile uint8_t *)(hd_scene_memory_c()+(scene&15u)*256+track*32);
    unsigned value=*slot;
    if (value==255) { value=(unsigned)hd_base_c((unsigned)context/4,(unsigned)context%4,track); *slot=(uint8_t)value; }
    int next=hd_ui_advance_c((int)value,delta);
    return next-(int)value;
}

int hd_scene_ui_c(unsigned flat, int base) {
    if (!hd_scenes_c() || flat) return base;
    unsigned side=LONG(0x460d169c), track=BYTE(0x100b14cc);
    int context=hd_ui_context_c();
    if ((side!=1 && side!=2) || context<0 || track>=8) return base;
    unsigned scene=BYTE(part((unsigned)context)+0x10+side-1);
    if (scene==255) return base;
    hd_scene_ensure_c();
    unsigned value=BYTE(hd_scene_memory_c()+(scene&15u)*256+track*32);
    return value<84 ? (int)value|256 : base;
}
