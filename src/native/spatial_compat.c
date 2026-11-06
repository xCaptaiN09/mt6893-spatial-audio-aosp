/* MT6893 Spatial Audio AOSP compatibility adapter.
 * Initializes OEM channels after SET_CONFIG and translates confirmed stereo
 * track metadata inside the inspected 12-channel AOSP mixer configuration.
 * Audio buffers, descriptors and other valid commands are forwarded unchanged.
 * No tuning, audio-device, global-setting, thread or service-management code.
 */
#include "spatial_effect_abi.h"
extern void *calloc(usize, usize);
extern void free(void *);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern int pthread_once(volatile int *, void (*)(void));

#define OEM_LIBRARY_PATH "/vendor/lib/soundfx/liboplus_spatializer.so"
#define CHANNEL_COUNT_PARAM 0x100100BAu
#define INPUT_CHANNEL_MASK_PARAM 12u
static volatile int load_once;
static struct library *oem;

static void load_library(void) {
    void *loaded=dlopen(OEM_LIBRARY_PATH,2); /* RTLD_NOW | RTLD_LOCAL */
    if(!loaded) return;
    struct library *candidate=(struct library *)dlsym(loaded,"AELI");
    if(candidate && candidate->tag==0x41454c54u && (candidate->version>>16)==3 &&
       candidate->create && candidate->release && candidate->descriptor) oem=candidate;
    /* Retain the DSO for the HAL process lifetime, including its descriptors. */
}
static int ensure_library(void) {
    return pthread_once(&load_once,load_library)==0 && oem ? 0 : -19;
}

struct context {
    struct interface *itfe; struct interface callbacks; handle inner;
    u32 configured_count, current_count;
    int have_metadata, stereo_only;
};
static struct context *context_of(handle h) {
    struct context *c=(struct context *)h;
    return c && c->inner && *c->inner ? c : (struct context *)0;
}
static i32 forward_process(handle h,struct buffer *in,struct buffer *out) {
    struct context *c=context_of(h);
    return c && (*c->inner)->process ? (*c->inner)->process(c->inner,in,out) : -22;
}
static i32 forward_reverse(handle h,struct buffer *in,struct buffer *out) {
    struct context *c=context_of(h);
    return c && (*c->inner)->reverse ? (*c->inner)->reverse(c->inner,in,out) : -38;
}
static i32 forward_descriptor(handle h,struct descriptor *d) {
    struct context *c=context_of(h);
    return c && (*c->inner)->descriptor ? (*c->inner)->descriptor(c->inner,d) : -22;
}
static u32 input_channels(u32 mask) {
    switch(mask) {case 3:return 2;case 0x3f:return 6;case 0x63f:return 8;case 0x2d63f:return 12;default:return 0;}
}
static i32 initialize_channels(struct context *c,u32 count) {
    struct {i32 status;u32 psize,vsize,key,value;} parameter={0,4,4,CHANNEL_COUNT_PARAM,count};
    u32 bytes=4;i32 status=-22;
    i32 rc=(*c->inner)->command(c->inner,5,sizeof(parameter),&parameter,&bytes,&status);
    i32 result=rc ? rc : bytes!=4 ? -22 : status;
    if(!result) c->current_count=count;
    return result;
}
/* Android's effect_param_t header and masks use native 32-bit words. Reading
   bytes avoids alignment assumptions for the variable-length packet. */
