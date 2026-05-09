# Badgesystem-LoRa — Session Handoff

## Project

IoT badge system (OST university) using micro:bit + RAK811 LoRaWAN hat and TTN (The Things Network). Nodes send sensor data over LoRaWAN; a display node receives temperature via downlink and shows it on the micro:bit LED matrix.

## Architecture

```
Sender micro:bit  ──LoRaWAN uplink──▶  TTN  ◀──MQTT──  ttn_bridge.py (laptop)
                                        │                     │
                                        │       MQTT downlink │
                                        ▼                     │
                                Display micro:bit  ◀──────────┘
                                (shows temp on LED)
```

- **Sender** (`microbit_node/main.ts`): sends temperature as Cayenne LPP every ~30 s
- **Display** (`microbit_node/main_display.ts`): sends dummy uplinks to open Class A RX windows, parses downlink, shows temp on LED
- **Bridge** (`dev/ttn_bridge.py`): subscribes to sender uplinks via TTN MQTT, decodes Cayenne LPP temp, pushes 2-byte Int16BE downlink to display device

## TTN Details

| Field | Value |
|---|---|
| Application ID | `microbit-node` |
| Server | `eu1.cloud.thethings.network` |
| Sender device ID | `eui-70b3d57ed0077401` (DEV_ADDR `260B1B4F`) |
| Display device ID | `euid-70b3d57ed00775f5` (DEV_ADDR `260B7183`) |

## Downlink Payload Format

2-byte signed Int16BE where value = temperature × 10  
Example: 26.0 °C → `0x01 0x04` (= 260)

## Current Status (2026-05-09)

- Bridge connects and queues downlinks ✓
- TTN Live Data confirms downlink delivered to display device with payload `01 04` ✓
- Display node sends uplinks ✓
- **Temperature rendering on LED — not yet confirmed**

Last fix applied to `main_display.ts`:
- Extended RX read wait: 3.5 s → 4 s + second read after 1 s
- Case-insensitive `at+recv=` search (some RAK811 firmware outputs uppercase)

## Next Debug Step

If temperature still doesn't show on LED, add this temporarily after the `serial.readString()` calls to see what the RAK811 actually outputs:

```typescript
basic.showString(resp.substr(0, 8))
```

This will scroll the first 8 chars of the RAK811 response on the LED so you can identify the exact format.

## Run the Bridge

```powershell
pip install paho-mqtt
python dev/ttn_bridge.py
```
