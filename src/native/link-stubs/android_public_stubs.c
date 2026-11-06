/* Link-time declarations only. NEVER ship or execute the resulting stub DSOs.
 * These public Bionic functions are resolved from Android's real libc/libdl.
 * The diagnostic needs explicit DT_NEEDED entries in its own local load group.
 */
typedef unsigned int usize;
#ifdef STUB_LIBDL
void *dlopen(const char *path, int flags) { (void)path; (void)flags; return (void *)0; }
void *dlsym(void *handle, const char *name) { (void)handle; (void)name; return (void *)0; }
char *dlerror(void) { return (char *)0; }
#else
int puts(const char *text) { (void)text; return -1; }
int fflush(void *stream) { (void)stream; return -1; }
int printf(const char *format, ...) { (void)format; return -1; }
int snprintf(char *out, usize size, const char *format, ...) { (void)out; (void)size; (void)format; return -1; }
void *calloc(usize count, usize size) { (void)count; (void)size; return (void *)0; }
void free(void *memory) { (void)memory; }
int pthread_once(volatile int *control, void (*initialize)(void)) { (void)control; (void)initialize; return -1; }
void *fopen(const char *path, const char *mode) { (void)path; (void)mode; return (void *)0; }
usize fread(void *out, usize size, usize count, void *file) { (void)out; (void)size; (void)count; (void)file; return 0; }
usize fwrite(const void *data, usize size, usize count, void *file) { (void)data; (void)size; (void)count; (void)file; return 0; }
int fclose(void *file) { (void)file; return -1; }
#endif
