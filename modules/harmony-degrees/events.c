/* Degree provenance follows the native staged/pending event. UI-selected
 * bank/pattern is never used to guess which lock has just fired. */
#include "core.h"

typedef struct {
    uint8_t bank, part, degree, note, active, valid, converted, pattern;
    uint8_t inherited;
} HdEvent;
static HdEvent staged[8], pending[32], fired[8];
volatile uint8_t hd_rebuild[8];
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))

void hd_events_reset_c(void) {
    for (unsigned i = 0; i < 8; ++i) staged[i].valid = fired[i].valid = hd_rebuild[i] = 0;
    for (unsigned i = 0; i < 32; ++i) pending[i].valid = 0;
}
void hd_event_stage_c(unsigned bank, unsigned pattern, unsigned track, unsigned step, int slot) {
    if (bank >= 16 || pattern >= 16 || track >= 8 || step >= 64 || slot > 3) return;
    HdEvent *e = slot < 0 ? &staged[track] : &pending[(unsigned)slot*8+track];
    uintptr_t native = 0x400e21e0u + bank*0x9b340u;
    unsigned part = BYTE(native + pattern*0x8ed8 + 0x8e57) & 3;
    unsigned note = BYTE(native + pattern*0x8ed8 + 0x4900 + track*0x8b0 + step*32);
    e->inherited = note == 255;
    if (note == 255) note = BYTE(native+0x8ed80+part*0x18b2+0x3e2+track*32);
    e->bank = (uint8_t)bank;
    e->part = (uint8_t)part;
    e->pattern = (uint8_t)pattern;
    e->note = (uint8_t)note;
    e->active = hd_type_c(track) != 0;
    e->degree = e->active ? (uint8_t)hd_lock_c(bank, pattern, track, step) : HD_NONE;
    e->converted = 0;
    e->valid = 1;
}
void hd_event_copy_c(unsigned track) {
    if (track < 8) pending[track] = staged[track];
}
int hd_event_fire_c(unsigned slot, unsigned track) {
    if (slot >= 32 || track >= 8) return -1;
    fired[track] = pending[slot];
    HdEvent *e = &fired[track];
    if (e->valid) e->part = BYTE(0x400e21e0u + e->bank*0x9b340u + e->pattern*0x8ed8 + 0x8e57) & 3;
    /* OFF ordinarily replays every native byte. Only a boundary conversion
     * of this already queued event supplies a replacement native root. */
    return e->valid && e->converted && !e->active ? e->note : -1;
}
static void convert(HdEvent *e, unsigned track, unsigned mode) {
    if (!e->valid || e->active == (mode != 0)) return;
    e->part = BYTE(0x400e21e0u + e->bank*0x9b340u + e->pattern*0x8ed8 + 0x8e57) & 3;
    int scale = hd_scale_c(e->bank, e->part, track);
    if (mode) e->degree = e->inherited ? HD_NONE : (uint8_t)hd_encode_c(e->note, scale);
    else {
        /* hd_mode_c has already materialized Part defaults in native NOTE. */
        if (e->inherited) e->note = BYTE(0x400e21e0u + e->bank*0x9b340u + 0x8ed80 + e->part*0x18b2 + 0x3e2 + track*32);
        else {
            int note = hd_decode_c(e->degree, scale);
            e->note = note >= 0 ? (uint8_t)note : e->degree < 7 ? 0 : 127;
        }
    }
    e->active = mode != 0;
    e->converted = 1;
}
void hd_events_mode_c(unsigned track, unsigned mode) {
    if (track >= 8 || mode > 2) return;
    convert(&staged[track], track, mode);
    for (unsigned slot = 0; slot < 4; ++slot) convert(&pending[slot*8+track], track, mode);
    convert(&fired[track], track, mode);
    hd_rebuild[track] = fired[track].valid;
    if (!mode && fired[track].valid)
        BYTE(0x46c76fe0u + track*32) = fired[track].note;
}
int hd_prepare_c(int note, unsigned track) {
    if (track >= 8 || !hd_type_c(track)) return note;
    if (hd_busy[track]) return -1;
    const HdEvent *e = &fired[track];
    if (e->valid && e->active) {
        int degree = e->inherited ? hd_base_c(e->bank,e->part,track) : e->degree;
        return hd_decode_c(degree, hd_scale_c(e->bank,e->part,track));
    }
    /* Before the first scheduled event, use the current working Part default.
     * This is also the root published to Follow before sequencer playback. */
    unsigned bank = BYTE(0x80000002), part = BYTE(0x100b14cf) & 3;
    return hd_decode_c(hd_base_c(bank,part,track),hd_scale_c(bank,part,track));
}
