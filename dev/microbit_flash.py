#"Dev Address",
#IoTLoRaNode.initialiseRadio(
#"AppKey",
#"NWSK",
#)
#spreadingFactors.Seven

#from machine import Pin, I2C
#from microbit import *
#
#i2c = I2C(freq=400000)          # create I2C peripheral at frequency of 400kHz
#                                # depending on the port, extra parameters may be required
#                                # to select the peripheral and/or pins to use
#
#i2c.scan()

#i2c_sda = Pin(20)
#i2c_scl = Pin(19)
#
#i2c = I2C(0,sda=i2c_sda,scl=i2c_scl,freq=100000)
#
#print('Scan I2C Bus...')
#devices = i2c.scan()
#
#if len(devices) == 0:
#    print('No I2C dev')
#else:
#    print('I2C found:', len(devices))
#    for device in devices:
#        print('Addr:', device, '| Hex Addr:', hex(device))

# scan i2c bus for responding devices
from microbit import *

start = 0x00
end = 0x7F
while True:
    print("Scanning I2C bus...now..")
    for i in range(start, end + 1):
            try:
                i2c.read(i, 1)
            except OSError:
                pass
            else:
                print("Found:  [%s]" % hex(i))
                display.scroll(hex(i))
    print("Scanning done")
    sleep(1)