/* pf-splash: move the Colorlight card's boot splash on to the next step.
 *
 *   pf-splash [-i IFACE] [-t SECONDS] [--show] [--restore] STEP
 *
 * The card's BIOS draws a spinner and a progress bar until the renderer takes the
 * display (receiver75/bios/splash.c). STEP goes into ctrl_scratch, which the bar
 * reads. --show also points the display back at the splash bank and enables it,
 * for when the renderer has stopped.
 *
 * The CSR writes are the 8-byte UDP packets r75_frame.poke() sends, but built by
 * hand and sent as raw Ethernet frames to the card's MAC. They need no IP
 * address, route or ARP, only a wired interface with link, so this runs the same
 * from the initramfs as from early systemd, before NetworkManager is up.
 *
 * Interfaces are found and watched with ioctls only, not /sys: the initramfs
 * copy runs in the background and outlives the switch to the real root, where
 * its /sys is gone. A wired interface that's down is brought up to get link;
 * --restore puts it back down afterwards (the initramfs uses it, so the real
 * root's udev can still rename it and NetworkManager finds it as it was).
 *
 * Freestanding (raw syscalls, no libc): Ubuntu's armhf libc is built for ARMv7,
 * and the Zero W is ARMv6. It also builds for AArch64 (the Pi 5) and for x86-64,
 * for testing on a PC.
 *
 * Exit status: 0 sent, 1 no wired link before the timeout, 2 bad arguments.
 */

#if defined(__arm__)
enum { SYS_write = 4, SYS_close = 6, SYS_ioctl = 54, SYS_nanosleep = 162,
       SYS_exit_group = 248, SYS_socket = 281, SYS_sendto = 290 };

static long sys6(long n, long a, long b, long c, long d, long e, long f)
{
    register long r7 __asm__("r7") = n;
    register long r0 __asm__("r0") = a;
    register long r1 __asm__("r1") = b;
    register long r2 __asm__("r2") = c;
    register long r3 __asm__("r3") = d;
    register long r4 __asm__("r4") = e;
    register long r5 __asm__("r5") = f;
    __asm__ volatile("svc #0" : "+r"(r0)
                     : "r"(r7), "r"(r1), "r"(r2), "r"(r3), "r"(r4), "r"(r5) : "memory");
    return r0;
}

__asm__(".text\n.global _start\n_start:\n"
        "  mov r0, sp\n"
        "  bl cstart\n");
#elif defined(__aarch64__)
enum { SYS_write = 64, SYS_close = 57, SYS_ioctl = 29, SYS_nanosleep = 101,
       SYS_exit_group = 94, SYS_socket = 198, SYS_sendto = 206 };

static long sys6(long n, long a, long b, long c, long d, long e, long f)
{
    register long x8 __asm__("x8") = n;
    register long x0 __asm__("x0") = a;
    register long x1 __asm__("x1") = b;
    register long x2 __asm__("x2") = c;
    register long x3 __asm__("x3") = d;
    register long x4 __asm__("x4") = e;
    register long x5 __asm__("x5") = f;
    __asm__ volatile("svc #0" : "+r"(x0)
                     : "r"(x8), "r"(x1), "r"(x2), "r"(x3), "r"(x4), "r"(x5) : "memory");
    return x0;
}

__asm__(".text\n.global _start\n_start:\n"
        "  mov x0, sp\n"
        "  bl cstart\n");
#elif defined(__x86_64__)
enum { SYS_write = 1, SYS_close = 3, SYS_ioctl = 16, SYS_nanosleep = 35,
       SYS_exit_group = 231, SYS_socket = 41, SYS_sendto = 44 };

static long sys6(long n, long a, long b, long c, long d, long e, long f)
{
    register long r10 __asm__("r10") = d;
    register long r8 __asm__("r8") = e;
    register long r9 __asm__("r9") = f;
    long ret;
    __asm__ volatile("syscall" : "=a"(ret)
                     : "a"(n), "D"(a), "S"(b), "d"(c), "r"(r10), "r"(r8), "r"(r9)
                     : "rcx", "r11", "memory");
    return ret;
}

__asm__(".text\n.global _start\n_start:\n"
        "  xor %rbp, %rbp\n"
        "  mov %rsp, %rdi\n"
        "  and $-16, %rsp\n"
        "  call cstart\n"
        "  hlt\n");
#else
#error "pf-splash: add this architecture's syscall numbers"
#endif

