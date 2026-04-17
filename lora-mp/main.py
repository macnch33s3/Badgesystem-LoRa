import serial
import time

SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 115200


def send_at(ser: serial.Serial, cmd: str, timeout: float = 1.0) -> str:
    ser.write((cmd + "\r\n").encode())
    time.sleep(timeout)
    response = ser.read_all().decode(errors="ignore").strip()
    return response


def init_rak811(ser: serial.Serial):
    print("Initializing RAK811...")

    # Reset module
    resp = send_at(ser, "at+set_config=device:restart", timeout=2.0)
    print(f"  restart: {resp}")

    # Set LoRa mode to P2P (point-to-point, no LoRaWAN)
    resp = send_at(ser, "at+set_config=lora:work_mode:1")
    print(f"  work_mode P2P: {resp}")

    # Frequency: 868.0 MHz, SF7, BW125, CR4/5, preamble 8, TX power 20
    resp = send_at(ser, "at+set_config=lorap2p:868000000:7:0:1:8:20")
    print(f"  lorap2p config: {resp}")


def receive_loop(ser: serial.Serial):
    print("Listening for LoRa packets...\n")

    # Put RAK811 into continuous RX mode
    send_at(ser, "at+set_config=lorap2p:transfer_mode:1", timeout=0.5)

    while True:
        if ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(f"RAW: {line}")
                parse_rx(line)
        time.sleep(0.05)


def parse_rx(line: str):
    # RAK811 P2P RX format: at+recv=<rssi>,<snr>,<data_len>:<hex_payload>
    if not line.startswith("at+recv="):
        return

    try:
        params, hex_payload = line[len("at+recv="):].split(":")
        rssi, snr, _ = params.split(",")
        payload = bytes.fromhex(hex_payload).decode(errors="replace")
        print(f"  RSSI={rssi} dBm  SNR={snr} dB")
        print(f"  Payload: {payload}\n")
    except ValueError:
        print(f"  Could not parse: {line}\n")


def main():
    with serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1) as ser:
        init_rak811(ser)
        receive_loop(ser)


if __name__ == "__main__":
    main()
