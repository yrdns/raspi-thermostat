from RPi_I2C_driver.RPi_I2C_driver import lcd

from gpiozero import Button

import logging
import threading
import time

custom_chars = [# Degree symbol
                [0b00110, 0b01001, 0b01001, 0b00110,
                 0b00000, 0b00000, 0b00000, 0b00000],
               ]

class displayControl():
    def __init__(self, thermostat, up_pin=None, down_pin=None,
                 update_frequency = 1.0):
        self.lock = threading.Condition()
        self.thread = None
        self.period = update_frequency

        self.thermostat = thermostat

        self.display = lcd()
        self.display.lcd_load_custom_chars(
            [# Degree symbol
                [0b00110, 0b01001, 0b01001, 0b00110,
                 0b00000, 0b00000, 0b00000, 0b00000],
            ])

        self.up_pin = None
        self.down_pin = None
        if up_pin != None:
            self.up_pin = Button(up_pin)
            self.up_ping.when_pressed = self.increaseTemp
        if down_pin != None:
            self.down_pin = Button(down_pin)
            self.down_pin.when_pressed = self.decreaseTemp

        self.to_delete = False
        self.thread = threading.Thread(target=self.displayThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        while (self.thread and not self.thread.join(0) and
               self.thread.is_alive()):
            self.lock.notify()
            self.lock.wait()
        self.lock.release()

    def increaseTemp(self):
        self.thermostat.setTargetTemp(self.thermostat.getTargetTemp() + 1)

        self.thermostat.updateState()

    def decreaseTemp(self):
        self.thermostat.setTargetTemp(self.thermostat.setTargetTemp() - 1)
        self.thermosat.updateState()

    def displayThread(self):
        self.lock.acquire()
        try:
            while not self.to_delete:
                self.updateDisplay()
                self.lock.wait(self.period - (time.time() % self.period))
            self.lock.notify()
            self.lock.release()
        finally:
            # What happens if we catch excpetion but hold the lock?
            self.display.lcd_clear()

    def updateDisplay(self):
        (temp, humidity) = self.thermostat.readSensor()
        runtime = int(self.thermostat.getTodaysRuntime() + .5)

        l1 = "     Temp:%7.2f"    % temp
        l2 = "   Target:%7.2f"    % self.thermostat.getTargetTemp()
        l3 = " On Value:%7.2f %%" % (100 * self.thermostat.getStatus())
        l4 = "  Runtime:%3d:%02d:%02d" % (runtime // 3600,
                                          (runtime % 3600)//60,
                                          runtime % 60)

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
        self.display.lcd_display_string(l4, 4)

