// TTN ABP credentials — register a NEW device on TTN for this receiver node
const DEV_ADDR  = "260B7183"
const NWK_S_KEY = "A3CDA7D9F255A278569B2BA3AB9E2858"
const APP_S_KEY = "4EECB8DFCC6EF71A15E3BB7216C9CBB5"

// RAK811 hat: TX=P14, RX=P15, reset=P16
serial.redirect(SerialPin.P14, SerialPin.P15, BaudRate.BaudRate115200)

function sendAT(cmd: string): void {
    serial.writeString(cmd + "\r\n")
    basic.pause(300)
    serial.readString()   // drain full response, not just one line
}

// Send AT command and return the response (for checking OK/ERROR)
function sendATRead(cmd: string): string {
    serial.writeString(cmd + "\r\n")
    basic.pause(300)
    return serial.readString()
}

// Convert two hex characters to a byte value
function hexToByte(h: string): number {
    const chars = "0123456789abcdef"
    h = h.toLowerCase()
    return chars.indexOf(h.charAt(0)) * 16 + chars.indexOf(h.charAt(1))
}

// Parse a 4-char hex string as signed Int16BE, return temp in tenths of a degree
function parseTemp(hex: string): number {
    let val = hexToByte(hex.substr(0, 2)) * 256 + hexToByte(hex.substr(2, 2))
    if (val > 32767) val -= 65536
    return val  // already temp * 10
}

// Hardware reset
basic.showIcon(IconNames.SmallDiamond)
pins.digitalWritePin(DigitalPin.P16, 1)
basic.pause(500)
pins.digitalWritePin(DigitalPin.P16, 0)
basic.pause(2000)
serial.readString()
basic.pause(200)

// LoRaWAN ABP configuration
sendAT("at+set_config=lora:region:EU868")
sendAT("at+set_config=lora:join_mode:1")   // 1 = ABP
sendAT("at+set_config=lora:class:0")       // Class A
sendAT("at+set_config=lora:dev_addr:" + DEV_ADDR)
sendAT("at+set_config=lora:nwks_key:" + NWK_S_KEY)
sendAT("at+set_config=lora:apps_key:" + APP_S_KEY)
sendAT("at+set_config=lora:dr:5")          // DR5 = SF7 BW125

let joinResp = sendATRead("at+join")
basic.pause(1000)
if (joinResp.indexOf("OK") >= 0) {
    basic.showString("JOIN OK")
} else {
    // Show J-ERR and the first 6 chars of the response to diagnose
    basic.showString("J-ERR")
    basic.showString(joinResp.substr(0, 6))
}

let lastTempTenths = 0
let hasTemp = false

basic.forever(function () {
    // Send a dummy uplink on port 1 to open Class A RX windows
    serial.writeString("at+send=lora:1:00\r\n")
    basic.showIcon(IconNames.Target)

    // Wait past RX1 (1 s) and RX2 (2 s) windows
    basic.pause(4000)
    let resp = serial.readString()
    basic.pause(1000)
    resp = resp + serial.readString()

    // Case-insensitive search — some RAK811 firmware uses uppercase AT+RECV=
    let respLow = resp.toLowerCase()

    if (respLow.indexOf("ok") >= 0) {
        basic.showIcon(IconNames.Yes)
    } else {
        basic.showString("TX ERR")
    }

    // RAK811 downlink: at+recv=<port>,<rssi>,<snr>,<len>:<hex>
    let idx = respLow.indexOf("at+recv=")
    if (idx >= 0) {
        let after = resp.substr(idx + 8)
        let colon = after.indexOf(":")
        if (colon >= 0) {
            let hex = after.substr(colon + 1).trim().toLowerCase()
            if (hex.length >= 4) {
                lastTempTenths = parseTemp(hex.substr(0, 4))
                hasTemp = true
            }
        }
    }

    if (hasTemp) {
        let whole = lastTempTenths / 10
        let frac  = Math.abs(lastTempTenths % 10)
        basic.showString("" + whole + "." + frac + "C")
    } else {
        basic.showIcon(IconNames.Asleep)
    }

    // TTN fair-use: ~30 s total cycle
    basic.pause(24000)
})