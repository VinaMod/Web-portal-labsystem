#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

int main() {
    // Set real and effective UID/GID to root (0)
    // This is required for some shells to not drop privileges
    setuid(0);
    setgid(0);

    printf("======================================\n");
    printf("   IoT System Health Check (v1.2)     \n");
    printf("======================================\n");
    printf("Checking system status...\n\n");

    // VULNERABILITY: Relative path call to 'ip' and 'uptime'
    // Attacker can hijack PATH to run their own 'ip' or 'uptime' binary
    printf("Network Configuration:\n");
    system("ip addr show eth0 | grep 'inet '");
    
    printf("\nSystem Uptime:\n");
    system("uptime");

    printf("\nStatus: ALL SYSTEMS NOMINAL\n");
    return 0;
}
