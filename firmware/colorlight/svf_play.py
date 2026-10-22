# glasgow script svf_play.py jtag-probe -V 3.3 -f 2000 -- FILE.svf
#
# Minimal SVF player for the subset ecppack emits (SIR/SDR with TDI/TDO/MASK,
# ENDIR/ENDDR, STATE, RUNTEST, zero HDR/HIR/TDR/TIR), on the jtag-probe
# interface. Glasgow's own jtag-svf applet misreads this ECP5's IDCODE; this
# one honours the Pause-DR end state between bitstream chunks and checks every
# expected TDO, so a bad load stops instead of passing silently.
import math, re, time
from glasgow.support.bits import bits

path = args.script_args[0]
j = jtag_iface
end_ir, end_dr = "IDLE", "IDLE"

def hexval(tokens, key):
    if key not in tokens:
        return None
    i = tokens.index(key)
    return int("".join(tokens[i + 1:]).split(")")[0].lstrip("(") or "0", 16)

async def end_in(state, kind):
    if state == "IDLE":
        await (j.enter_update_ir() if kind == "IR" else j.enter_update_dr())
        await j.enter_run_test_idle()
    elif state in ("IRPAUSE", "DRPAUSE"):
        await (j.enter_pause_ir() if kind == "IR" else j.enter_pause_dr())
    else:
        raise ValueError(f"unsupported end state {state}")

async def scan(kind, tokens, n):
    tdi = hexval(tokens, "TDI") or 0
    tdo = hexval(tokens, "TDO")
    mask = hexval(tokens, "MASK")
    await (j.enter_shift_ir() if kind == "IR" else j.enter_shift_dr())
    if tdo is None:
        await j.shift_tdi(bits(tdi, n), last=True)
    else:
        # On the bench card, TDO reads corrupt (1s drop to 0) while TDI is driven low:
        # a TDI-TDO short or coupling. Reads of capture-only registers (IDCODE,
        # status) ignore TDI, so shift ones there.
        if tdi == 0:
            tdi = (1 << n) - 1
        got = int.from_bytes(bytes(await j.shift_tdio(bits(tdi, n), last=True)), "little")
        mask = (1 << n) - 1 if mask is None else mask
        if got & mask != tdo & mask:
            raise RuntimeError(f"S{kind} {n}: TDO 0x{got:x} & 0x{mask:x} != 0x{tdo & mask:x}")
    await end_in(end_ir if kind == "IR" else end_dr, kind)

text = re.sub(r"!.*", "", open(path).read())
commands = [c.split() for c in text.replace("(", " ( ").replace(")", " ) ").split(";")]
commands = [c for c in commands if c]
t0 = time.time(); bits_sent = 0

await j.test_reset()
for n, tokens in enumerate(commands):
    op = tokens[0].upper()
    if op in ("HDR", "HIR", "TDR", "TIR"):
        assert tokens[1] == "0", f"{op} {tokens[1]} unsupported"
    elif op == "ENDIR":
        end_ir = tokens[1]
    elif op == "ENDDR":
        end_dr = tokens[1]
    elif op == "STATE":
        assert tokens[-1] == "IDLE", tokens
        await j.enter_run_test_idle()
    elif op in ("SIR", "SDR"):
        length = int(tokens[1])
        await scan(op[1:], tokens, length)
        bits_sent += length
    elif op == "RUNTEST":
        rest = tokens[1:]
        if rest and rest[0] in ("IDLE",):
            rest = rest[1:]
        await j.enter_run_test_idle()
        if "TCK" in rest:
            await j.run_test_idle(int(rest[rest.index("TCK") - 1]))
        if "SEC" in rest:
            await j.delay_ms(max(1, math.ceil(float(rest[rest.index("SEC") - 1]) * 1000)))
    else:
        raise ValueError(f"unsupported SVF command {op}")
    if n % 100 == 0:
        print(f"\r{n}/{len(commands)} commands, {bits_sent >> 13} KiB", end="", flush=True)

await j.flush()
await j.test_reset()
print(f"\ndone: {len(commands)} commands, {bits_sent >> 13} KiB in {time.time() - t0:.1f} s")
