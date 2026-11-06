/* Contract tests for the actual adapter, with only the OEM DSP mocked. */
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define SPATIAL_COMPAT_HOST_TEST
#define dlopen test_dlopen
#define dlsym test_dlsym
#define pthread_once test_once
#include "../src/native/spatial_compat.c"

struct fake_context { struct interface *itfe; };
static int loads,releases,injections,config_error,transport_error,injection_error;
static int metadata_error,metadata_transport,metadata_calls,init_error,reset_calls,short_injection;
static u32 expected_counts[4],expected_size,expected_pos;
static struct config *expected_config;
static struct buffer *expected_in,*expected_out;
static const struct uuid *expected_id;
static const struct uuid id={0xde4d6aaf,0x4e9d,0x473d,0x8168,{0x4c,0xe9,0x2d,0x50,0xa6,0x37}};
static struct descriptor original_descriptor;
static void expect_counts(u32 a,u32 b) {
    assert(expected_pos==expected_size);
    expected_size=a ? (b ? 2:1):0;expected_pos=0;
    expected_counts[0]=a;expected_counts[1]=b;
}
static void done(void) {assert(expected_pos==expected_size);}
static i32 fake_process(handle h,struct buffer *in,struct buffer *out) {
    assert(h && in==expected_in && out==expected_out);return 57;
}
static i32 fake_descriptor(handle h,struct descriptor *out) {assert(h);*out=original_descriptor;return 0;}
static i32 fake_command(handle h,u32 command,u32 bytes,void *data,u32 *reply_bytes,void *reply) {
    assert(h);
    if(command==1) {
        assert(bytes==sizeof(struct config) && data==expected_config);
        *(i32 *)reply=config_error;*reply_bytes=4;return transport_error;
    }
    if(command==5) {
        if(read_word(data,12)==CHANNEL_COUNT_PARAM) {
            assert(bytes==20 && read_word(data,4)==4 && read_word(data,8)==4);
            assert(expected_pos<expected_size && read_word(data,16)==expected_counts[expected_pos++]);
            injections++;*(i32 *)reply=injection_error;*reply_bytes=short_injection ? 0:4;return 0;
        }
        metadata_calls++;*(i32 *)reply=metadata_error;*reply_bytes=4;return metadata_transport;
    }
    if(command==0) {*(i32 *)reply=init_error;*reply_bytes=4;return 0;}
    if(command==2) {reset_calls++;return 0;}
    assert(command==9 && bytes==4 && !reply_bytes && !reply);return 17;
}
static struct interface fake_interface={fake_process,fake_command,fake_descriptor,0};
static i32 fake_create(const struct uuid *which,i32 session,i32 io,handle *out) {
    assert(which==expected_id && session==123 && io==42);
    struct fake_context *c=calloc(1,sizeof(*c));assert(c);c->itfe=&fake_interface;*out=(handle)c;return 0;
}
static i32 fake_release(handle h) {assert(h);releases++;free(h);return 0;}
static i32 fake_library_descriptor(const struct uuid *which,struct descriptor *out) {
    assert(which==expected_id);*out=original_descriptor;return 0;
}
static struct library fake_library={0x41454c54,0x30000,"fake","fake",fake_create,fake_release,fake_library_descriptor,0};
void *test_dlopen(const char *path,int flags) {assert(!strcmp(path,OEM_LIBRARY_PATH) && flags==2);loads++;return (void *)1;}
void *test_dlsym(void *h,const char *name) {assert(h==(void *)1 && !strcmp(name,"AELI"));return &fake_library;}
int test_once(volatile int *control,void (*fn)(void)) {if(!*control){fn();*control=1;}return 0;}
static void configure(handle h,u32 mask,i32 error) {
    struct config cfg={0};cfg.input.channels=mask;expected_config=&cfg;
    u32 bytes=4;i32 status=-99;
    assert((*h)->command(h,1,sizeof(cfg),&cfg,&bytes,&status)==transport_error);
    if(!transport_error) assert(status==error && bytes==4);
    done();
}
static void metadata(handle h,const u32 *masks,u32 count,i32 error) {
    u32 p[12]={0,4,0,12};assert(count<=8);p[2]=count*4;
    for(u32 n=0;n<count;n++)p[n+4]=masks[n];
    u32 bytes=4;i32 status=-99;
    assert((*h)->command(h,5,16+count*4,p,&bytes,&status)==metadata_transport);
    if(!metadata_transport)assert(status==error && bytes==4);
    done();
}
static void malformed(handle h,u32 size,void *p) {
    u32 bytes=4;i32 status=-99;int before=metadata_calls;
    assert((*h)->command(h,5,size,p,&bytes,&status)==-22 && status==-99);
    assert(before==metadata_calls);done();
}
int main(void) {
    expected_id=&id;memset(&original_descriptor,0x5a,sizeof(original_descriptor));
    struct descriptor d;
    assert(AELI.descriptor(&id,&d)==0 && !memcmp(&d,&original_descriptor,sizeof(d)));
    assert(AELI.create(&id,123,42,0)==-22);
    handle h=0;assert(AELI.create(&id,123,42,&h)==0 && h && !(*h)->reverse);
    assert((*h)->descriptor(h,&d)==0 && !memcmp(&d,&original_descriptor,sizeof(d)));
    const u32 stereo[]={3,3},multi[]={0x63f},mixed[]={3,0x3f},unknown[]={0x80000003};
    const u32 masks[]={3,0x3f,0x63f,0x2d63f,3},counts[]={2,6,8,12,2};
    for(int i=0;i<5;i++){expect_counts(counts[i],0);configure(h,masks[i],0);}
    expect_counts(12,0);configure(h,0x2d63f,0);
    expect_counts(2,0);metadata(h,stereo,1,0);
    expect_counts(0,0);metadata(h,stereo,1,0);metadata(h,stereo,2,0);metadata(h,0,0,0);
    assert(context_of(h)->current_count==2);
    assert((*h)->command(h,2,0,0,0,0)==0 && reset_calls==1 && context_of(h)->current_count==2);
    expect_counts(12,2);configure(h,0x2d63f,0); /* Reconfiguration reapplies remembered track type. */
    expect_counts(12,0);metadata(h,multi,1,0);
    expect_counts(0,0);metadata(h,mixed,2,0);metadata(h,unknown,1,0);
    expect_counts(2,0);metadata(h,stereo,1,0);
    expect_counts(12,0);metadata(h,mixed,2,0);
    expect_counts(0,0);metadata(h,0,0,0);
    /* A failed OEM metadata command never changes the adapter's track state. */
    metadata_error=-38;metadata(h,stereo,1,-38);metadata_error=0;
    metadata_transport=-7;metadata(h,stereo,1,0);metadata_transport=0;
    assert(!context_of(h)->stereo_only && context_of(h)->current_count==12);
    /* Failed injections are surfaced and retried on the next identical metadata. */
    injection_error=-38;expect_counts(2,0);metadata(h,stereo,1,-38);
    assert(context_of(h)->current_count==12);injection_error=0;
    expect_counts(2,0);metadata(h,stereo,1,0);
    expect_counts(12,0);metadata(h,multi,1,0);
    short_injection=1;expect_counts(2,0);metadata(h,stereo,1,-22);short_injection=0;
    expect_counts(2,0);metadata(h,stereo,1,0);
    /* Limit the new translation to the phone-tested 12-channel config. */
    expect_counts(8,0);configure(h,0x63f,0);expect_counts(0,0);metadata(h,stereo,1,0);
    expect_counts(6,0);configure(h,0x3f,0);expect_counts(0,0);metadata(h,stereo,1,0);
    expect_counts(2,0);configure(h,3,0);expect_counts(0,0);metadata(h,stereo,1,0);
    /* INIT clears metadata only on success; RESET leaves it to the OEM. */
    u32 bytes=4;i32 status=-99;
    init_error=-22;assert((*h)->command(h,0,0,0,&bytes,&status)==0 && status==-22);
    assert(context_of(h)->have_metadata);init_error=0;
    assert((*h)->command(h,0,0,0,&bytes,&status)==0 && status==0);
    assert(!context_of(h)->have_metadata && !context_of(h)->configured_count);
    expect_counts(0,0);metadata(h,stereo,1,0); /* Metadata before configuration is remembered. */
    expect_counts(12,2);configure(h,0x2d63f,0);
    config_error=-22;expect_counts(0,0);configure(h,3,-22);config_error=0;
    transport_error=-7;configure(h,3,0);transport_error=0;
    injection_error=-38;expect_counts(12,0);configure(h,0x2d63f,-38);injection_error=0;
    expect_counts(0,0);configure(h,0xdead,-22);
    assert((*h)->command(h,1,0,0,0,0)==-22);
    /* Bounds cover truncated, overflowing, misaligned and invalid key-12 values. */
    u32 bad[]={0,4,4,12,3};
    malformed(h,0,0);malformed(h,11,bad);malformed(h,15,bad);malformed(h,19,bad);
    bad[1]=0xffffffff;malformed(h,20,bad);bad[1]=8;malformed(h,20,bad);
    bad[1]=4;bad[2]=3;malformed(h,20,bad);bad[2]=0xffffffff;malformed(h,20,bad);
    /* Non-key-12 parameters retain their exact command payload. */
    bad[2]=4;bad[3]=1;bytes=4;status=-99;int before=metadata_calls;
    assert((*h)->command(h,5,20,bad,&bytes,&status)==0 && status==0 && metadata_calls==before+1);
    u32 device=0x4000000;
    assert((*h)->command(h,9,4,&device,0,0)==17);
    float input[8]={0},output[8]={0};
    struct buffer in={4,input},out={4,output};expected_in=&in;expected_out=&out;
    assert((*h)->process(h,&in,&out)==57 && in.data==input && out.data==output);
    handle second=0;assert(AELI.create(&id,123,42,&second)==0 && loads==1);
    assert(!context_of(second)->have_metadata && context_of(h)->have_metadata);
    assert(AELI.release(second)==0 && AELI.release(h)==0 && releases==2 && loads==1);
    printf("PASS adapter: %d OEM initializations; stereo/multichannel transitions, tails, config/INIT/RESET, per-instance state, failures and bounds; buffers/descriptors unchanged.\n",injections);
}
