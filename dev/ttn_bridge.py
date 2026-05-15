"""
TTN MQTT bridge: reads temperature uplinks from the sender node and
schedules a downlink to the display node so it can show the value.

Fill in the four constants below, then run:  python3 dev/ttn_bridge.py
"""

import json
import struct
import base64
from datetime import datetime
import paho.mqtt.client as mqtt

# Configure app ID and dev
TTN_APP_ID      = "microbit-node"               # application ID from TTN Console (not the display name)
TTN_API_KEY     = "NNSXS.C6C5H3NUTURSGK5JUOSA6WDWKYRSRS3AG25X7YA.IB73CYYGEIVWE76UGZ4D2RTUOEO4LYKDCH73IF5UXCTDIJTYUGRQ"
SENDER_DEV_ID   = "eui-70b3d57ed0077401"
DISPLAY_DEV_ID  = "euid-70b3d57ed00775f5"
TTN_HOST        = "eu1.cloud.thethings.network"
TTN_PORT        = 8883


#Uplink and downlink topic
UPLINK_TOPIC   = f"v3/{TTN_APP_ID}@ttn/devices/{SENDER_DEV_ID}/up"
DOWNLINK_TOPIC = f"v3/{TTN_APP_ID}@ttn/devices/{DISPLAY_DEV_ID}/down/push"

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def decode_cayenne_temp(payload_bytes: bytes) -> float | None:
    """Parse Cayenne LPP: 01 67 <Int16BE temp*10> → degrees Celsius."""
    if len(payload_bytes) >= 4 and payload_bytes[0] == 0x01 and payload_bytes[1] == 0x67:
        raw = struct.unpack(">h", payload_bytes[2:4])[0]   # signed Int16BE
        return raw / 10.0
    return None


def on_connect(client, userdata, flags, rc, props=None):
    if rc == 0:
        print(f"[{ts()}] Connected to TTN MQTT — subscribing to {UPLINK_TOPIC}")
        client.subscribe(UPLINK_TOPIC)
    else:
        print(f"[{ts()}] Connection failed, rc={rc}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
        b64  = data["uplink_message"]["frm_payload"]
        raw  = base64.b64decode(b64)
    except (KeyError, ValueError) as e:
        print(f"[{ts()}] Could not parse uplink: {e}")
        return

    temp = decode_cayenne_temp(raw)
    if temp is None:
        print(f"[{ts()}] Uplink received but not a Cayenne temp payload: {raw.hex()}")
        return

    print(f"[{ts()}] Temperature from sender: {temp:.1f} °C — scheduling downlink")

    # Encode as 2-byte signed Int16BE (temp * 10) for the display node
    tenths   = round(temp * 10)
    payload  = struct.pack(">h", tenths)
    downlink = {
        "downlinks": [{
            "f_port": 1,
            "frm_payload": base64.b64encode(payload).decode(),
            "priority": "NORMAL"
        }]
    }
    client.publish(DOWNLINK_TOPIC, json.dumps(downlink))
    print(f"[{ts()}] Downlink queued: {payload.hex()} → display node")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(f"{TTN_APP_ID}@ttn", TTN_API_KEY)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[{ts()}] Connecting to {TTN_HOST}:{TTN_PORT} ...")
    client.connect(TTN_HOST, TTN_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()
