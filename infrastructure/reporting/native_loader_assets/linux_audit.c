/* Source-owned glibc loader observation. Never substitutes symbols or paths.
 * Qualification only: original executable is unchanged; the audited process
 * blocks at each callback until its actual parent retains the exact record.
 * No libc/DT_NEEDED: fixed x86_64/aarch64 Linux raw syscalls avoid an unobserved
 * audit namespace dependency. Compile with the Source-owned flags in Python.
 */
#define _GNU_SOURCE 1
#include <elf.h>
#include <link.h>
#include <stdint.h>
#include <stddef.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/uio.h>
#include <poll.h>
#include <fcntl.h>
#include <asm/unistd.h>

#if !defined(__linux__) || (!defined(__x86_64__) && !defined(__aarch64__))
#error "Only the reviewed little-endian Linux x86_64/aarch64 ABI is supported"
#endif
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Loader protocol requires the reviewed little-endian ABI"
#endif

#define MAX_ENV 65536
#define MAX_PATH 4096
#define MAX_OBJECTS 4096
#define MAX_EVENTS 32768
#define MAX_SEGMENTS 128
#define MAX_IMAGE (512ULL * 1024 * 1024)
#define MAX_MEMORY (128ULL * 1024 * 1024)
#define MAGIC "TLDOBS1"
#define HELLO 1
#define OPEN 2
#define CLOSE 3
#define ACTIVITY 4
#define PREINIT 5
#define DONE 6

/* Exact protocol words are explicitly encoded, never native-struct padding. */
static int channel = -1;
static uint64_t sequence, objects, active, deadline_ns, owner_pid;
static char token[64], environment[MAX_ENV];
static unsigned char busy;

