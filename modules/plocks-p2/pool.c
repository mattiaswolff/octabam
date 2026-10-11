/* P2S1: header in dedicated SRAM, codec payload in protected MIDI padding.
 * P2LK files and the full 10,234-lock capacity remain unchanged. The caller
 * serializes writers and publishes the magic only after its generation check.
 */
typedef unsigned char u8;
typedef unsigned int u32;
#define BYTES 15464u
#define POOLED 0x50325331u
extern u32 plk_nv_encode(volatile u8 *, const volatile u8 *, u32);
extern u32 plk_nv_decode(u8 *, const volatile u8 *, u32, u32);
extern int rp_write(const u8 *, u32, u32);
extern int rp_read(u8 *, u32, u32);
static u32 staging[BYTES/4];

u32 plk_pool_encode(volatile u8 *nv, const volatile u8 *table, u32 bank)
{
    volatile u32 *header=(volatile u32 *)nv;
    u32 format=plk_nv_encode((u8 *)staging,table,bank);
    if (!format || !rp_write((u8 *)staging+16,0,BYTES-16)) return 0;
    header[1]=format;
    header[2]=staging[1]; header[3]=staging[2]; header[4]=staging[3];
    return POOLED;
}

u32 plk_pool_decode(u8 *table, const volatile u8 *nv, u32 bank, u32 available)
{
    const volatile u32 *header=(const volatile u32 *)nv;
    if (header[0]!=POOLED) return plk_nv_decode(table,nv,bank,available);
    staging[0]=header[1]; staging[1]=header[2];
    staging[2]=header[3]; staging[3]=header[4];
    if (!rp_read((u8 *)staging+16,0,BYTES-16)) return 0;
    return plk_nv_decode(table,(u8 *)staging,bank,BYTES);
}
