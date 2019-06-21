from RPi_I2C_driver.RPi_I2C_driver import lcd

from gpiozero import Button

import logging
import threading
import time

class displayControl():
    def __init__(self, thermostat, up_pin=None, down_pin=None):
        self.display = lcd()
        self.display.lcd_load_custom_chars(
            [ # Degree symbol
             [0x02, 0x05, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00],
              # Alternate colon
             [0x00, 0x00, 0x04, 0x00, 0x00, 0x04, 0x00, 0x00],
            ])

        self.up_pin = None
        self.down_pin = None
        if up_pin != None:
            self.up_pin = Button(up_pin)
            self.up_ping.when_pressed = thermostat.increaseTemp
        if down_pin != None:
            self.down_pin = Button(down_pin)
            self.down_pin.when_pressed = thermostat.decreaseTemp

    def __del__(self):
        self.display.lcd_clear()

    def updateDisplay(self, temp, target, status, runtime):
        status *= 100
        runtime = int(runtime + .5)

        l1 = "     Temp:%7.2f"   % temp
        l2 = "   Target:%7.2f"   % target
        l3 = " On Value:%7.2f%%" % status
        l4 = ("  Runtime:%3d-%02d-%02d" % (runtime // 3600,
                                           (runtime % 3600) // 60,
                                           runtime % 60)).split("-")

        #First Line
        self.display.lcd_display_string(l1, 1)
        self.display.lcd_write_char(0) # Degree sign
        self.display.lcd_write_char(ord("F"))

        # Second Line
        self.display.lcd_display_string(l2, 2)
        self.display.lcd_write_char(0) # Degree sign
        self.display.lcd_write_char(ord("F"))

        # Third Line
        self.display.lcd_display_string(l3, 3)

        # Fourth Line
        self.display.lcd_display_string(l4[0], 4)
        for s in l4[1:]:
            self.display.lcd_write_char(1) # Colon (alternate)
            self.display.lcd_display_string(s, 0)

