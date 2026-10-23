# pf-splash: ARMv6 (Pi Zero W) by default; `make host` builds an x86-64 copy for testing.
CROSS ?= arm-linux-gnueabihf-
CFLAGS = -Os -Wall -Wextra -ffreestanding -fno-builtin -fno-stack-protector -fno-pic \
         -fomit-frame-pointer -fno-asynchronous-unwind-tables
LDFLAGS = -nostdlib -static -no-pie -Wl,--gc-sections -Wl,--build-id=none -s

pf-splash: pf-splash.c
	$(CROSS)gcc $(CFLAGS) -marm -march=armv6kz+fp -mfloat-abi=hard $(LDFLAGS) -o $@ $<
	@$(CROSS)readelf -A $@ | grep -q "Tag_CPU_arch: v6" || { echo "not an ARMv6 binary"; exit 1; }

host: pf-splash-host
pf-splash-host: pf-splash.c
	gcc $(CFLAGS) $(LDFLAGS) -o $@ $<

clean:
	rm -f pf-splash pf-splash-host

.PHONY: host clean
