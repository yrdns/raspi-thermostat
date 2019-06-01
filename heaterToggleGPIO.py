# Using gpiozero for simplicity's sake
from gpiozero import LED

class heaterToggle():
    def __init__(self, pin=22, period = 60.0)
        self.gpio_dev = LED(pin)

    def setState(self, val):
        if (val):
            self.gpio_dev.on()
        else:
            self.gpio_dev.off()

    def getState(self):
        return self.gpio_dev.value

    def lookupState():
        return self.gpio_dev.value

