// TTN ABP credentials
const DEV_ADDR  = "260B7183"
const NWK_S_KEY = "A3CDA7D9F255A278569B2BA3AB9E2858"
const APP_S_KEY = "4EECB8DFCC6EF71A15E3BB7216C9CBB5"

// RAK811 hat: TX=P14, RX=P15, reset=P16
serial.redirect(SerialPin.P14, SerialPin.P15, BaudRate.BaudRate115200)

// Send one AT command
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

// Wait for RAK811 to finish booting, then drain whatever it sent
basic.pause(2000)
serial.readString()
basic.pause(200)

// LoRaWAN configuration sending AT commands
sendAT("at+set_config=lora:region:EU868")
sendAT("at+set_config=lora:join_mode:1")    // 1 = ABP
sendAT("at+set_config=lora:class:0")        // Class A
sendAT("at+set_config=lora:dev_addr:" + DEV_ADDR)
sendAT("at+set_config=lora:nwks_key:" + NWK_S_KEY)
sendAT("at+set_config=lora:apps_key:" + APP_S_KEY)
sendAT("at+set_config=lora:dr:5")           // DR5 = SF7 BW125 for EU868 (good for testing)
sendAT("at+join")
basic.pause(1000)

basic.showString("ABP OK")

// Calibrate compass before sending heading data
input.calibrateCompass()
basic.showString("CAL OK")

// Uplink loop -> actual loop function of the uplink payload
basic.forever(function () {
    // Build Cayenne LPP payload: analog input on channel 1
    // Format: CH(1B) + TYPE(1B) + UInt16BE(heading degrees)
    // Analog input type = 0x02, raw degrees 0–359
    let heading = input.compassHeading()
    let buf = pins.createBuffer(2)
    buf.setNumber(NumberFormat.UInt16BE, 0, heading)
    let payload = "0102" + buf.toHex()

    // Port 1, unconfirmed uplink
    serial.writeString("at+send=lora:1:" + payload + "\r\n")
    // Wait past Class A RX1 (1 s) and RX2 (2 s) windows, then drain any
    // downlink bytes the RAK811 may have written to UART
    basic.pause(3500)
    serial.readString()

    // Visual TX indicator
    basic.showIcon(IconNames.Target)
    basic.pause(1000)
    basic.clearScreen()

    // TTN fair-use policy: ~30 s total (3.5 s drain already counted)
    basic.pause(25500)
})
