/* Metadata accompanies native pattern/track/Part clipboard and undo copies.
 * The synchronous native memcpy wrapper captures before copying and repairs
 * representation after copying. It never calls back into a UI dispatcher. */
#include "core.h"
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define LONG(a) (*(volatile uint32_t *)(uintptr_t)(a))

typedef struct { uint8_t degree, note; } Copied;
typedef struct { Copied root[512]; unsigned length, valid; } Clipboard;
typedef struct { unsigned kind, bank, pattern, track, part, buffer; } Location;
enum { UNKNOWN, CLIP, PATTERN, TRACK, PART };
static Clipboard clips[2], transfer;
static Location destination;
typedef struct { uintptr_t address; Copied root; } BaseCopy;
static BaseCopy base_clips[2][8], base_transfer[8];
static unsigned base_counts[2], base_count;
static void copy_clip(Clipboard *dst, const Clipboard *src) {
    for (unsigned i = 0; i < 512; ++i) dst->root[i] = src->root[i];
    dst->length = src->length;
    dst->valid = src->valid;
}

static uintptr_t canonical(uintptr_t p) {
    unsigned current = BYTE(0x80000002);
    if (current < 16) {
        uintptr_t bank = 0x400e21e0u + current*0x9b340;
        if (p >= 0x1001614e && p < 0x1001614e + 0x8ed80)
            p = bank+p-0x1001614e;
        else if (p >= 0x100a4ece && p < 0x100a4ece + 4*0x18b2)
            p = bank+0x8ed80+p-0x100a4ece;
        else if (p >= 0x100ab196 && p < 0x100ab196+4*0x18b2)
            p = bank+0x9504a+p-0x100ab196;
    }
    return p;
}
static Location locate(uintptr_t p, unsigned length) {
    Location l = {0,0,0,0,0,0};
    if (p == 0x460c8122 || p == 0x460bf218) {
        l.kind = CLIP;
        l.buffer = p == 0x460bf218;
        return l;
    }
    p = canonical(p);
    if (p < 0x400e21e0 || p >= 0x400e21e0 + 16*0x9b340) return l;
    unsigned offset = (unsigned)(p-0x400e21e0);
    l.bank = offset / 0x9b340;
    offset %= 0x9b340;
    if (length == 0x18b2) {
        if (offset >= 0x9504a && offset < 0x9504a + 4*0x18b2) {
            offset -= 0x9504a;
            l.part = 4 + offset/0x18b2;
        } else if (offset >= 0x8ed80 && offset < 0x8ed80 + 4*0x18b2) {
            offset -= 0x8ed80;
            l.part = offset/0x18b2;
        } else return l;
        if (!(offset%0x18b2)) l.kind = PART;
        return l;
    }
    l.pattern = offset/0x8ed8;
    offset %= 0x8ed8;
    if (l.pattern >= 16) return l;
    if (length == 0x8ed8 && !offset) l.kind = PATTERN;
    if (length == 0x8b0 && offset >= 0x48d0 && offset < 0x48d0 + 8*0x8b0) {
        offset -= 0x48d0;
        if (!(offset%0x8b0)) { l.kind = TRACK; l.track = offset/0x8b0; }
    }
    return l;
}
static int absolute(int code, int scale) {
    int n = hd_decode_c(code,scale);
    return n >= 0 ? n : code < 7 ? 0 : 127;
}
static Copied capture(unsigned bank, unsigned pattern, unsigned track, unsigned step, int part) {
    uintptr_t native = 0x400e21e0u + bank*0x9b340;
    Copied result = {HD_NONE,HD_NONE};
    unsigned p;
    if (part >= 0) {
        p = (unsigned)part;
        unsigned off = p < 4 ? 0x8ed80+p*0x18b2 : 0x9504a+(p-4)*0x18b2;
        result.note = BYTE(native+off+0x3e2+track*32);
        if (hd_type_c(track)) result.degree = (uint8_t)hd_base_c(bank,p,track);
    } else {
        p = BYTE(native+pattern*0x8ed8+0x8e57) & 3;
        result.note = BYTE(native+pattern*0x8ed8+0x4900+track*0x8b0+step*32);
        if (hd_type_c(track)) result.degree = (uint8_t)hd_lock_c(bank,pattern,track,step);
    }
    if (result.note != HD_NONE && result.degree < HD_CODES)
        result.note = (uint8_t)absolute(result.degree,hd_scale_c(bank,p,track));
    return result;
}
/* Native MIDI track copy moves NOTE-page defaults in a separate 0xf0-byte
 * slice after the 0x8b0-byte pattern track. Carry those roots by their exact
 * copied byte offsets as well; equality of native pitch is not identity. */