static u32 read_word(const void *data,u32 offset) {
    const u8 *p=(const u8 *)data+offset;
    return (u32)p[0]|((u32)p[1]<<8)|((u32)p[2]<<16)|((u32)p[3]<<24);
}
static u32 desired_count(const struct context *c) {
    /* Only this 12-channel stereo translation has private phone PCM evidence.
       Any mixed, multichannel or unknown mask retains the full mixer layout. */
    return c->configured_count==12 && c->have_metadata && c->stereo_only ? 2 : c->configured_count;
}
static i32 forward_command(handle h,u32 command,u32 bytes,void *data,u32 *reply_bytes,void *reply) {
    struct context *c=context_of(h);
    if(!c || !(*c->inner)->command) return -22;
    if(command==1 && (!data || bytes!=sizeof(struct config) || !reply_bytes || !reply || *reply_bytes<4)) return -22;
    int metadata=0,stereo_only=0;
    u32 values=0;
    if(command==5) {
        /* Validate lengths before either adapter or OEM sees a SET_PARAM.
           Subtraction-based bounds prevent overflow in attacker-sized words. */
        if(!data || bytes<12 || !reply_bytes || !reply || *reply_bytes<4) return -22;
        u32 psize=read_word(data,4),vsize=read_word(data,8);
        if(psize>bytes-12 || psize>0xfffffffcu) return -22;
        u32 aligned=(psize+3u)&~3u;
        if(aligned>bytes-12 || vsize>bytes-12-aligned) return -22;
        if(psize>=4 && read_word(data,12)==INPUT_CHANNEL_MASK_PARAM) {
            if(psize!=4 || (vsize&3u)) return -22;
            metadata=1;values=vsize/4;stereo_only=values!=0;
            for(u32 n=0;n<values;n++)
                if(read_word(data,16+n*4)!=3u) stereo_only=0;
        }
    }
    i32 rc=(*c->inner)->command(c->inner,command,bytes,data,reply_bytes,reply);
    if(rc || !reply_bytes || !reply || *reply_bytes!=4 || read_word(reply,0)!=0) return rc;
    i32 initialized=0;
    if(command==0) {
        /* INIT resets the OEM instance. RESET (command 2) retains its layout. */
        c->configured_count=0;c->current_count=0;c->have_metadata=0;c->stereo_only=0;
    } else if(command==1) {
        c->configured_count=input_channels(((struct config *)data)->input.channels);
        c->current_count=0;
        initialized=c->configured_count ? initialize_channels(c,c->configured_count) : -22;
        if(!initialized && desired_count(c)!=c->current_count)
            initialized=initialize_channels(c,desired_count(c));
    } else if(metadata && values) {
        /* Empty active-track metadata must not change the mode while tails
           drain. Nonempty metadata is remembered across reconfiguration. */
        c->have_metadata=1;c->stereo_only=stereo_only;
        u32 count=desired_count(c);
        if(count && count!=c->current_count) initialized=initialize_channels(c,count);
    }
    if(initialized) *(i32 *)reply=initialized; /* Surface errors to AudioFlinger. */
    return rc;
}
static i32 create(const struct uuid *id,i32 session,i32 io,handle *out) {
    if(!out) return -22;
    *out=(handle)0;
    if(ensure_library()) return -19;
    handle inner=(handle)0;
    i32 rc=oem->create(id,session,io,&inner);
    if(rc) return rc;
    if(!inner || !*inner) return -19;
    struct context *c=calloc(1,sizeof(*c));
    if(!c) {oem->release(inner);return -12;}
    c->inner=inner;c->callbacks=**inner;c->itfe=&c->callbacks;
    c->callbacks.process=forward_process;
    c->callbacks.command=forward_command;
    c->callbacks.descriptor=forward_descriptor;
    c->callbacks.reverse=(*inner)->reverse ? forward_reverse : (void *)0;
    *out=(handle)c;
    return 0;
}
static i32 release(handle h) {
    struct context *c=context_of(h);
    if(!c || !oem) return -22;
    i32 rc=oem->release(c->inner);
    free(c);
    return rc;
}
static i32 descriptor(const struct uuid *id,struct descriptor *out) {
    return ensure_library() ? -19 : oem->descriptor(id,out);
}
__attribute__((visibility("default"))) struct library AELI={
    0x41454c54u,0x00030000u,"MT6893 AOSP Spatial compatibility","xCaptaiN09",
    create,release,descriptor,(void *)0
};
