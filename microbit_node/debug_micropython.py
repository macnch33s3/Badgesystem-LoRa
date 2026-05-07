"""
Debug script — scrolls each AT command response on the LED display.
Flash this first to verify the RAK811 is talking before running main.
"""
from microbit import *

uart.init(baudrate=115200, tx=pin14, rx=pin15)


def read_line(timeout_ms=3000):
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
    return buf.decode("utf-8", "replace")


def send_at_show(cmd):
    """Send command, scroll the response on the display."""
    uart.write(cmd + "\r\n")
    sleep(200)
    resp = read_line()
    display.scroll(resp if resp else "---", delay=80)
    return resp


# ─── Reset ────────────────────────────────────────────────────────────────────
display.show(Image.DIAMOND_SMALL)
pin16.write_digital(1)
sleep(500)
pin16.write_digital(0)

# Show each boot line so we know the actual count
display.scroll("BOOT:", delay=80)
for i in range(9):          # read up to 9 lines; stops showing "---" when done
    line = read_line(2000)
    if line:
        display.scroll(str(i + 1) + ":" + line, delay=60)
    else:
        display.scroll("END" + str(i + 1), delay=80)
        break
sleep(300)

# ─── Test each AT command ─────────────────────────────────────────────────────
display.scroll("REG", delay=80)
send_at_show("at+set_config=lora:region:EU868")

display.scroll("MODE", delay=80)
send_at_show("at+set_config=lora:join_mode:1")

display.scroll("JOIN", delay=80)
send_at_show("at+join")

display.scroll("TX", delay=80)
send_at_show("at+send=lora:1:01670122")   # hardcoded: temp = 29.0 °C

display.show(Image.YES)
