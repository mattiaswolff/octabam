/* Working data and OFF/HARM boundary conversion. No allocation, libc,
 * files, UI, or generated-note ownership in this unit. The wrappers provide
 * ordered publication and invoke the persistence/edit lifecycle. */
#include "core.h"

#define NATIVE_BANK_SIZE 0x9b340u
#define PATTERN_SIZE 0x8ed8u
#define PART_SIZE 0x18b2u
#define WORK_PARTS 0x8ed80u
#define SAVED_PARTS 0x9504au
#define NATIVE_BASE 0x400e21e0u
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define WORD(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define ORDER() __asm__ volatile("" ::: "memory")

/* Publish a root and its native edit-detection snapshot together. Keep
 * conversion and retained-bank hashing outside these small critical sections. */
static uint16_t root_mask(void) {
    uint16_t sr;
    __asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr" : "=d"(sr) :: "cc", "memory");
    return sr;
}
static void root_unmask(uint16_t sr) {
    __asm__ volatile("move.w %0,%%sr" :: "d"(sr) : "cc", "memory");
}

HdBank hd_banks[HD_BANKS];
volatile uint8_t hd_busy[HD_TRACKS];
volatile uint8_t hd_target[HD_TRACKS];

static volatile uint8_t *native(unsigned bank) {
    return (volatile uint8_t *)(uintptr_t)(NATIVE_BASE + NATIVE_BANK_SIZE*bank);
}
static unsigned index_of(unsigned pattern, unsigned track, unsigned step) {
    return (pattern*8 + track)*64 + step;
}
static unsigned part_of(unsigned bank, unsigned pattern) {
    return native(bank)[pattern*PATTERN_SIZE + 0x8e57] & 3;
}
static unsigned part_offset(unsigned part) {
    return part < 4 ? WORK_PARTS + part*PART_SIZE : SAVED_PARTS + (part-4)*PART_SIZE;
}
static volatile uint8_t *base_note(unsigned bank, unsigned part, unsigned track) {
    return native(bank) + part_offset(part) + 0x3e2 + 32*track;
}
static volatile uint8_t *step_note(unsigned bank, unsigned pattern, unsigned track, unsigned step) {
    return native(bank) + pattern*PATTERN_SIZE + 0x4900 + track*0x8b0 + step*32;
}
static int valid_code(unsigned value) { return value < HD_CODES || value == HD_NONE; }

int hd_scale_c(unsigned bank, unsigned part, unsigned track) {
    if (bank >= 16 || part >= 8 || track >= 8) return 0;
    unsigned source = hd_source_c(track);
    if (source >= 8) source = track;
    unsigned raw = native(bank)[part_offset(part) + 0x4e2 + source*36 + 17];
    if (!raw || raw > 84) return 0; /* KEY OFF -> C-major reference */
    if (raw <= 24) return (int)(((raw-1)/2)*4 + ((raw-1)&1)*320);
    static const unsigned modes[5] = {1, 2, 3, 4, 6};
    return (int)(((raw-25)/5)*4 + modes[(raw-25)%5]*64);
}

/* Native mirrors have different bases for patterns, working and saved Parts. */
static void write_native(unsigned bank, volatile uint8_t *p, unsigned value) {
    *p = (uint8_t)value;
    if (BYTE(0x80000002) != bank) return;
    unsigned offset = (unsigned)(p - native(bank));
    if (offset < WORK_PARTS) BYTE(0x1001614e + offset) = (uint8_t)value;
    else if (offset >= WORK_PARTS && offset < WORK_PARTS+4*PART_SIZE)
        BYTE(0x100a4ece + offset-WORK_PARTS) = (uint8_t)value;
    else if (offset >= SAVED_PARTS && offset < SAVED_PARTS+4*PART_SIZE)
        BYTE(0x100ab196 + offset-SAVED_PARTS) = (uint8_t)value;
}
static void dirty(unsigned bank) {
    *(volatile uint32_t *)(native(bank)+0x9b332) = 1;
    if (BYTE(0x80000002) == bank) WORD(0x100f8598) = 1;
}
static unsigned absolute(unsigned degree, int scale) {
    int note = hd_decode_c((int)degree, scale);
    /* Native NOTE has no silent-root sentinel independent of lock presence.
     * Commit the closest MIDI boundary on OFF; never wrap or erase a lock. */
    return note >= 0 ? (unsigned)note : degree < 7 ? 0u : 127u;
}

void hd_bank_reset_c(unsigned bank) {
    if (bank >= 16) return;
    uint8_t *p = (uint8_t *)&hd_banks[bank];
    for (unsigned i = 0; i < sizeof(HdBank); ++i) p[i] = HD_NONE;
    for (unsigned t = 0; t < 8; ++t) {
        hd_banks[bank].active[t] = 0;
        hd_banks[bank].valid[t] = 0;
    }
}
void hd_reset_c(void) {
    for (unsigned b = 0; b < 16; ++b) hd_bank_reset_c(b);
    for (unsigned t = 0; t < 8; ++t) hd_busy[t] = hd_target[t] = 0;
}

static void enter(unsigned bank, unsigned track) {
    HdBank *h = &hd_banks[bank];
    for (unsigned part = 0; part < 8; ++part) {
        unsigned i = part*8 + track, note = *base_note(bank, part, track);
        h->base_note[i] = (uint8_t)note;
        h->base[i] = (uint8_t)hd_encode_c((int)note, hd_scale_c(bank, part, track));
    }
    for (unsigned p = 0; p < 16; ++p) {
        int scale = hd_scale_c(bank, part_of(bank, p), track);
        for (unsigned s = 0; s < 64; ++s) {
            unsigned i = index_of(p, track, s), note = *step_note(bank, p, track, s);
            h->note[i] = (uint8_t)note;
            h->degree[i] = (uint8_t)hd_encode_c((int)note, scale);
        }
    }
    ORDER();
    h->active[track] = 1;
    h->valid[track] = 1;
}

/* Reconcile native edits without interpreting a degree as a MIDI note. This
 * also handles ordinary Part Clear/Reload paths; explicit degree copy hooks
 * preserve degree identity when copying while a different KEY is selected. */
int hd_base_c(unsigned bank, unsigned part, unsigned track) {
    if (bank >= 16 || part >= 8 || track >= 8) return -1;
    HdBank *h = &hd_banks[bank];
    if (!h->valid[track] || !h->active[track]) return -1;
    unsigned i = part*8 + track, note = *base_note(bank, part, track);
    if (note != h->base_note[i]) {
        h->base[i] = (uint8_t)hd_encode_c((int)note, hd_scale_c(bank, part, track));
        h->base_note[i] = (uint8_t)note;
    }
    return h->base[i] < HD_CODES ? h->base[i] : -1;
}
int hd_degree_c(unsigned bank, unsigned pattern, unsigned track, unsigned step) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64) return -1;
    HdBank *h = &hd_banks[bank];
    if (!h->valid[track] || !h->active[track]) return -1;
    unsigned i = index_of(pattern, track, step), part = part_of(bank, pattern);
    unsigned note = *step_note(bank, pattern, track, step);
    if (note != h->note[i]) {
        h->degree[i] = (uint8_t)hd_encode_c((int)note, hd_scale_c(bank, part, track));
        h->note[i] = (uint8_t)note;
    }
    return h->degree[i] < HD_CODES ? h->degree[i] : hd_base_c(bank, part, track);
}
int hd_resolve_c(unsigned bank, unsigned pattern, unsigned track, unsigned step) {
    int degree = hd_degree_c(bank, pattern, track, step);
    return degree < 0 ? -1 : hd_decode_c(degree, hd_scale_c(bank, part_of(bank, pattern), track));
}

