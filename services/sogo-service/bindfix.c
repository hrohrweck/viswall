/*
 * bindfix.c - LD_PRELOAD shim for gnustep-base 1.28.0 sin_family bug.
 *
 * On Debian bookworm, gnustep-base 1.28.0 passes a sockaddr_in to bind()
 * with an uninitialized sin_family field (garbage value), causing
 * EAFNOSUPPORT.  The port and address are correct.  This shim detects
 * the corruption (non-zero port + INADDR_ANY + invalid family) and
 * restores sin_family = AF_INET before delegating to the real bind().
 */
#define _GNU_SOURCE
#include <sys/socket.h>
#include <netinet/in.h>
#include <dlfcn.h>
#include <string.h>

int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen)
{
    static int (*real_bind)(int, const struct sockaddr *, socklen_t) = NULL;
    if (!real_bind)
        real_bind = dlsym(RTLD_NEXT, "bind");

    if (addr && addrlen >= (socklen_t)sizeof(struct sockaddr_in)) {
        const struct sockaddr_in *sin = (const struct sockaddr_in *)addr;
        if (sin->sin_port != 0 &&
            sin->sin_addr.s_addr == 0 &&
            sin->sin_family != AF_INET)
        {
            struct sockaddr_in fixed;
            memcpy(&fixed, sin, sizeof(fixed));
            fixed.sin_family = AF_INET;
            return real_bind(sockfd, (const struct sockaddr *)&fixed,
                             sizeof(fixed));
        }
    }

    return real_bind(sockfd, addr, addrlen);
}
