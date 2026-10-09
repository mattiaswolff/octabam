/* Pattern-root conversion policy, independent of native Part storage, UI,
 * KITS and file I/O. Native adapters capture contexts and publish atomically. */
#include "roots.h"

extern int hd_encode_c(int note, int scale);
extern int hd_decode_c(int degree, int scale);

static int scale_valid(unsigned scale) {
    return !(scale & 3u) && ((scale >> 2) & 15u) < 12 && (scale >> 6) < 7;
}
static unsigned pack_scale(unsigned scale) {
    return (scale >> 6)*12 + ((scale >> 2) & 15u);
}
static unsigned unpack_scale(unsigned scale) {
    return (scale/12)*64 + (scale%12)*4;
}
static unsigned absolute(unsigned degree, unsigned scale) {
    int note = hd_decode_c((int)degree, (int)scale);
    /* Native NOTE has no silent-root sentinel separate from lock presence.
     * Leaving HARM clamps at MIDI bounds without dropping explicit locks. */
    return note >= 0 ? (unsigned)note : degree < 7 ? 0u : 127u;
}

void hd_roots_reset_c(HdRoots *r) {
    for (unsigned s = 0; s < HD_ROOT_STEPS; ++s)
        r->degree[s] = r->note[s] = HD_ROOT_NONE;
    r->state = HD_ROOT_UNKNOWN;
    r->scale = 0;
    r->context = HD_ROOT_NONE;
}
int hd_roots_valid_c(const HdRoots *r) {
    if (r->state > HD_ROOT_HARM || r->scale >= 84 ||
        (r->context >= 64 && r->context != HD_ROOT_NONE)) return 0;
    if (r->state == HD_ROOT_UNKNOWN && r->context != HD_ROOT_NONE) return 0;
    for (unsigned s = 0; s < HD_ROOT_STEPS; ++s) {
        unsigned degree = r->degree[s], note = r->note[s];
        if ((degree >= HD_ROOT_CODES && degree != HD_ROOT_NONE) ||
            (note > 127 && note != HD_ROOT_NONE)) return 0;
        if (r->state != HD_ROOT_HARM && degree != HD_ROOT_NONE) return 0;
        if (r->state == HD_ROOT_HARM &&
            ((note == HD_ROOT_NONE) != (degree == HD_ROOT_NONE))) return 0;
        if (r->state == HD_ROOT_UNKNOWN && note != HD_ROOT_NONE) return 0;
    }
    return 1;
}
int hd_roots_sync_c(HdRoots *r, const uint8_t *notes, uint8_t *result,
                    unsigned harm, unsigned scale, unsigned context) {
    if (harm > 2 || context >= 64 || !scale_valid(scale) || !hd_roots_valid_c(r)) return -1;
    for (unsigned s = 0; s < HD_ROOT_STEPS; ++s)
        if (notes[s] > 127 && notes[s] != HD_ROOT_NONE) return -1;

    unsigned outgoing = unpack_scale(r->scale), changed = 0;
    for (unsigned s = 0; s < HD_ROOT_STEPS; ++s) {
        unsigned note = notes[s], degree = r->degree[s], next = note;
        if (r->state != HD_ROOT_HARM || note != r->note[s])
            degree = (unsigned)hd_encode_c((int)note, (int)(harm ? scale : outgoing));
        if (!harm && r->state == HD_ROOT_HARM && degree < HD_ROOT_CODES)
            next = absolute(degree, outgoing);
        if (next != note) ++changed;
        result[s] = (uint8_t)next;
        r->note[s] = (uint8_t)next;
        r->degree[s] = harm ? (uint8_t)degree : HD_ROOT_NONE;
    }
    r->state = harm ? HD_ROOT_HARM : HD_ROOT_STOCK;
    r->scale = (uint8_t)pack_scale(scale);
    r->context = (uint8_t)context;
    return (int)changed;
}
int hd_roots_detach_c(HdRoots *r, unsigned context, unsigned scale) {
    if (context >= 64 || !scale_valid(scale) || !hd_roots_valid_c(r)) return -1;
    if (r->state == HD_ROOT_UNKNOWN || r->context != context) return 0;
    r->scale = (uint8_t)pack_scale(scale);
    r->context = HD_ROOT_NONE;
    return 1;
}