static void leave(unsigned bank, unsigned track) {
    HdBank *h = &hd_banks[bank];
    for (unsigned part = 0; part < 8; ++part) {
        int code = hd_base_c(bank, part, track);
        if (code >= 0) {
            unsigned note = absolute((unsigned)code, hd_scale_c(bank, part, track));
            write_native(bank, base_note(bank, part, track), note);
            h->base_note[part*8+track] = (uint8_t)note;
        }
    }
    for (unsigned p = 0; p < 16; ++p) {
        int scale = hd_scale_c(bank, part_of(bank, p), track);
        for (unsigned s = 0; s < 64; ++s) {
            unsigned i = index_of(p, track, s);
            /* Inheritance is preserved: never materialize an unlocked root. */
            if (*step_note(bank, p, track, s) == HD_NONE) continue;
            int code = hd_degree_c(bank, p, track, s);
            if (code >= 0) {
                unsigned note = absolute((unsigned)code, scale);
                write_native(bank, step_note(bank, p, track, s), note);
                h->note[i] = (uint8_t)note;
            }
        }
    }
    ORDER();
    h->active[track] = 0;
    dirty(bank);
}

void hd_bank_loaded_c(unsigned bank) {
    if (bank >= 16) return;
    HdBank *h = &hd_banks[bank];
    for (unsigned t = 0; t < 8; ++t) {
        unsigned mode = hd_type_c(t) != 0;
        if (mode && (!h->valid[t] || !h->active[t])) enter(bank, t);
        else if (!mode && h->valid[t] && h->active[t]) leave(bank, t);
        h->valid[t] = 1;
    }
}
void hd_ready_all_c(void) {
    for (unsigned b = 0; b < 16; ++b) hd_bank_loaded_c(b);
}
void hd_mode_c(unsigned track, unsigned mode) {
    if (track >= 8 || mode > 2) return;
    hd_target[track] = (uint8_t)mode;
    ORDER();
    hd_busy[track] = 1;
    ORDER();
    for (unsigned b = 0; b < 16; ++b) {
        HdBank *h = &hd_banks[b];
        if (!h->valid[track]) continue; /* native bank not loaded yet */
        if (mode && !h->active[track]) enter(b, track);
        else if (!mode && h->active[track]) leave(b, track);
    }
    ORDER();
    /* Wrapper publishes HARM setting and refreshes live/pending roots before
     * clearing hd_busy. No engine consumer may read partially converted data. */
}
void hd_record_c(unsigned bank, unsigned pattern, unsigned track, unsigned step, int degree) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64) return;
    /* A HARM event can still be queued when HARM is turned off. Its metadata
     * then holds the resolved absolute root, frozen at that boundary. */
    if (degree >= 128 && degree <= 255) {
        hd_copy_note_c(bank,pattern,track,step,-1,degree & 127);
        return;
    }
    if ((unsigned)degree >= HD_CODES) return;
    HdBank *h = &hd_banks[bank];
    unsigned i = index_of(pattern, track, step);
    uint16_t sr = root_mask();
    h->degree[i] = (uint8_t)degree;
    h->note[i] = *step_note(bank, pattern, track, step);
    h->active[track] = h->valid[track] = 1;
    root_unmask(sr);
    dirty(bank);
}
void hd_edit_base_c(unsigned bank, unsigned part, unsigned track, int degree) {
    if (bank >= 16 || part >= 8 || track >= 8 || (unsigned)degree >= HD_CODES) return;
    HdBank *h = &hd_banks[bank];
    unsigned i = part*8 + track;
    uint16_t sr = root_mask();
    h->base[i] = (uint8_t)degree;
    h->base_note[i] = *base_note(bank, part, track);
    h->active[track] = h->valid[track] = 1;
    root_unmask(sr);
    if (part < 4) {
        unsigned mask = native(bank)[0x95048] | (1u << part);
        native(bank)[0x95048] = (uint8_t)mask;
        if (BYTE(0x80000002) == bank) BYTE(0x100b145e) = (uint8_t)mask;
    }
    dirty(bank);
}
int hd_lock_c(unsigned bank, unsigned pattern, unsigned track, unsigned step) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64) return -1;
    (void)hd_degree_c(bank, pattern, track, step);
    unsigned code = hd_banks[bank].degree[index_of(pattern,track,step)];
    return code < HD_CODES ? (int)code : -1;
}
void hd_edit_step_c(unsigned bank, unsigned pattern, unsigned track, unsigned step, int degree) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64 ||
        (degree != HD_NONE && (unsigned)degree >= HD_CODES)) return;
    HdBank *h = &hd_banks[bank];
    unsigned i = index_of(pattern, track, step);
    unsigned note = degree == HD_NONE ? HD_NONE : absolute((unsigned)degree,
                                          hd_scale_c(bank,part_of(bank,pattern),track));
    uint16_t sr = root_mask();
    write_native(bank,step_note(bank,pattern,track,step),note);
    h->degree[i] = (uint8_t)degree;
    h->note[i] = (uint8_t)note;
    h->active[track] = h->valid[track] = 1;
    root_unmask(sr);
    dirty(bank);
}
/* Native memcpy has already copied all fields. Repair only the root's
 * representation at the destination; source degree -1 denotes stock. */