#define sys3(n, a, b, c) sys6(n, (long)(a), (long)(b), (long)(c), 0, 0, 0)

/* The compiler may emit calls to these for struct copies and zeroing. */
void *memset(void *d, int c, unsigned long n)
{
    unsigned char *p = d;
    while (n--)
        *p++ = (unsigned char)c;
    return d;
}

void *memcpy(void *d, const void *s, unsigned long n)
{
    unsigned char *p = d;
    const unsigned char *q = s;
    while (n--)
        *p++ = *q++;
    return d;
}

/* --- receiver75 -------------------------------------------------------------- */

static const unsigned char CARD_MAC[6] = { 0x10, 0xe2, 0xd5, 0x00, 0x00, 0x00 };
static const unsigned char HOST_IP[4] = { 192, 168, 75, 1 };
static const unsigned char CARD_IP[4] = { 192, 168, 75, 39 };
#define CSR_PORT 4344

/* As in r75_frame.py and receiver75's csr.csv. */
#define CSR_CTRL_SCRATCH 0x82000804u
#define CSR_ENABLE       0x82002014u
#define CSR_BASE_ADDR    0x8200201cu
#define SPLASH_BANK_WORDS (2u * 16u * 64u * 48u)   /* bank 2: after the renderer's two */

/* --- Linux ABI bits -------------------------------------------------------- */

#define AF_INET 2
#define AF_PACKET 17
#define SOCK_DGRAM 2
#define SOCK_RAW 3
#define ETH_P_IP 0x0800
#define ARPHRD_ETHER 1
#define SIOCGIFNAME 0x8910
#define SIOCGIFFLAGS 0x8913
#define SIOCSIFFLAGS 0x8914
#define SIOCGIFHWADDR 0x8927
#define SIOCGIFINDEX 0x8933
#define SIOCETHTOOL 0x8946
#define SIOCGIWNAME 0x8b01
#define ETHTOOL_GDRVINFO 3
#define IFF_UP 0x1
#define IFF_LOOPBACK 0x8
#define IFF_RUNNING 0x40
#define IFNAMSIZ 16
#define MAX_IFINDEX 64

struct ifreq {
    char name[IFNAMSIZ];
    union {
        struct { unsigned short family; unsigned char data[14]; } hwaddr;
        short flags;
        int ifindex;
        void *data;
        char pad[24];
        long align;
    } u;
};

struct ethtool_drvinfo {
    unsigned cmd;
    char driver[32], version[32], fw_version[32], bus_info[32], erom_version[32];
    char reserved2[12];
    unsigned n_priv_flags, n_stats, testinfo_len, eedump_len, regdump_len;
};

struct sockaddr_ll {
    unsigned short family;
    unsigned short protocol;
    int ifindex;
    unsigned short hatype;
    unsigned char pkttype;
    unsigned char halen;
    unsigned char addr[8];
};

struct timespec { long sec, nsec; };

/* --- small helpers ------------------------------------------------------------ */

static unsigned slen(const char *s)
{
    unsigned n = 0;
    while (s[n])
        n++;
    return n;
}

static int seq(const char *a, const char *b)
{
    while (*a && *a == *b)
        a++, b++;
    return *a == *b;
}

static void say(const char *a, const char *b, const char *c)
{
    sys3(SYS_write, 2, "pf-splash: ", 11);
    sys3(SYS_write, 2, a, slen(a));
    if (b)
        sys3(SYS_write, 2, b, slen(b));
    if (c)
        sys3(SYS_write, 2, c, slen(c));
    sys3(SYS_write, 2, "\n", 1);
}

static void sleep_ms(long ms)
{
    struct timespec t = { 0, ms * 1000000L };
    sys3(SYS_nanosleep, &t, 0, 0);
}

static long ctl;        /* AF_INET socket for the interface ioctls */

static int if_req(unsigned long req, const char *name, struct ifreq *ifr)
{
    memset(ifr, 0, sizeof *ifr);
    memcpy(ifr->name, name, slen(name) + 1);
    return sys3(SYS_ioctl, ctl, req, ifr) >= 0;
}

static int if_flags(const char *name)
{
    struct ifreq ifr;
    return if_req(SIOCGIFFLAGS, name, &ifr) ? (unsigned short)ifr.u.flags : -1;
}

/* An Ethernet interface on a real bus (so not veth, bridges or the like) that
   isn't wireless. */
