/* Real Linux control: private RX mutation persists through a loader boundary.
 * This Source-owned fixture never changes the official Crossref executable.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

__attribute__((noinline, aligned(64)))
static int drift_target(int value) {
    return value + 73;
}

int main(int argc, char **argv) {
    if (argc != 2 || (strcmp(argv[1], "clean") && strcmp(argv[1], "drift"))) return 2;
    int drift = !strcmp(argv[1], "drift");
    if (drift_target(2) != 75) return 3;
    if (drift) {
        long page = sysconf(_SC_PAGESIZE);
        uintptr_t address = (uintptr_t)(void (*)(void))drift_target;
        if (page <= 0 || (page != 4096 && page != 16384 && page != 65536)) return 4;
        uintptr_t start = address / (uintptr_t)page * (uintptr_t)page;
        if (mprotect((void *)start, (size_t)page, PROT_READ | PROT_WRITE | PROT_EXEC)) return 5;
        volatile unsigned char *code = (volatile unsigned char *)address;
        *code = (unsigned char)(*code ^ 1u);
        __builtin___clear_cache((char *)address, (char *)address + 1);
        if (mprotect((void *)start, (size_t)page, PROT_READ | PROT_EXEC)) return 6;
        /* The changed function is deliberately never called again. The
         * physical ELF and its RX map metadata retain their original values. */
    }
    if (puts("persistent-rx-ready") == EOF || fflush(stdout)) return 7;
    /* libm is not linked by this fixture. Its real dlopen invokes the actual
     * auditor's later LA_ACT_CONSISTENT boundary with the drift still present. */
    void *loaded = dlopen("libm.so.6", RTLD_NOW | RTLD_LOCAL);
    if (loaded == NULL) return 8;
    if (dlclose(loaded)) return 9;
    if (puts(drift ? "persistent-rx-drift" : "persistent-rx-clean") == EOF) return 10;
    return 0;
}
