
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
#include <net/if.h>
#include <netinet/ether.h>
#include <linux/if_packet.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <linux/if_tun.h>
#include <pthread.h>
#include <linux/if_ether.h>

/* Connect to a tap interface making it "live" */

#define DAEMON 0

#define DEBUG 0

#if DEBUG > 0
#define dprintf(format,args...) printf("%s(%d) %s: " format,__FILE__,__LINE__, __FUNCTION__, ## args)
#else
#define dprintf(format,args...) /* noop */
#endif

#if DAEMON
int become_daemon(void) {
	pid_t pid;

	/* Fork the process */
	dprintf("become_daemon: forking process...");
	pid = fork();

	/* If pid < 0, error */
	if (pid < 0) {
		perror("become_daemon: fork");
		return 1;
	}

	/* If pid > 0, parent */
	else if (pid > 0) {
		dprintf("become_daemon: parent exiting...");
		_exit(0);
	}

	/* Set the session ID */
	setsid();

	/* Fork again */
	pid = fork();
	if (pid < 0)
		return 1;
	else if (pid != 0) {
		dprintf("become_daemon(2): parent exiting...");
		_exit(0);
	}

	/* Set the umask */
	umask(022);

	/* Close stdin,stdout,stderr */
	close(0);
	close(1);
	close(2);
	return 0;
}
#endif

int getfd(char *name) {
	struct ifreq ifr;
	int fd,err;

	dprintf("name: %s\n", name);

	if( (fd = open("/dev/net/tun", O_RDWR)) < 0 ) {
		perror("Opening /dev/net/tun");
		return fd;
	}
	dprintf("fd: %d\n", fd);

	memset(&ifr, 0, sizeof(ifr));
	ifr.ifr_flags = IFF_TAP | IFF_NO_PI;
	strncpy(ifr.ifr_name, name, IFNAMSIZ);
	if( (err = ioctl(fd, TUNSETIFF, (void *)&ifr)) < 0 ) {
		perror("ioctl(TUNSETIFF)");
		close(fd);
		fd = -1;
	}

	return fd;
}

int main(int argc, char **argv) {
	int i, fd;

	dprintf("argc: %d\n", argc);
	if (argc < 2) {
		printf("usage: %s <tap1> [tap2] [tap3] ...\n", argv[0]);
		return 1;
	}
	for (i = 1; i < argc; i++) {
		fd = getfd(argv[i]);
		if (fd < 0) {
			fprintf(stderr, "Failed to open tap: %s\n", argv[i]);
			return 1;
		}
		dprintf("opened %s on fd %d\n", argv[i], fd);
	}
#if !defined(DEBUG) || DEBUG == 0
#if DAEMON
	become_daemon();
#endif
#endif
	while(1) { sleep(99999); }
	return 0;
}
