/* Current-bank retention only. The P2LK v1 project files are unchanged.
 * P2NV: original sorted 24-bit (index << 7 | value) entries.
 * P2R1: MSB-first Rice(k=3) gaps (ones, zero, 3 remainder bits),
 *       then 7 value bits. Previous index starts at -1. Zero tail padding.
 * Both: big-endian magic, bank, count, sum of decoded 24-bit entries.
 * Publish magic last; validate the entire snapshot before touching STORE.
 */
typedef unsigned char u8;
typedef unsigned int u32;
#define SLOTS 98304u
#define OLD_BYTES 30720u
#define MAX_LOCKS ((OLD_BYTES - 16u) / 3u)
#define PACKED_BYTES 15464u
#define RAW 0x50324e56u
#define RICE 0x50325231u

static u32 read32(const volatile u8 *p)
{
    return (u32)p[0] << 24 | (u32)p[1] << 16 | (u32)p[2] << 8 | p[3];
}

static void write32(volatile u8 *p, u32 v)
{
    p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v;
}

/* Aligned, single-store invalidation/publication on ColdFire. */
static void magic(volatile u8 *p, u32 v)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    v = __builtin_bswap32(v);
#endif
    *(volatile u32 *)p = v;
}

struct writer { volatile u8 *p, *end; u32 byte, bits, failed; };
static void bit(struct writer *w, u32 b)
{
    w->byte = (w->byte << 1) | b;
    if (++w->bits == 8) {
        if (w->p == w->end) { w->failed = 1; return; }
        *w->p++ = w->byte;
        w->bits = w->byte = 0;
    }
}

/* Returns the format magic to publish, or zero on overflow/invalid input.
 * The assembly wrapper owns publication and serializes nested requests.
 * Even if another task edits the table between passes, writes are bounded. */
u32 plk_nv_encode(volatile u8 *nv, const volatile u8 *table, u32 bank)
{
    u32 i, n = 0, sum = 0, prev = 0, bits = 0, bytes, format;
    magic(nv, 0);
    if (bank >= 16) return 0;
    for (i = 0; i < SLOTS; ++i) {
        /* STORE banks are long-aligned. Retain the old writer's fast path
         * across empty words; most step/parameter slots have no lock. */
        if (!(i & 3) && *(const volatile u32 *)(table + i) == 0xffffffffu) {
            i += 3;
            continue;
        }
        u32 v = table[i];
        if (v == 255) continue;
        if (v > 127 || ++n > MAX_LOCKS) return 0;
        bits += 11 + ((i - prev) >> 3);
        prev = i + 1;
        sum += (i << 7) | v;
    }
    bytes = (bits + 7) >> 3;
    format = bytes < 3 * n ? RICE : RAW;
    if (format == RAW) bytes = 3 * n;
    if (bytes > PACKED_BYTES - 16) return 0;
    write32(nv + 4, bank); write32(nv + 8, n); write32(nv + 12, sum);
    if (!n) return format;
    if (format == RAW) {
        volatile u8 *p = nv + 16;
        for (i = 0; i < SLOTS; ++i) {
            if (!(i & 3) && *(const volatile u32 *)(table + i) == 0xffffffffu) {
                i += 3;
                continue;
            }
            u32 v = table[i], entry;
            if (v == 255) continue;
            if (v > 127 || p + 3 > nv + PACKED_BYTES) return 0;
            entry = (i << 7) | v;
            *p++ = entry >> 16; *p++ = entry >> 8; *p++ = entry;
        }
    } else {
        struct writer w = {nv + 16, nv + PACKED_BYTES, 0, 0, 0};
        prev = 0;
        for (i = 0; i < SLOTS; ++i) {
            if (!(i & 3) && *(const volatile u32 *)(table + i) == 0xffffffffu) {
                i += 3;
                continue;
            }
            u32 v = table[i], gap, q, j, tail;
            if (v == 255) continue;
            if (v > 127) return 0;
            gap = i - prev; q = gap >> 3;
            tail = ((gap & 7) << 7) | v;
            prev = i + 1;
            while (q--) bit(&w, 1);
            bit(&w, 0);
            for (j = 10; j; --j) bit(&w, (tail >> (j - 1)) & 1);
            if (w.failed) return 0;
        }
        if (w.bits) {
            if (w.p == w.end) return 0;
            *w.p = w.byte << (8 - w.bits);
        }
    }
    return format;
}

struct reader { const volatile u8 *p; u32 pos, limit; };
static int getbit(struct reader *r)
{
    u32 pos = r->pos;
    if (pos >= r->limit) return -1;
    r->pos = pos + 1;
    return (r->p[pos >> 3] >> (7 - (pos & 7))) & 1;
}

/* available is bounded by the actual old SRAM reservation. It also lets
 * the gate test every truncated input without reading beyond its bytes. */
u32 plk_nv_decode(u8 *table, const volatile u8 *nv, u32 bank, u32 available)
{
    u32 format, n, pass;
    if (available < 16 || bank >= 16) return 0;
    format = read32(nv);
    if (format != RAW && format != RICE) return 0;
    if (read32(nv + 4) != bank) return 0;
    n = read32(nv + 8);
    if (n > MAX_LOCKS) return 0;
    if (available > OLD_BYTES) available = OLD_BYTES;
    if (format == RICE && available > PACKED_BYTES) available = PACKED_BYTES;
    if (format == RAW && n * 3 > available - 16) return 0;
    /* First pass is read-only. A rejected snapshot leaves the whole bank
     * untouched so the caller can take its existing file fallback. */
    for (pass = 0; pass < 2; ++pass) {
        u32 j, next = 0, sum = 0;
        struct reader r = {nv + 16, 0, (available - 16) * 8};
        if (pass) for (j = 0; j < SLOTS; ++j) table[j] = 255;
        for (j = 0; j < n; ++j) {
            u32 index, value, entry;
            if (format == RAW) {
                const volatile u8 *p = nv + 16 + 3 * j;
                entry = (u32)p[0] << 16 | (u32)p[1] << 8 | p[2];
                index = entry >> 7; value = entry & 127;
                if (index < next || index >= SLOTS) return 0;
            } else {
                u32 gap = 0, tail = 0, k;
                int b;
                while ((b = getbit(&r)) == 1) {
                    gap += 8;
                    if (gap >= SLOTS - next) return 0;
                }
                if (b < 0) return 0;
                for (k = 0; k < 10; ++k) {
                    b = getbit(&r);
                    if (b < 0) return 0;
                    tail = (tail << 1) | (u32)b;
                }
                gap += tail >> 7;
                if (gap >= SLOTS - next) return 0;
                index = next + gap; value = tail & 127;
                entry = (index << 7) | value;
            }
            next = index + 1;
            sum += entry;
            if (pass) table[index] = value;
        }
        if (sum != read32(nv + 12)) return 0;
        if (format == RICE) {
            /* Reject nonzero padding in the final byte. Bytes after the
             * stream are unused SRAM and may contain an older snapshot. */
            while (r.pos & 7) if (getbit(&r) != 0) return 0;
        }
    }
    return 1;
}
