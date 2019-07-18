from keyboard import on_press_key, on_release_key

import logging

class buttonHandler():
    def __init__(self, key, callback):
        self.presshandler = None
        self.releasehandler = None

        self.callback = callback
        self.pressed = False
        self.presshandler = on_press_key(key, self.press, True)
        self.releasehandler = on_release_key(key, self.release, True)

    def __del__(self):
        if self.presshandler != None:
            keyboard.unhook(self.presshandler)
        if self.releasehandler != None:
            keyboard.unhook(self.releasehandler)

    def press(self, event):
        if not self.pressed:
            self.pressed = True
            self.callback()

    def relesae(self, event):
        self.pressed = False

