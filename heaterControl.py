from pyHS100 import SmartPlug, Discover

import threading 
import time

class heaterControl():
    def __init__(self, name="Heater", period = 60.0):
        self.name = name
        self.period = period
        self.level = 0.0
        self.state = 0
        self.to_delete = False

        self.initializeSmartPlug()
        self.lock = threading.Condition()
        self.thread = threading.Thread(target=self.heaterThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        self.lock.notify()
        self.lock.wait()
        self.thead.join()
        self.lock.release()

    def initializeSmartPlug(self):
        self.smart_plug = None
        print ("Searching for valid plug...")
        try:
            for (ip, plug) in Discover.discover().items():
                if self.name == plug.sys_info["alias"]:
                    print ("Found plug", self.name, "at address", ip)
                    self.smart_plug = plug
                    return True
        except Exception as error:
            print ("Failed to initialize due to exception:", error)
        print ("ERROR: Could not find any plug named", self.name)
        return False

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
                self.setState(1)
                period_pos = (time.time() - start_time) % self.period
                if period_pos < period_threshold:
                    self.lock.wait(period_threshold - period_pos)
            else:
                self.setState(0)
                period_pos = (time.time() - start_time) % self.period
                if period_pos > period_threshold:
                    self.lock.wait(self.period - period_pos)
        self.lock.notify()
        self.lock.release()

    def setState(self, val):
        try:
            if val:
                print ("Turning heater on")
                self.smart_plug.turn_on()
            else:
                print ("Turning heater off")
                self.smart_plug.turn_off()
            self.state = val
        except:
            print ("Plug state gave error, attempting to re-discover...")
            if (self.initializeSmartPlug()):
                print ("Successful, retrying state read")
                # Does python support tail recursion?
                return self.setState(val)
            else:
                print ("Failed, ignoring set state command")

    def getState(self):
        return self.state

    def lookupState():
        if self.smart_plug == None:
            return -2
        try:
            cur_state = self.smart_plug.state
            if cur_state == "ON":
                return 1
            if cur_state == "OFF":
                return 0
        except Exception as error:
            print ("Plug state gave error <", error, "> attempting to re-discover...")
            if (self.initializeSmartPlug()):
                print ("Successful, retrying state read")
                return self.lookupState()
            print ("Failed, returning error")
            return -3
        return -1

