/* Android effect ABI subset. Declarations follow AOSP audio_effect.h (Apache-2.0).
 * This module targets the inspected 32-bit legacy vendor effect service.
 */
#ifndef SPATIAL_EFFECT_ABI_H
#define SPATIAL_EFFECT_ABI_H
typedef unsigned int u32;
typedef int i32;
typedef unsigned short u16;
typedef unsigned char u8;
#ifdef SPATIAL_COMPAT_HOST_TEST
typedef __SIZE_TYPE__ usize;
#else
typedef unsigned int usize;
#endif
struct uuid { u32 low; u16 mid, high, seq; u8 node[6]; };
struct descriptor { struct uuid type, implementation; u32 api, flags; u16 cpu, memory; char name[64], implementor[64]; };
struct buffer { usize frames; void *data; };
struct config_one { struct buffer buffer; u32 rate, channels; void *get, *release, *cookie; u8 format, access; u16 mask; };
struct config { struct config_one input, output; };
struct interface;
typedef struct interface **handle;
struct interface {
    i32 (*process)(handle, struct buffer *, struct buffer *);
    i32 (*command)(handle, u32, u32, void *, u32 *, void *);
    i32 (*descriptor)(handle, struct descriptor *);
    i32 (*reverse)(handle, struct buffer *, struct buffer *);
};
struct library { u32 tag, version; const char *name, *implementor;
    i32 (*create)(const struct uuid *, i32, i32, handle *);
    i32 (*release)(handle); i32 (*descriptor)(const struct uuid *, struct descriptor *); void *create31; };
#ifndef SPATIAL_COMPAT_HOST_TEST
typedef char pointer_size_must_be_4[sizeof(void *)==4 ? 1 : -1];
typedef char config_one_must_be_32[sizeof(struct config_one)==32 ? 1 : -1];
typedef char config_must_be_64[sizeof(struct config)==64 ? 1 : -1];
typedef char descriptor_must_be_172[sizeof(struct descriptor)==172 ? 1 : -1];
#endif
#endif