static int is_wired(const char *name)
{
    struct ifreq ifr;
    int flags = if_flags(name);
    if (flags < 0 || (flags & IFF_LOOPBACK))
        return 0;
    if (!if_req(SIOCGIFHWADDR, name, &ifr) || ifr.u.hwaddr.family != ARPHRD_ETHER)
        return 0;
    if (if_req(SIOCGIWNAME, name, &ifr))
        return 0;
    struct ethtool_drvinfo info;
    memset(&info, 0, sizeof info);
    info.cmd = ETHTOOL_GDRVINFO;
    memset(&ifr, 0, sizeof ifr);
    memcpy(ifr.name, name, slen(name) + 1);
    ifr.u.data = &info;
    return sys3(SYS_ioctl, ctl, SIOCETHTOOL, &ifr) >= 0 && info.bus_info[0];
}

/* Interfaces this run brought up, to put back down at the end. */
static char raised[4][IFNAMSIZ];
static int n_raised;

static void raise_if(const char *name)
{
    struct ifreq ifr;
    if (!if_req(SIOCGIFFLAGS, name, &ifr) || (ifr.u.flags & IFF_UP))
        return;
    ifr.u.flags |= IFF_UP;
    if (sys3(SYS_ioctl, ctl, SIOCSIFFLAGS, &ifr) < 0)
        return;
    for (int i = 0; i < n_raised; i++)
        if (seq(raised[i], name))
            return;
    if (n_raised < 4)
        memcpy(raised[n_raised++], name, slen(name) + 1);
}

static void lower_raised(void)
{
    struct ifreq ifr;
    for (int i = 0; i < n_raised; i++) {
        if (!if_req(SIOCGIFFLAGS, raised[i], &ifr))
            continue;
        ifr.u.flags &= ~IFF_UP;
        sys3(SYS_ioctl, ctl, SIOCSIFFLAGS, &ifr);
    }
}

/* One pass: bring up any wired interface that's down; return 1 with its name
   in `out` once one has link. With a fixed name, only that one. */
static int poll_links(const char *fixed, char *out)
{
    struct ifreq ifr;
    for (int idx = 1; idx <= MAX_IFINDEX; idx++) {
        if (fixed) {
            if (idx > 1)
                break;
            memcpy(ifr.name, fixed, slen(fixed) + 1);
        } else {
            memset(&ifr, 0, sizeof ifr);
            ifr.u.ifindex = idx;
            if (sys3(SYS_ioctl, ctl, SIOCGIFNAME, &ifr) < 0 || !is_wired(ifr.name))
                continue;
        }
        int flags = if_flags(ifr.name);
        if (flags < 0)
            continue;
        if (!(flags & IFF_UP)) {
            raise_if(ifr.name);
        } else if (flags & IFF_RUNNING) {
            memcpy(out, ifr.name, slen(ifr.name) + 1);
            return 1;
        }
    }
    return 0;
}

static unsigned short csum(const unsigned char *p, int n)
{
    unsigned long s = 0;
    for (int i = 0; i < n; i += 2)
        s += (p[i] << 8) | p[i + 1];
    while (s >> 16)
        s = (s & 0xffff) + (s >> 16);
    return (unsigned short)~s;
}

static void put16(unsigned char *p, unsigned v) { p[0] = v >> 8; p[1] = v; }
static void put32le(unsigned char *p, unsigned v)
{
    p[0] = v; p[1] = v >> 8; p[2] = v >> 16; p[3] = v >> 24;
}

/* One CSR write: Ethernet + IPv4 + UDP + (word address, value), padded to 60 bytes. */
static void build_frame(unsigned char f[60], const unsigned char *src_mac, unsigned csr,
                        unsigned value, unsigned id)
{
    memset(f, 0, 60);
    memcpy(f, CARD_MAC, 6);
    memcpy(f + 6, src_mac, 6);
    put16(f + 12, ETH_P_IP);
    unsigned char *ip = f + 14;
    ip[0] = 0x45;
    put16(ip + 2, 20 + 8 + 8);
    put16(ip + 4, id);
    put16(ip + 6, 0x4000);          /* don't fragment */
    ip[8] = 64;
    ip[9] = 17;                     /* UDP */
    memcpy(ip + 12, HOST_IP, 4);
    memcpy(ip + 16, CARD_IP, 4);
    put16(ip + 10, csum(ip, 20));
    unsigned char *udp = ip + 20;
    put16(udp, CSR_PORT);
    put16(udp + 2, CSR_PORT);
    put16(udp + 4, 8 + 8);          /* checksum 0: none, allowed over IPv4 */
    put32le(udp + 8, csr >> 2);
    put32le(udp + 12, value);
}

