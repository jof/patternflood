# glasgow script ecp5_flash_write.py jtag-probe -V 3.3 -f 2000 -- IMAGE.bit [OFFSET]
#
# Write an image to an ECP5's configuration SPI flash through JTAG
# (LSC_PROG_SPI pass-through), then read the whole range back and compare.
# Same entry sequence as ecp5_flash_dump.py. GD25Q32C commands: 06 WREN,
# 05 RDSR1, 35 RDSR2, D8 64 KiB block erase, 02 page program, 03 read.
#
# Every read shifts with TDI held high: on the bench wiring, TDO reads corrupt
# while TDI is low (see README). Stops before erasing if the IDs or the
# write-protect bits are not as expected.
import time
from glasgow.support.bits import bits

ISC_ENABLE, ISC_ERASE, ISC_DISABLE, LSC_PROG_SPI, LSC_REFRESH = 0xC6, 0x0E, 0x26, 0x3A, 0x79
FLASH_SIZE = 4 * 1024 * 1024
BLOCK, PAGE, CHUNK = 64 * 1024, 256, 64 * 1024

image_path = args.script_args[0]
status_only = image_path == "status"     # "-- status": print IDs and status registers, change nothing
offset = int(args.script_args[1], 0) if len(args.script_args) > 1 else 0
image = b"" if status_only else open(image_path, "rb").read()
assert offset % BLOCK == 0 and offset + len(image) <= FLASH_SIZE
j = jtag_iface

REV = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

def spi_bits(data):                     # SPI is MSB-first; JTAG shifts LSB-first
    return bits(bytes(REV[b] for b in data))

def spi_bytes(b):
    return bytes(REV[x] for x in bytes(b))

async def ir(op):
    await j.write_ir(bits(op, 8), elide=False)

async def spi(tx, nrx=0):
    await j.enter_shift_dr()
    await j.shift_tdi(spi_bits(tx), last=(nrx == 0))
    rx = await j.shift_tdo(nrx * 8, last=True) if nrx else bits()   # shift_tdo holds TDI high
    await j.enter_update_dr()
    return spi_bytes(rx)

async def status():
    return (await spi(b"\x05", 1))[0]

async def wait_ready(what, timeout_s):
    t0 = time.time()
    while True:
        sr = await status()
        if not sr & 0x01:
            return sr
        if time.time() - t0 > timeout_s:
            raise RuntimeError(f"{what}: flash still busy after {timeout_s} s (SR1 0x{sr:02x})")

async def write_enable():
    for _ in range(3):
        await spi(b"\x06")
        if await status() & 0x02:
            return
    raise RuntimeError("WREN did not set WEL")

async def read(addr, n):
    out = bytearray()
    for a in range(addr, addr + n, CHUNK):
        m = min(CHUNK, addr + n - a)
        out += await spi(bytes([0x03]) + a.to_bytes(3, "big"), m)
    return bytes(out)

# --- Checks before touching anything ---
await j.test_reset()
idcode = int.from_bytes(bytes(await j.read_dr(32)), "little")
print(f"IDCODE 0x{idcode:08x}")
assert idcode == 0x41111043, "not an LFE5U-25F"

async def enter():
    await ir(ISC_ENABLE); await j.write_dr(bits(0, 8)); await j.run_test_idle_ms(10)
    await ir(ISC_ERASE);  await j.write_dr(bits(1, 8)); await j.run_test_idle_ms(100)
    await ir(ISC_DISABLE); await j.run_test_idle_ms(10)
    await ir(LSC_PROG_SPI); await j.write_dr(bits(bytes([0xFE, 0x68]))); await j.run_test_idle_ms(1)

async def leave():
    await ir(ISC_DISABLE); await j.run_test_idle_ms(10)
    await ir(LSC_REFRESH); await j.run_test_idle_ms(100)
    await j.test_reset()

