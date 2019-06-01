from heaterToggleSmartSwitch import heaterToggle

import threading 
import time

class heaterControl():
    def __init__(self, period = 60.0):
        self.period = period
        self.level = 0.0
        self.to_delete = False
        self.switch = heaterToggle()

        self.lock = threading.Condition()
        self.thread = threading.Thread(target=self.heaterThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        while self.thread.is_alive():
            self.lock.notify()
            self.lock.wait()
            self.thead.join(0)
        self.lock.release()

    def setLevel(self, val):
        self.lock.acquire()
        self.level = val
        self.lock.notify()
        self.lock.release()

    def getLevel(self):
        return self.level

    def heaterThread(self):
        self.lock.acquire()
        start_time = time.time()
        while not self.to_delete:
            period_pos = (time.time() - start_time) % self.period
            period_threshold = self.period * self.level

            if period_pos < period_threshold:
                self.switch.setState(1)
                period_pos = (time.time() - start_time) % self.period
                if period_pos < period_threshold:
                    self.lock.wait(period_threshold - period_pos)
            else:
                self.swith.setState(0)
                period_pos = (time.time() - start_time) % self.period
                if period_pos > period_threshold:
                    self.lock.wait(self.period - period_pos)
        self.lock.notify()
        self.lock.release()

    def getState(self):
        return self.switch.getState()

    def lookupState():
        return self.switch.setState()

