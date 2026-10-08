/* NOTE-page degree values and edits. The panel wrappers own native redraw,
 * lock-indicator and trigless-lock lifecycle calls. */
#include "core.h"
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define WORD(a) (*(volatile uint16_t *)(uintptr_t)(a))
#define LONG(a) (*(volatile uint32_t *)(uintptr_t)(a))

int hd_ui_value_c(int step) {
    unsigned bank = BYTE(0x80000002), pattern = BYTE(0x100b14d0);
    unsigned track = BYTE(0x100b14cc), part = BYTE(0x100b14cf) & 3;
    if (step < 0) return hd_base_c(bank,part,track);
    int lock = hd_lock_c(bank,pattern,track,(unsigned)step);
    return lock >= 0 ? lock | 256 : hd_degree_c(bank,pattern,track,(unsigned)step);
}
static int advance(int code, int delta) {
    if (code < 0) code = 35; /* sensible editable fallback: 1:3 */
    if (delta > 83) delta = 83;
    if (delta < -83) delta = -83;
    code += delta;
    return code < 0 ? 0 : code >= HD_CODES ? HD_CODES-1 : code;
}
int hd_ui_edit_c(int delta, int toggle, int steps) {
    unsigned bank = BYTE(0x80000002), pattern = BYTE(0x100b14d0);
    unsigned track = BYTE(0x100b14cc), part = BYTE(0x100b14cf) & 3;
    if (track >= 8 || !hd_type_c(track) || (!delta && !toggle)) return 0;
    if (!steps) {
        hd_edit_base_c(bank,part,track,advance(hd_base_c(bank,part,track),delta));
        return 1;
    }
    unsigned mask = WORD(0x460d174a), start = LONG(0x460d174c), changed = 0;
    for (unsigned i = 0; i < 16; ++i) {
        unsigned step = start+i;
        if (!(mask & (1u << i)) || step >= 64) continue;
        int code = hd_degree_c(bank,pattern,track,step);
        if (toggle && hd_lock_c(bank,pattern,track,step) >= 0) code = HD_NONE;
        else code = advance(code,delta);
        hd_edit_step_c(bank,pattern,track,step,code);
        changed = 1;
    }
    return (int)changed;
}
