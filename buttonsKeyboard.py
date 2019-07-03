import keyboard

import logging

class buttons():
    def __init__(self, upbutton_callback=None, downbutton_callback=None,
                 upbutton_key="F12", downbutton_key="F11"):

        self.upkey = None
        if upbutton_key != None and upbutton_callback != None:
            cb = lambda ev : upbutton_callback()
            self.upkey = keyboard.on_press_key(upbutton_key, cb, True)
        self.downkey = None
        if downbutton_key != None and downbutton_callback != None:
            cb = lambda ev : downbutton_callback()
            self.downkey = keyboard.on_press_key(downbutton_key, cb, True)

    def __del__(self):
        if self.upkey != None:
            keyboard.unhook(self.upkey)
        if self.downkey != None:
            keyboard.unhook(self.downkey)