static int clip_of(uintptr_t p) {
    if (p >= 0x460c8122 && p < 0x460c8122+0x8ed8) return 0;
    if (p >= 0x460bf218 && p < 0x460bf218+0x8ed8) return 1;
    return -1;
}
static void base_before(uintptr_t dst, uintptr_t src, unsigned length) {
    int clip = clip_of(src);
    if (clip >= 0) {
        for (unsigned i = 0; i < base_counts[clip]; ++i) {
            BaseCopy *c = &base_clips[clip][i];
            if (c->address >= src && c->address-src < length)
                base_transfer[base_count++] = (BaseCopy){dst+c->address-src,c->root};
        }
        return;
    }
    src = canonical(src);
    if (src < 0x400e21e0 || src >= 0x400e21e0 + 16*0x9b340) return;
    unsigned bank = (unsigned)(src-0x400e21e0)/0x9b340;
    uintptr_t native = 0x400e21e0u + bank*0x9b340;
    for (unsigned part = 0; part < 8 && base_count < 8; ++part) {
        unsigned off = part < 4 ? 0x8ed80+part*0x18b2 : 0x9504a+(part-4)*0x18b2;
        for (unsigned t = 0; t < 8 && base_count < 8; ++t) {
            uintptr_t p = native+off+0x3e2+t*32;
            if (p >= src && p-src < length)
                base_transfer[base_count++] = (BaseCopy){dst+p-src,capture(bank,0,t,0,(int)part)};
        }
    }
}
static int base_after(void) {
    int touched = -1;
    for (unsigned i = 0; i < base_count; ++i) {
        BaseCopy c = base_transfer[i];
        int clip = clip_of(c.address);
        if (clip >= 0) {
            unsigned j = 0;
            while (j < base_counts[clip] && base_clips[clip][j].address != c.address) ++j;
            if (j < 8) {
                base_clips[clip][j] = c;
                if (j == base_counts[clip]) ++base_counts[clip];
            }
            continue;
        }
        uintptr_t p = canonical(c.address);
        if (p < 0x400e21e0 || p >= 0x400e21e0 + 16*0x9b340) continue;
        unsigned bank = (unsigned)(p-0x400e21e0)/0x9b340;
        unsigned offset = (unsigned)(p-0x400e21e0)%0x9b340;
        for (unsigned part = 0; part < 8; ++part) {
            unsigned off = part < 4 ? 0x8ed80+part*0x18b2 : 0x9504a+(part-4)*0x18b2;
            if (offset < off+0x3e2 || offset >= off+0x3e2+8*32) continue;
            unsigned delta = offset-off-0x3e2;
            if (delta%32) continue;
            hd_copy_base_c(bank,part,delta/32,c.root.degree < HD_CODES ? c.root.degree : -1,c.root.note);
            touched = (int)bank;
        }
    }
    return touched;
}
void hd_copy_before_c(uintptr_t dst, uintptr_t src, unsigned length) {
    transfer.valid = 0;
    base_count = 0;
    if (dst == 0x460c8122 || dst == 0x460bf218) {
        unsigned clip = dst == 0x460bf218;
        base_counts[clip] = 0;
        if (length != 0x8ed8 && length != 0x8b0 && length != 0x18b2) clips[clip].valid = 0;
    }
    if (length != 0x8ed8 && length != 0x8b0 && length != 0x18b2) {
        base_before(dst,src,length);
        return;
    }
    destination = locate(dst,length);
    Location source = locate(src,length);
    if (!source.kind || !destination.kind) {
        if (destination.kind == CLIP) clips[destination.buffer].valid = 0;
        return;
    }
    if (source.kind == CLIP) {
        if (!clips[source.buffer].valid || clips[source.buffer].length != length) return;
        copy_clip(&transfer,&clips[source.buffer]);
    } else {
        unsigned count = source.kind == PATTERN ? 512 : source.kind == TRACK ? 64 : 8;
        for (unsigned i = 0; i < count; ++i) {
            unsigned track = source.kind == PATTERN ? i/64 : source.kind == TRACK ? source.track : i;
            transfer.root[i] = capture(source.bank,source.pattern,track,i%64,
                                      source.kind == PART ? (int)source.part : -1);
        }
        transfer.valid = 1;
        transfer.length = length;
    }
}
int hd_copy_after_c(void) {
    if (!transfer.valid) return base_after();
    if (destination.kind == CLIP) {
        copy_clip(&clips[destination.buffer],&transfer);
        return -1;
    }
    unsigned count = destination.kind == PATTERN ? 512 : destination.kind == TRACK ? 64 : 8;
    for (unsigned i = 0; i < count; ++i) {
        unsigned track = destination.kind == PATTERN ? i/64 : destination.kind == TRACK ? destination.track : i;
        Copied c = transfer.root[i];
        int degree = c.degree < HD_CODES ? c.degree : -1;
        if (destination.kind == PART) hd_copy_base_c(destination.bank,destination.part,track,degree,c.note);
        else hd_copy_note_c(destination.bank,destination.pattern,track,i%64,degree,c.note);
    }
    return (int)destination.bank;
}
void hd_operations_reset_c(void) {
    clips[0].valid = clips[1].valid = transfer.valid = 0;
    base_counts[0] = base_counts[1] = base_count = 0;
}
void hd_part_reset_c(uintptr_t p) {
    Location part = locate(p,0x18b2);
    if (part.kind != PART) return;
    for (unsigned t = 0; t < 8; ++t)
        hd_copy_base_c(part.bank,part.part,t,-1,BYTE(p+0x3e2+t*32));
}
void hd_step_copy_c(uintptr_t buffer, unsigned pattern, unsigned track, unsigned page, unsigned mask) {
    Location dst = locate(buffer,0);
    if (dst.kind != CLIP || pattern >= 16 || track >= 8 || page >= 4) return;
    unsigned bank = (LONG(0x46c82456)-0x400e21e0u)/0x9b340;
    if (bank >= 16) return;
    Clipboard *c = &clips[dst.buffer];
    base_counts[dst.buffer] = 0;
    c->valid = 1;
    c->length = 0;
    for (unsigned i = 0; i < 16; ++i)
        if (mask & (1u << i)) c->root[i] = capture(bank,pattern,track,page*16+i,-1);
}
int hd_step_paste_c(uintptr_t buffer, unsigned slot, unsigned pattern, unsigned track, unsigned step) {
    Location src = locate(buffer,0);
    if (src.kind != CLIP || slot >= 16 || pattern >= 16 || track >= 8 || step >= 64) return -1;
    Clipboard *c = &clips[src.buffer];
    if (!c->valid || c->length) return -1;
    unsigned bank = (LONG(0x46c82456)-0x400e21e0u)/0x9b340;
    if (bank >= 16) return -1;
    Copied root = c->root[slot];
    hd_copy_note_c(bank,pattern,track,step,root.degree < HD_CODES ? root.degree : -1,root.note);
    return (int)bank;
}
