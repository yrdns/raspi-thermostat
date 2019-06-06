# Using gpiozero for simplicity's sake
from gpiozero import LED

import logging

class heaterSwitch():
    def __init__(self, pin=21):
        self.gpio_dev = LED(pin)
        logging.info("Connected heater to pin %s" % pin)

    def setState(self, val):
        if (val):
            logging.info("Turning heater on (pin %s)" % self.gpio_dev.pin)
            self.gpio_dev.on()
        else:
            logging.info("Turning heater off (pin %s)" % self.gpio_dev.pin)
            self.gpio_dev.off()

    def getState(self):
        return self.gpio_dev.value

    def lookupState():
        return self.gpio_dev.value

