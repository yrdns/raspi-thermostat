from gpiozero import Button

import logging

class buttons():
    def __init__(self, upbutton_callback=None, downbutton_callback=None,
                 upbutton_pin=24, downbutton_pin=23):

        self.upbutton = None
        if upbutton_pin != None and upbutton_callback != None:
            self.upbutton = Button(upbutton_pin)
            self.upbutton.when_pressed = upbutton_callback

        self.downbutton = None
        if downbutton_pin != None and downbutton_callback != None:
            self.downbutton = Button(downbutton_pin)
            self.downbutton.when_pressed = downbutton_callback

    def __del__(self):
        if self.upbutton != None:
            self.upbutton.when_pressed = None
        if self.downbutton != None:
            self.downbutton.when_pressed = None

