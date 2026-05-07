// TTN ABP credentials -> fill out with your registered enddevice stuff from ttn
const DEV_ADDR  = "260B1B4F"
const NWK_S_KEY = "54C9328D5498A00E309E10A3ABC7EFFC"
const APP_S_KEY = "648865406677CB0C88FC8769C11B9F68"

// RAK811 hat: TX=P14, RX=P15, reset=P16
serial.redirect(SerialPin.P14, SerialPin.P15, BaudRate.BaudRate115200)

function sendAT(cmd: string): void {
    serial.writeString(cmd + "\r\n")
    basic.pause(100)
    serial.readUntil(serial.delimiters(Delimiters.NewLine))
}

// Hardware reset
basic.showIcon(IconNames.SmallDiamond)
pins.digitalWritePin(DigitalPin.P16, 1)
basic.pause(500)
pins.digitalWritePin(DigitalPin.P16, 0)

basic.pause(2000)
serial.readString()
basic.pause(200)

// LoRaWAN configuration
sendAT("at+set_config=lora:region:EU868")
sendAT("at+set_config=lora:join_mode:1")
sendAT("at+set_config=lora:class:0")
sendAT("at+set_config=lora:dev_addr:" + DEV_ADDR)
sendAT("at+set_config=lora:nwks_key:" + NWK_S_KEY)
sendAT("at+set_config=lora:apps_key:" + APP_S_KEY)
sendAT("at+set_config=lora:dr:5")
sendAT("at+join")
basic.pause(1000)

basic.showString("ABP OK")
//---------------------------------------This stuff down here for our nfc reader---------------------------------------
// PN532 NFC reader over I2C (address 0x24)
// Change PN532_ADDR if your chip uses a different address (e.g. 0x48 for some boards)
const PN532_ADDR = 0x24

function byteToHex(b: number): string {
    let h = b.toString(16).toUpperCase()
    return h.length < 2 ? "0" + h : h
}

// Build a PN532 normal information frame and write it over I2C
function pn532Send(cmd: number[]): void {
    let len = cmd.length + 1        // TFI byte (0xD4) + command bytes
    let lcs = (~len + 1) & 0xFF
    let dcs = 0xD4
    for (let i = 0; i < cmd.length; i++) dcs += cmd[i]
    dcs = (~dcs + 1) & 0xFF

    // Frame layout: 0x00 0x00 0xFF LEN LCS 0xD4 <cmd bytes> DCS 0x00
    let frameLen = 7 + cmd.length + 1
    let buf = pins.createBuffer(frameLen)
    buf.setNumber(NumberFormat.UInt8LE, 0, 0x00)  // preamble
    buf.setNumber(NumberFormat.UInt8LE, 1, 0x00)  // start code
    buf.setNumber(NumberFormat.UInt8LE, 2, 0xFF)  // start code
    buf.setNumber(NumberFormat.UInt8LE, 3, len)
    buf.setNumber(NumberFormat.UInt8LE, 4, lcs)
    buf.setNumber(NumberFormat.UInt8LE, 5, 0xD4)  // TFI: host→PN532
    for (let i = 0; i < cmd.length; i++) {
        buf.setNumber(NumberFormat.UInt8LE, 6 + i, cmd[i])
    }
    buf.setNumber(NumberFormat.UInt8LE, 6 + cmd.length, dcs)
    buf.setNumber(NumberFormat.UInt8LE, 7 + cmd.length, 0x00)  // postamble
    pins.i2cWriteBuffer(PN532_ADDR, buf)
}

// SAMConfiguration — must be called once before card detection
function pn532Init(): void {
    // Normal mode, timeout irrelevant for polling, no IRQ
    pn532Send([0x14, 0x01, 0x14, 0x00])
    basic.pause(100)
    pins.i2cReadBuffer(PN532_ADDR, 10)  // discard response
}

// Poll for one ISO14443A card (Mifare Classic / Ultralight / NTAG)
// Returns the UID as an uppercase hex string, or "" if no card present
function pn532ReadUID(): string {
    // InListPassiveTarget: 1 target max, 106 kbps Type A
    pn532Send([0x4A, 0x01, 0x00])
    basic.pause(200)

    // Response layout (I2C, byte offsets from start of read):
    //  [0]      status   0x01 = ready
    //  [1..3]   0x00 0x00 0xFF  (preamble + start)
    //  [4]      LEN
    //  [5]      LCS
    //  [6]      0xD5  (TFI: PN532→host)
    //  [7]      0x4B  (InListPassiveTarget response code)
    //  [8]      NbTg  number of targets found (0 or 1)
    //  [9]      Tg    target number (0x01)
    //  [10..11] ATQA
    //  [12]     SAK
    //  [13]     NIDLen  UID byte count (4 for Classic, 7 for Ultralight/NTAG)
    //  [14..]   UID bytes
    let resp = pins.i2cReadBuffer(PN532_ADDR, 22)

    if (resp.getNumber(NumberFormat.UInt8LE, 0) != 0x01) return ""  // not ready
    if (resp.getNumber(NumberFormat.UInt8LE, 8) == 0) return ""     // no card

    let uidLen = resp.getNumber(NumberFormat.UInt8LE, 13)
    if (uidLen == 0 || uidLen > 7) return ""

    let uid = ""
    for (let i = 0; i < uidLen; i++) {
        uid += byteToHex(resp.getNumber(NumberFormat.UInt8LE, 14 + i))
    }
    return uid
}

// Init NFC reader
pn532Init()
basic.showString("NFC OK")

// Uplink loop
// Sends an uplink only when a badge is scanned.
// Payload = raw UID bytes (4 or 7 bytes depending on card type).
// On TTN, use a custom payload formatter — see bottom of this file.
let lastUid = ""
let lastSendTime = 0

basic.forever(function () {
    let uid = pn532ReadUID()

    if (uid.length > 0 && uid != lastUid && (input.runningTime() - lastSendTime) > 30000) {
        // New card detected and at least 30 s since last uplink
        lastUid = uid
        lastSendTime = input.runningTime()

        // Send raw UID as payload on port 1
        serial.writeString("at+send=lora:1:" + uid + "\r\n")
        basic.pause(3500)   // wait past RX1 (1 s) and RX2 (2 s) windows
        serial.readString() // drain any downlink bytes

        basic.showIcon(IconNames.Target)
        basic.pause(1000)
        basic.clearScreen()
    } else if (uid.length == 0) {
        // No card in range — clear last UID so the same card can scan again
        lastUid = ""
        basic.pause(300)    // poll every 300 ms when idle
    } else {
        basic.pause(300)
    }
})

// TTN payload formatter (JavaScript — paste into TTN Console)
// Application → Payload formatters → Uplink → Custom Javascript formatter
//
// function decodeUplink(input) {
//     var uid = "";
//     for (var i = 0; i < input.bytes.length; i++) {
//         uid += ("0" + input.bytes[i].toString(16).toUpperCase()).slice(-2);
//     }
//     return { data: { badge_uid: uid } };
// }
