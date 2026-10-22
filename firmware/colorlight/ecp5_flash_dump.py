# glasgow script ecp5_flash_dump.py jtag-probe -V 3.3 -f 2000 -- OUT.bin [SIZE]
#
# Read an ECP5's configuration SPI flash through JTAG (LSC_PROG_SPI pass-through),
# using the jtag-probe gateware's bulk shifts. Same entry/exit sequence as
# openFPGALoader's Lattice driver: enable config, erase SRAM, disable, PROG_SPI.
# Ends with LSC_REFRESH so the FPGA reboots from flash.
import time
from glasgow.support.bits import bits

ISC_ENABLE, ISC_ERASE, ISC_DISABLE, LSC_PROG_SPI, LSC_REFRESH = 0xC6, 0x0E, 0x26, 0x3A, 0x79
CHUNK = 64 * 1024

out_path = args.script_args[0]
size = int(args.script_args[1], 0) if len(args.script_args) > 1 else 4 * 1024 * 1024
j = jtag_iface

REV = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

def spi_bits(data):                     # SPI is MSB-first; JTAG shifts LSB-first
    return bits(bytes(REV[b] for b in data))

def spi_bytes(b):
    return bytes(REV[x] for x in bytes(b))

async def ir(op):
    await j.write_ir(bits(op, 8), elide=False)

async def spi(tx, nrx):
    await j.enter_shift_dr()
    await j.shift_tdi(spi_bits(tx), last=(nrx == 0))
    rx = await j.shift_tdo(nrx * 8, last=True) if nrx else bits()
    await j.enter_update_dr()
    return spi_bytes(rx)

await j.test_reset()
idcode = int.from_bytes(bytes(await j.read_dr(32)), "little")
print(f"IDCODE 0x{idcode:08x}")
assert idcode == 0x41111043, "not an LFE5U-25F"

await ir(ISC_ENABLE); await j.write_dr(bits(0, 8)); await j.run_test_idle_ms(10)
await ir(ISC_ERASE);  await j.write_dr(bits(1, 8)); await j.run_test_idle_ms(100)
await ir(ISC_DISABLE); await j.run_test_idle_ms(10)
await ir(LSC_PROG_SPI); await j.write_dr(bits(bytes([0xFE, 0x68]))); await j.run_test_idle_ms(1)

jedec = await spi(b"\x9f", 3)
print(f"JEDEC {jedec.hex()}")
assert jedec == bytes.fromhex("c84016"), "unexpected flash ID"

t0 = time.time()
with open(out_path, "wb") as f:
    for addr in range(0, size, CHUNK):
        n = min(CHUNK, size - addr)
        f.write(await spi(bytes([0x03]) + addr.to_bytes(3, "big"), n))
        done = addr + n
        dt = time.time() - t0
        print(f"\r{done >> 10:5d} / {size >> 10} KiB  {done / dt / 1024:6.1f} KiB/s", end="", flush=True)
print()

await ir(ISC_DISABLE); await j.run_test_idle_ms(10)
await ir(LSC_REFRESH); await j.run_test_idle_ms(100)
await j.test_reset()
print("refresh sent; FPGA should reboot from flash")