static long call6(long n, long a, long b, long c, long d, long e, long f) {
#if defined(__x86_64__)
    register long r10 __asm__("r10") = d;
    register long r8 __asm__("r8") = e;
    register long r9 __asm__("r9") = f;
    long out;
    __asm__ volatile("syscall" : "=a"(out) : "a"(n), "D"(a), "S"(b), "d"(c),
                     "r"(r10), "r"(r8), "r"(r9) : "rcx", "r11", "memory");
    return out;
#else
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    register long x8 __asm__("x8") = n;
    __asm__ volatile("svc 0" : "+r"(x0) : "r"(x1), "r"(x2), "r"(x3), "r"(x4),
                     "r"(x5), "r"(x8) : "memory", "cc");
    return x0;
#endif
}
static void fail(void) {
    call6(__NR_exit_group, 125, 0, 0, 0, 0, 0);
    __builtin_unreachable();
}
static size_t length(const char *s, size_t bound) {
    size_t n = 0;
    while (n < bound && s[n]) ++n;
    if (n == bound) fail();
    return n;
}
static int equal(const char *a, const char *b, size_t n) {
    for (size_t i = 0; i < n; ++i) if (a[i] != b[i]) return 0;
    return 1;
}
static void copy(void *to, const void *from, size_t n) {
    unsigned char *a = to;
    const unsigned char *b = from;
    for (size_t i = 0; i < n; ++i) a[i] = b[i];
}
static void zero(void *to, size_t n) {
    unsigned char *a = to;
    for (size_t i = 0; i < n; ++i) a[i] = 0;
}
static uint64_t now(void) {
    struct { int64_t seconds, nanos; } t;
    if (call6(__NR_clock_gettime, 1, (long)&t, 0, 0, 0, 0) != 0 || t.seconds < 0 ||
        t.nanos < 0 || t.nanos >= 1000000000) fail();
    return (uint64_t)t.seconds * 1000000000ULL + (uint64_t)t.nanos;
}
static void ready(short events) {
    uint64_t current = now();
    if (current >= deadline_ns) fail();
    uint64_t delta = (deadline_ns - current + 999999) / 1000000;
    struct pollfd p = { channel, events, 0 };
    struct { int64_t seconds, nanos; } t = {
        (int64_t)(delta / 1000), (int64_t)(delta % 1000) * 1000000
    };
    long r = call6(__NR_ppoll, (long)&p, 1, (long)&t, 0, 0, 0);
    if (r != 1 || (p.revents & (POLLERR | POLLHUP | POLLNVAL)) || !(p.revents & events)) fail();
}
static void send_all(const void *bytes, size_t size) {
    const unsigned char *p = bytes;
    while (size) {
        ready(POLLOUT);
        long n = call6(__NR_sendto, channel, (long)p, size, MSG_NOSIGNAL | MSG_DONTWAIT, 0, 0);
        if (n == -11 || n == -4) continue;
        if (n <= 0 || (uint64_t)n > size) fail();
        p += n; size -= (size_t)n;
    }
}
static void word(unsigned char *p, uint64_t n) {
    for (unsigned i = 0; i < 8; ++i) { p[i] = (unsigned char)n; n >>= 8; }
}
static const char *get(const char *name) {
    size_t wanted = length(name, 128), i = 0;
    while (i < MAX_ENV && environment[i]) {
        size_t n = length(environment + i, MAX_ENV - i);
        if (n > wanted && equal(environment + i, name, wanted) && environment[i + wanted] == '=')
            return environment + i + wanted + 1;
        i += n + 1;
    }
    fail();
}
static uint64_t number(const char *s) {
    size_t n = length(s, 32);
    uint64_t v = 0;
    if (!n) fail();
    for (size_t i = 0; i < n; ++i) {
        if (s[i] < '0' || s[i] > '9' || v > (UINT64_MAX - 9) / 10) fail();
        v = v * 10 + (uint64_t)(s[i] - '0');
    }
    return v;
}
static void acknowledge(void) {
    unsigned char response = 0;
    for (;;) {
        ready(POLLIN);
        long n = call6(__NR_recvfrom, channel, (long)&response, 1, MSG_DONTWAIT, 0, 0);
        if (n == -11 || n == -4) continue;
        if (n != 1 || response != 0xa5) fail();
        break;
    }
    if (now() >= deadline_ns) fail();
}
static void header(uint64_t kind, uint64_t id, uint64_t base, uint64_t ns,
                   size_t path_size, size_t segments, int descriptor) {
    if (++sequence > MAX_EVENTS) fail();
    unsigned char frame[152];
    zero(frame, sizeof frame);
    copy(frame, MAGIC, 7);
    uint64_t words[10] = { sequence, owner_pid, now(), kind, id, base, ns,
                          path_size, segments, descriptor >= 0 };
    for (unsigned i = 0; i < 10; ++i) word(frame + 8 + 8 * i, words[i]);
    copy(frame + 88, token, sizeof token);
    if (descriptor < 0) { send_all(frame, sizeof frame); return; }
    union { struct cmsghdr alignment; unsigned char bytes[CMSG_SPACE(sizeof(int))]; } control;
    zero(&control, sizeof control);
    struct iovec vector = { frame, sizeof frame };
    struct msghdr message;
    zero(&message, sizeof message);
    message.msg_iov = &vector; message.msg_iovlen = 1;
    message.msg_control = control.bytes; message.msg_controllen = sizeof control.bytes;
    struct cmsghdr *c = CMSG_FIRSTHDR(&message);
    c->cmsg_level = SOL_SOCKET; c->cmsg_type = SCM_RIGHTS; c->cmsg_len = CMSG_LEN(sizeof(int));
    copy(CMSG_DATA(c), &descriptor, sizeof descriptor);
    ready(POLLOUT);
    long n = call6(__NR_sendmsg, channel, (long)&message, MSG_NOSIGNAL, 0, 0, 0);
    if (n <= 0 || n > (long)sizeof frame) fail();
    send_all(frame + n, sizeof frame - (size_t)n);
}
static void enter(void) {
    /* A reentrant loader callback cannot be represented by a complete serial
       observation and is a refusal, never silently dropped or deadlocked. */
    if (__atomic_test_and_set(&busy, __ATOMIC_ACQUIRE)) fail();
    if ((uint64_t)call6(__NR_getpid, 0, 0, 0, 0, 0, 0) != owner_pid || now() >= deadline_ns) fail();
}
static void leave(void) { __atomic_clear(&busy, __ATOMIC_RELEASE); }

