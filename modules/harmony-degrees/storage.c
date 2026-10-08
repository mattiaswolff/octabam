/* One validated payload for roots and chord quality. The native bank is
 * still native. Its companion has an independent identity and no legacy
 * migration. The retained copy commits its magic last, under a short mask. */
#include "core.h"

enum { QUALITY_BYTES = 8192, PAYLOAD_BYTES = QUALITY_BYTES + sizeof(HdBank) };
extern uint8_t ch_lock_table[16 * QUALITY_BYTES];
extern uint8_t ch_lock_status[16];
extern volatile uint32_t ch_nv_bank;
static volatile uint32_t generation;
#define NV ((volatile uint32_t *)(uintptr_t)0x100f8600)
#define NV_PAYLOAD ((volatile uint8_t *)(uintptr_t)0x100f8620)
#define MAGIC 0x48444e32u

static uint16_t mask(void) {
    uint16_t sr;
    __asm__ volatile("move.w %%sr,%0\n\tmove.w #0x2700,%%sr" : "=d"(sr) :: "memory");
    return sr;
}
static void unmask(uint16_t sr) {
    __asm__ volatile("move.w %0,%%sr" :: "d"(sr) : "memory");
}
static uint32_t hash(const volatile uint8_t *p, unsigned n, uint32_t h) {
    while (n--) h = (h ^ *p++) * 0x01000193u;
    return h;
}
int hd_payload_valid_c(const uint8_t *p) {
    for (unsigned i = 0; i < QUALITY_BYTES; ++i)
        if (p[i] > 7 && p[i] != 255) return 0;
    return hd_validate_c((const HdBank *)(p + QUALITY_BYTES));
}
uint32_t hd_payload_hash_c(const uint8_t *p) {
    return hash(p, PAYLOAD_BYTES, 0x811c9dc5u);
}
void hd_export_c(unsigned bank, uint8_t *p) {
    if (bank >= 16) return;
    hd_checkpoint_c(bank);
    const uint8_t *src = (const uint8_t *)&hd_banks[bank];
    uint32_t ticket;
    do {
        ticket = hd_revision_c(bank);
        for (unsigned i = 0; i < sizeof(HdBank); ++i) p[i] = src[i];
    } while (ticket != hd_revision_c(bank));
}
void hd_import_c(unsigned bank, const uint8_t *p) {
    if (bank >= 16 || !hd_validate_c((const HdBank *)p)) return;
    uint8_t *dst = (uint8_t *)&hd_banks[bank];
    for (unsigned i = 0; i < sizeof(HdBank); ++i) dst[i] = p[i];
    hd_bank_loaded_c(bank);
}
uint32_t hd_native_hash_c(unsigned bank, uint32_t h) {
    if (bank >= 16) return 0;
    /* The caller fingerprints pattern NOTE/trig data. Reassigning a Part
     * slot or changing its defaults must not invalidate explicit locks. */
    return h;
}
void hd_nv_save_c(unsigned bank) {
    if (bank >= 16) return;
    hd_checkpoint_c(bank);
    uint16_t sr = mask();
    ch_nv_bank = bank;
    ++generation;
    unmask(sr);
    for (;;) {
        uint32_t ticket = generation;
        bank = ch_nv_bank;
        uint32_t roots_ticket = hd_revision_c(bank);
        NV[0] = 0;
        const volatile uint8_t *q = ch_lock_table + bank*QUALITY_BYTES;
        const volatile uint8_t *d = (const uint8_t *)&hd_banks[bank];
        uint32_t sum = 0x811c9dc5u;
        unsigned i;
        for (i = 0; i < PAYLOAD_BYTES; ++i) {
            if (ticket != generation) break;
            uint8_t v = i < QUALITY_BYTES ? q[i] : d[i-QUALITY_BYTES];
            NV_PAYLOAD[i] = v;
            sum = (sum ^ v) * 0x01000193u;
        }
        sr = mask();
        if (i == PAYLOAD_BYTES && ticket == generation && roots_ticket == hd_revision_c(bank)) {
            NV[1] = 2;
            NV[2] = bank;
            NV[3] = PAYLOAD_BYTES;
            NV[4] = sum;
            NV[5] = ticket;
            NV[6] = ch_lock_status[bank];
            NV[7] = ~NV[6];
            NV[0] = MAGIC;
            unmask(sr);
            return;
        }
        unmask(sr);
    }
}
int hd_nv_restore_c(unsigned bank) {
    if (bank >= 16 || NV[0] != MAGIC || NV[1] != 2 || NV[2] != bank ||
        NV[3] != PAYLOAD_BYTES || NV[6] > 4 || NV[7] != ~NV[6] ||
        NV[4] != hash(NV_PAYLOAD, PAYLOAD_BYTES, 0x811c9dc5u) ||
        !hd_payload_valid_c((const uint8_t *)NV_PAYLOAD)) return 0;
    /* Restore runs on the serialized bank-load path; no live publication
     * occurs until every byte and both representations have been checked. */
    for (unsigned i = 0; i < QUALITY_BYTES; ++i)
        ch_lock_table[bank*QUALITY_BYTES+i] = NV_PAYLOAD[i];
    uint8_t *d = (uint8_t *)&hd_banks[bank];
    for (unsigned i = 0; i < sizeof(HdBank); ++i) d[i] = NV_PAYLOAD[QUALITY_BYTES+i];
    ch_lock_status[bank] = (uint8_t)NV[6];
    ch_nv_bank = bank;
    hd_bank_loaded_c(bank);
    return 1;
}
