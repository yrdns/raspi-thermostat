from buttonsKeyboard import buttons

import threading

class buttonsController():
    def __init__(self, thermostat):
        self.lock = threading.Condition()
        self.delta = 0
        self.thermostat = thermostat
        self.buttons = buttons(self.increase, self.decrease)

        self.to_delete = False
        self.thread = threading.Thread(target=self.callbackThread)
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

    def increase(self):
        self.lock.acquire()
        self.delta += 1
        self.lock.notify()
        self.lock.release()

    def decrease(self):
        self.lock.acquire()
        self.delta -= 1
        self.lock.notify()
        self.lock.release()

    def callbackThread(self):
        self.lock.acquire()
        while not self.to_delete:
            self.lock.wait()
            while self.delta:
                new_temp = self.thermostat.getTargetTemp() + self.delta
                self.delta = 0
                self.lock.release()
                self.thermostat.setTargetTemp(new_temp)
                self.thermostat.updateState()
                self.lock.acquire()

        self.lock.notify()
        self.lock.release()