/* The writes are idempotent; each goes out three times in case the first
   frames after link-up are dropped. */
static int send_writes(const char *ifname, int step, int show)
{
    struct ifreq ifr;
    if (!if_req(SIOCGIFHWADDR, ifname, &ifr))
        return 0;
    unsigned char src_mac[6];
    memcpy(src_mac, ifr.u.hwaddr.data, 6);
    if (!if_req(SIOCGIFINDEX, ifname, &ifr))
        return 0;
    struct sockaddr_ll to;
    memset(&to, 0, sizeof to);
    to.family = AF_PACKET;
    to.protocol = (ETH_P_IP >> 8) | ((ETH_P_IP & 0xff) << 8);
    to.ifindex = ifr.u.ifindex;
    to.halen = 6;
    memcpy(to.addr, CARD_MAC, 6);

    long s = sys3(SYS_socket, AF_PACKET, SOCK_RAW, 0);
    if (s < 0) {
        say("can't open a raw socket (needs CAP_NET_RAW)", 0, 0);
        return 0;
    }
    struct { unsigned csr, value; } w[3] = {
        { CSR_CTRL_SCRATCH, (unsigned)step },
        { CSR_BASE_ADDR, SPLASH_BANK_WORDS },
        { CSR_ENABLE, 1 },
    };
    int nw = show ? 3 : 1, sent = 0;
    unsigned char f[60];
    for (int rep = 0; rep < 3; rep++) {
        if (rep)
            sleep_ms(200);
        for (int k = 0; k < nw; k++) {
            build_frame(f, src_mac, w[k].csr, w[k].value, (unsigned)(rep * 4 + k));
            if (sys6(SYS_sendto, s, (long)f, sizeof f, 0, (long)&to, sizeof to) == sizeof f)
                sent++;
        }
    }
    sys3(SYS_close, s, 0, 0);
    return sent;
}

static int usage(void)
{
    say("usage: pf-splash [-i IFACE] [-t SECONDS] [--show] [--restore] STEP", 0, 0);
    return 2;
}

static int run(int argc, char **argv)
{
    const char *fixed = 0;
    int timeout_s = 10, show = 0, restore = 0, step = -1;
    for (int i = 1; i < argc; i++) {
        char *a = argv[i];
        if (seq(a, "-i") && i + 1 < argc) {
            fixed = argv[++i];
            if (!fixed[0] || slen(fixed) >= IFNAMSIZ)
                return usage();
        } else if (seq(a, "-t") && i + 1 < argc) {
            timeout_s = 0;
            for (char *p = argv[++i]; *p; p++) {
                if (*p < '0' || *p > '9' || timeout_s > 3600)
                    return usage();
                timeout_s = timeout_s * 10 + (*p - '0');
            }
        } else if (seq(a, "--show")) {
            show = 1;
        } else if (seq(a, "--restore")) {
            restore = 1;
        } else if (a[0] >= '0' && a[0] <= '9' && a[1] == 0 && step < 0) {
            step = a[0] - '0';
        } else {
            return usage();
        }
    }
    if (step < 0)
        return usage();

    ctl = sys3(SYS_socket, AF_INET, SOCK_DGRAM, 0);
    char ifname[IFNAMSIZ];
    int linked = 0;
    for (int tick = 0; tick <= timeout_s * 10 && !linked; tick++) {
        if (tick)
            sleep_ms(100);
        linked = poll_links(fixed, ifname);
    }
    int sent = linked ? send_writes(ifname, step, show) : 0;
    if (restore)
        lower_raised();
    if (!linked) {
        say("no wired link", fixed ? " on " : 0, fixed);
        return 1;
    }
    char msg[] = "step ? sent on ";
    msg[5] = (char)('0' + step);
    say(sent ? msg : "send failed on ", ifname, show ? " (splash shown)" : 0);
    return sent ? 0 : 1;
}

__attribute__((used, noreturn)) void cstart(long *sp)
{
    long r = run((int)sp[0], (char **)(sp + 1));
    for (;;)
        sys3(SYS_exit_group, r, 0, 0);
}
