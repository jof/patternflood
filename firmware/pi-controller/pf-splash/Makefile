# pf-splash: ARMv6 (Pi Zero W) by default; `make pf-splash-arm64` for the Pi 5,
# `make host` for an x86-64 copy for testing.
CROSS ?= arm-linux-gnueabihf-
CROSS64 ?= aarch64-linux-gnu-
CFLAGS = -Os -Wall -Wextra -ffreestanding -fno-builtin -fno-stack-protector -fno-pic \
         -fomit-frame-pointer -fno-asynchronous-unwind-tables
LDFLAGS = -nostdlib -static -no-pie -Wl,--gc-sections -Wl,--build-id=none -s

pf-splash: pf-splash.c
	$(CROSS)gcc $(CFLAGS) -marm -march=armv6kz+fp -mfloat-abi=hard $(LDFLAGS) -o $@ $<
	@$(CROSS)readelf -A $@ | grep -q "Tag_CPU_arch: v6" || { echo "not an ARMv6 binary"; exit 1; }

pf-splash-arm64: pf-splash.c
	$(CROSS64)gcc $(CFLAGS) -mgeneral-regs-only $(LDFLAGS) -o $@ $<
	@$(CROSS64)readelf -h $@ | grep -q "AArch64" || { echo "not an AArch64 binary"; exit 1; }

host: pf-splash-host
pf-splash-host: pf-splash.c
	gcc $(CFLAGS) $(LDFLAGS) -o $@ $<

clean:
	rm -f pf-splash pf-splash-arm64 pf-splash-host

.PHONY: host clean
