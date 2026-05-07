from microbit import *
import struct

# ─── TTN ABP credentials ──────────────────────────────────────────────────────
DEV_ADDR  = "260B1B4F"
NWK_S_KEY = "54C9328D5498A00E309E10A3ABC7EFFC"
APP_S_KEY  = "648865406677CB0C88FC8769C11B9F68"
# ─────────────────────────────────────────────────────────────────────────────

# RAK811 hat: TX=P14, RX=P15, reset=P16
uart.init(baudrate=115200, tx=pin14, rx=pin15)


def read_line(timeout_ms=2000):
    """Read from UART until newline or timeout."""
    buf = b""
    elapsed = 0
    while elapsed < timeout_ms:
        c = uart.read(1)
        if c is None:
            sleep(10)
            elapsed += 10
        elif c == b"\n":
            break
        elif c != b"\r":
            buf += c
    return buf


def drain():
    """Drain all pending UART bytes (handles multi-line responses and downlinks)."""
    sleep(3500)  # wait past RX1 (1s) and RX2 (2s) Class A windows
    while uart.any():
        uart.read(uart.any())
        sleep(50)


def send_at(cmd):
    uart.write(cmd + "\r\n")
    sleep(150)
    read_line()  # consume OK / response line


# ─── Hardware reset ───────────────────────────────────────────────────────────
display.show(Image.DIAMOND_SMALL)
pin16.write_digital(1)
sleep(500)
pin16.write_digital(0)

# Consume 7 boot lines emitted by RAK811 after reset
for _ in range(7):
    read_line()
sleep(200)

# ─── LoRaWAN configuration ────────────────────────────────────────────────────
send_at("at+set_config=lora:region:EU868")
send_at("at+set_config=lora:join_mode:1")    # 1 = ABP
send_at("at+set_config=lora:class:0")        # Class A
send_at("at+set_config=lora:dev_addr:" + DEV_ADDR)
send_at("at+set_config=lora:nwks_key:" + NWK_S_KEY)
send_at("at+set_config=lora:apps_key:" + APP_S_KEY)
send_at("at+set_config=lora:dr:5")           # DR5 = SF7 BW125
send_at("at+join")
sleep(1000)

display.scroll("ABP OK")

# ─── Uplink loop ──────────────────────────────────────────────────────────────
while True:
    # Cayenne LPP: channel 1, type 0x67 (temperature), Int16BE(temp * 10)
    temp = temperature()
    lpp = bytes([0x01, 0x67]) + struct.pack(">h", temp * 10)
    payload = "".join("{:02X}".format(b) for b in lpp)

    uart.write("at+send=lora:1:" + payload + "\r\n")
    drain()  # waits 3.5 s for RX windows + drains any downlink data from UART

    display.show(Image.TARGET)
    sleep(1000)
    display.clear()

    # TTN fair-use: ~30 s total between uplinks (drain already took ~3.5 s)
    sleep(25500)