static void read_environment(void) {
    long fd = call6(__NR_openat, AT_FDCWD, (long)"/proc/self/environ", O_RDONLY | O_CLOEXEC, 0, 0, 0);
    if (fd < 0) fail();
    size_t total = 0;
    while (total < MAX_ENV - 1) {
        long n = call6(__NR_read, fd, (long)(environment + total), MAX_ENV - 1 - total, 0, 0, 0);
        if (n == -4) continue;
        if (n < 0) fail();
        if (n == 0) break;
        total += (size_t)n;
    }
    if (total == MAX_ENV - 1 || call6(__NR_close, fd, 0, 0, 0, 0, 0) != 0) fail();
    environment[total] = 0;
}
static void initialize(void) {
    const char *selected = get("TEMPLATE_LOADER_TOKEN");
    if (length(selected, 65) != 64) fail();
    for (size_t i = 0; i < 64; ++i)
        if (!((selected[i] >= '0' && selected[i] <= '9') || (selected[i] >= 'a' && selected[i] <= 'f'))) fail();
    copy(token, selected, 64);
    deadline_ns = number(get("TEMPLATE_LOADER_DEADLINE_NS"));
    owner_pid = (uint64_t)call6(__NR_getpid, 0, 0, 0, 0, 0, 0);
    const char *path = get("TEMPLATE_LOADER_SOCKET");
    size_t n = length(path, sizeof(((struct sockaddr_un *)0)->sun_path));
    if (!n || path[0] != '/') fail();
    struct sockaddr_un address;
    zero(&address, sizeof address); address.sun_family = AF_UNIX;
    copy(address.sun_path, path, n);
    channel = (int)call6(__NR_socket, AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, 0, 0, 0);
    if (channel < 0 || call6(__NR_connect, channel, (long)&address,
                            offsetof(struct sockaddr_un, sun_path) + n + 1, 0, 0, 0) != 0) fail();
    enter(); header(HELLO, 0, 0, 0, 0, 0, -1); acknowledge(); leave();
}
unsigned int la_version(unsigned int version) {
    if (version < LAV_CURRENT || LAV_CURRENT != 2) fail();
    read_environment();
    /* Descendant execs inherit env DATA, never this direct-child capability.
       Refuse activation there rather than connect to the original parent peer.
       Returning zero is the documented glibc la_version disable operation. */
    if ((uint64_t)call6(__NR_getppid, 0, 0, 0, 0, 0, 0) != number(get("TEMPLATE_LOADER_OWNER_PID")))
        return 0;
    initialize(); return LAV_CURRENT;
}
unsigned int la_objopen(struct link_map *map, Lmid_t namespace_id, uintptr_t *cookie) {
    enter();
    if (++objects > MAX_OBJECTS || namespace_id != LM_ID_BASE) fail();
    uint64_t id = objects; *cookie = (uintptr_t)id; ++active;
    const char *path = map->l_name;
    if (!path || !*path) path = "/proc/self/exe";
    size_t path_size = length(path, MAX_PATH);
    long fd = call6(__NR_openat, AT_FDCWD, (long)path, O_RDONLY | O_CLOEXEC, 0, 0, 0);
    /* Linux vDSO has no physical body; its mapped bytes are observed below,
       with the missing independent kernel-body origin explicit at readback. */
    Elf64_Ehdr eh;
    if (fd >= 0) {
        long n = call6(__NR_pread64, fd, (long)&eh, sizeof eh, 0, 0, 0);
        if (n != (long)sizeof eh) fail();
    } else {
        if (!map->l_addr || !equal(path, "linux-vdso.so.", 14)) fail();
        copy(&eh, (const void *)(uintptr_t)map->l_addr, sizeof eh);
    }
    if (!equal((const char *)eh.e_ident, "\177ELF", 4) || eh.e_ident[EI_CLASS] != ELFCLASS64 ||
        eh.e_ident[EI_DATA] != ELFDATA2LSB || eh.e_phentsize != sizeof(Elf64_Phdr) ||
        !eh.e_phnum || eh.e_phnum > MAX_SEGMENTS || eh.e_phoff > 4 * 1024 * 1024) fail();
    Elf64_Phdr ph[MAX_SEGMENTS];
    size_t ph_size = (size_t)eh.e_phnum * sizeof(Elf64_Phdr);
    if (fd >= 0) {
        long n = call6(__NR_pread64, fd, (long)ph, ph_size, eh.e_phoff, 0, 0);
        if (n != (long)ph_size) fail();
    } else copy(ph, (const void *)(uintptr_t)(map->l_addr + eh.e_phoff), ph_size);
    size_t count = 0; uint64_t image = 0, memory = 0;
    for (unsigned i = 0; i < eh.e_phnum; ++i) if (ph[i].p_type == PT_LOAD) {
        if (++count > MAX_SEGMENTS || ph[i].p_memsz > MAX_IMAGE || ph[i].p_filesz > ph[i].p_memsz ||
            ph[i].p_vaddr > UINT64_MAX - ph[i].p_memsz || ph[i].p_offset > UINT64_MAX - ph[i].p_filesz ||
            (uint64_t)map->l_addr > UINT64_MAX - ph[i].p_vaddr ||
            ((ph[i].p_flags & PF_X) && (!(ph[i].p_flags & PF_R) || (ph[i].p_flags & PF_W) || ph[i].p_filesz != ph[i].p_memsz))) fail();
        image += ph[i].p_memsz;
        if (ph[i].p_flags & PF_X) memory += ph[i].p_filesz;
        if (image > MAX_IMAGE || memory > MAX_MEMORY) fail();
    }
    if (!count || !memory) fail();
    header(OPEN, id, (uint64_t)map->l_addr, (uint64_t)namespace_id, path_size, count, (int)fd);
    send_all(path, path_size);
    for (unsigned i = 0; i < eh.e_phnum; ++i) if (ph[i].p_type == PT_LOAD) {
        uint64_t bytes = (ph[i].p_flags & PF_X) ? ph[i].p_filesz : 0;
        uint64_t values[6] = { (uint64_t)map->l_addr + ph[i].p_vaddr, ph[i].p_memsz,
                               ph[i].p_offset, ph[i].p_filesz, ph[i].p_flags, bytes };
        unsigned char row[48];
        for (unsigned j = 0; j < 6; ++j) word(row + j * 8, values[j]);
        send_all(row, sizeof row);
        if (bytes) send_all((const void *)(uintptr_t)values[0], (size_t)bytes);
    }
    acknowledge();
    if (fd >= 0 && call6(__NR_close, fd, 0, 0, 0, 0, 0) != 0) fail();
    leave(); return 0; /* No symbol binding callbacks, no redirection. */
}
void la_activity(uintptr_t *cookie, unsigned int flag) {
    enter(); header(ACTIVITY, cookie ? *cookie : 0, flag, 0, 0, 0, -1); acknowledge(); leave();
}
void la_preinit(uintptr_t *cookie) {
    enter(); header(PREINIT, cookie ? *cookie : 0, 0, 0, 0, 0, -1); acknowledge(); leave();
}
unsigned int la_objclose(uintptr_t *cookie) {
    enter();
    if (!cookie || !*cookie || !active) fail();
    header(CLOSE, *cookie, 0, 0, 0, 0, -1); acknowledge(); --active;
    if (!active) { header(DONE, 0, 0, 0, 0, 0, -1); acknowledge(); }
    leave(); return 0;
}