# The first entry of a session sometimes doesn't take on the bench wiring (flash
# reads all ones), so retry until the flash answers.
for attempt in range(3):
    await enter()
    jedec = await spi(b"\x9f", 3)
    if jedec == bytes.fromhex("c84016"):
        break
    print(f"flash not answering (JEDEC {jedec.hex()}), re-entering")
    await j.test_reset()
sr1, sr2 = await status(), (await spi(b"\x35", 1))[0]
print(f"JEDEC {jedec.hex()}  SR1 0x{sr1:02x}  SR2 0x{sr2:02x}  "
      f"(SRP0 {sr1 >> 7 & 1}, BP4..0 {sr1 >> 2 & 0x1f:05b}, WEL {sr1 >> 1 & 1}, WIP {sr1 & 1}; "
      f"SRP1 {sr2 & 1}, QE {sr2 >> 1 & 1}, LB {sr2 >> 3 & 7:03b}, CMP {sr2 >> 6 & 1})")
if status_only or jedec != bytes.fromhex("c84016") or sr1 & 0x80 or sr2 & 0x41:
    await leave()                       # always exit pass-through mode, so the next session works
    assert jedec == bytes.fromhex("c84016"), "unexpected flash ID"
    assert not (sr1 & 0x80 or sr2 & 0x41), "SRP0/SRP1/CMP set: protection not plain BP bits; refusing"
    raise SystemExit(0)

# Stock firmware leaves BP2..0 = 111 (whole array protected). Clear, write, then restore.
orig_sr = (sr1, sr2)
if sr1 & 0x7C:
    # One-byte WRSR (SR1 only): this GD25Q32C ignored the two-byte 01 xx yy form
    # (WEL stayed set, nothing written). SR2 is already 0.
    await write_enable()
    await spi(bytes([0x01, 0x00]))
    await wait_ready("clear protection", 1)
    sr1 = await status()
    print(f"protection cleared: SR1 0x{sr1:02x}")
    if sr1 & 0x7C:
        await leave()
        raise RuntimeError("block-protect bits did not clear")

end = offset + len(image)
blocks = range(offset, (end + BLOCK - 1) // BLOCK * BLOCK, BLOCK)
print(f"writing {len(image)} bytes at 0x{offset:06x}-0x{end:06x}, erasing {len(blocks)} x 64 KiB")

# --- Erase ---
t0 = time.time()
for b in blocks:
    await write_enable()
    await spi(bytes([0xD8]) + b.to_bytes(3, "big"))
    await wait_ready(f"erase 0x{b:06x}", 5)
print(f"erased in {time.time() - t0:.1f} s")

# --- Program ---
t0 = time.time()
for a in range(offset, end, PAGE):
    page = image[a - offset:a - offset + PAGE]
    if page == b"\xff" * len(page):
        continue                        # erased already
    await write_enable()
    await spi(bytes([0x02]) + a.to_bytes(3, "big") + page)
    await wait_ready(f"program 0x{a:06x}", 1)
    if (a - offset) % (64 * PAGE) == 0:
        print(f"\r  programmed {(a - offset) >> 10:4d} / {len(image) >> 10} KiB", end="", flush=True)
print(f"\nprogrammed in {time.time() - t0:.1f} s")

# --- Verify ---
back = await read(offset, len(image))
bad = [i for i in range(len(image)) if back[i] != image[i]]
if bad:
    print(f"VERIFY FAILED: {len(bad)} bytes differ, first at 0x{offset + bad[0]:06x}")
else:
    print(f"VERIFY OK: {len(image)} bytes match")
    if orig_sr[0] & 0x7C:               # restore the shipped protection
        await write_enable()
        await spi(bytes([0x01, orig_sr[0] & 0x7C]))
        await wait_ready("restore protection", 1)
        print(f"protection restored: SR1 0x{await status():02x}")

await leave()
if bad:
    raise SystemExit(1)
print("refresh sent; power-cycle the card to boot from flash")