void hd_copy_note_c(unsigned bank, unsigned pattern, unsigned track, unsigned step, int degree, int note) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64 ||
        (note != HD_NONE && (unsigned)note > 127)) return;
    if (hd_type_c(track)) {
        if (note == HD_NONE) degree = HD_NONE;
        else if (degree < 0) degree = hd_encode_c(note,hd_scale_c(bank,part_of(bank,pattern),track));
        hd_edit_step_c(bank,pattern,track,step,degree);
    } else {
        write_native(bank,step_note(bank,pattern,track,step),(unsigned)note);
        hd_banks[bank].note[index_of(pattern,track,step)] = (uint8_t)note;
        hd_banks[bank].active[track] = 0;
        hd_banks[bank].valid[track] = 1;
        dirty(bank);
    }
}
void hd_copy_base_c(unsigned bank, unsigned part, unsigned track, int degree, int note) {
    if (bank >= 16 || part >= 8 || track >= 8 || (unsigned)note > 127) return;
    if (hd_type_c(track)) {
        if (degree < 0) degree = hd_encode_c(note,hd_scale_c(bank,part,track));
        hd_edit_base_c(bank,part,track,degree);
    } else {
        write_native(bank,base_note(bank,part,track),(unsigned)note);
        hd_banks[bank].base_note[part*8+track] = (uint8_t)note;
        dirty(bank);
    }
}
int hd_validate_c(const HdBank *h) {
    for (unsigned i = 0; i < HD_LOCKS; ++i)
        if (!valid_code(h->degree[i]) || (h->note[i] > 127 && h->note[i] != HD_NONE)) return 0;
    for (unsigned i = 0; i < HD_BASES; ++i)
        if (!valid_code(h->base[i]) || (h->base_note[i] > 127 && h->base_note[i] != HD_NONE)) return 0;
    for (unsigned t = 0; t < 8; ++t)
        if (h->active[t] > 1 || h->valid[t] > 1 || (h->active[t] && !h->valid[t])) return 0;
    return 1;
}

/* Native clear/place hooks run before stock clears the root. Invalidate its
 * degree explicitly so deleting and replacing an identical NOTE cannot
 * resurrect a degree that belonged to an earlier KEY. */
void hd_forget_c(unsigned bank, unsigned pattern, unsigned track, unsigned step) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64) return;
    HdBank *h = &hd_banks[bank];
    unsigned i = index_of(pattern,track,step);
    uint16_t sr = root_mask();
    /* A reader between this hook and native clear must not reconstruct the
     * deleted degree from the still-present old NOTE. OFF stays native. */
    if (h->active[track]) write_native(bank,step_note(bank,pattern,track,step),HD_NONE);
    h->degree[i] = h->note[i] = HD_NONE;
    root_unmask(sr);
}
