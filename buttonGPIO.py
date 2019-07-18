from gpiozero import Button

import logging

class buttonGPIO():
    def __init__(self, pin, callback):
        self.button = None
        self.button = Button(pin)
        self.button.when_pressed = callback

    def __del__(self):
        if self.button != None:
            self.button.when_pressed = None

