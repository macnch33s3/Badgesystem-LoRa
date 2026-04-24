# micro:bit MicroPython — LoRaWAN ABP transmitter
# Flash this file to the micro:bit using:
#   uv run uflash microbit_node.py
#
# Wiring (IoT LoRa Node edge connector):
#   micro:bit pin0 (TX) -> RAK811 RX
#   micro:bit pin1 (RX) -> RAK811 TX
#   3.3V / GND via edge connector
#
# ABP credentials: TTN Console -> your device -> Activation -> ABP

from microbit import display, Image, button_a, sleep
import uart as serial

BADGE_ID = "BADGE_01"
TX_INTERVAL_MS = 30000  # TTN fair use: ~1 packet/30s

# From TTN console (ABP activation)
DEV_ADDR = "260BAAFD"
NWK_S_KEY = "AD2995B461E158F506027728E79A77DE"
APP_S_KEY = "81E4AAA8D77D370EDE614C5801AFA2BD"


def send_at(cmd, wait_ms=500):
    serial.write(cmd + "\r\n")
    sleep(wait_ms)
    resp = b""
    while serial.any():
        resp += serial.read(1)
    return resp.decode("utf-8", "ignore").strip()


def init_lorawan_abp():
    display.show(Image.CLOCK12)

    send_at("at+set_config=device:restart", wait_ms=2000)

    # LoRaWAN mode
    send_at("at+set_config=lora:work_mode:0")

    # Region
    send_at("at+set_config=lora:region:EU868")

    # ABP credentials
    send_at("at+set_config=lora:dev_addr:" + DEV_ADDR)
    send_at("at+set_config=lora:nwks_key:" + NWK_S_KEY)
    send_at("at+set_config=lora:apps_key:" + APP_S_KEY)

    # ABP does not require join — confirm mode off, ADR off
    send_at("at+set_config=lora:join_mode:1")   # 1 = ABP
    send_at("at+set_config=lora:confirm:0")      # unconfirmed uplinks
    send_at("at+set_config=lora:adr:0")          # fixed data rate

    # Frame counter reset (needed after reflash in ABP)
    send_at("at+set_config=lora:countUp:0")
    send_at("at+set_config=lora:countDown:0")

    display.show(Image.YES)
    sleep(500)
    display.clear()


def send_payload(payload: str):
    hex_data = payload.encode().hex()
    # port 1, unconfirmed uplink
    return send_at("at+send=lora:1:" + hex_data, wait_ms=3000)


def main():
    serial.init(baudrate=115200, tx=pin0, rx=pin1)
    sleep(500)

    init_lorawan_abp()

    counter = 0
    while True:
        if button_a.was_pressed():
            msg = "{}:{}:BTN".format(BADGE_ID, counter)
            send_payload(msg)
            display.show(Image.ARROW_N)
            sleep(300)
            display.clear()

        msg = "{}:{}:HB".format(BADGE_ID, counter)
        send_payload(msg)
        display.show(Image.ARROW_N)
        sleep(300)
        display.clear()

        counter += 1
        sleep(TX_INTERVAL_MS)


main()
