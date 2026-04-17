# micro:bit MicroPython — LoRa P2P transmitter
# Flash this file to the micro:bit using:
#   uv run uflash microbit_node.py
#
# Wiring (IoT LoRa Node edge connector):
#   micro:bit pin0 (TX) -> RAK811 RX
#   micro:bit pin1 (RX) -> RAK811 TX
#   3.3V / GND via edge connector

from microbit import display, Image, button_a, button_b, sleep
import uart as serial

BADGE_ID = "BADGE_01"
TX_INTERVAL_MS = 5000  # send every 5 seconds

# P2P config must match Raspberry Pi side:
# 868.0 MHz, SF7, BW125, CR4/5, preamble 8, TX power 20
LORA_CONFIG = "at+set_config=lorap2p:868000000:7:0:1:8:20"


def send_at(cmd, wait_ms=500):
    serial.write(cmd + "\r\n")
    sleep(wait_ms)
    resp = b""
    while serial.any():
        resp += serial.read(1)
    return resp.decode("utf-8", "ignore").strip()


def init_rak811():
    display.show(Image.CLOCK12)

    send_at("at+set_config=device:restart", wait_ms=2000)
    send_at("at+set_config=lora:work_mode:1")   # P2P mode
    send_at(LORA_CONFIG)

    # TX mode
    send_at("at+set_config=lorap2p:transfer_mode:2", wait_ms=300)

    display.show(Image.YES)
    sleep(500)
    display.clear()


def send_payload(payload: str):
    hex_data = payload.encode().hex()
    resp = send_at("at+send=lorap2p:" + hex_data)
    return resp


def main():
    serial.init(baudrate=115200, tx=pin0, rx=pin1)
    sleep(500)

    init_rak811()

    counter = 0
    while True:
        # Button A: send immediately
        # Button B: change badge ID (placeholder)
        if button_a.was_pressed():
            msg = "{}:{}:BTN".format(BADGE_ID, counter)
            resp = send_payload(msg)
            display.show(Image.ARROW_N)
            sleep(200)
            display.clear()

        # Periodic heartbeat
        msg = "{}:{}:HB".format(BADGE_ID, counter)
        send_payload(msg)
        counter += 1

        display.show(str(counter % 10))
        sleep(TX_INTERVAL_MS)


main()
