from tempSensorDHT import tempSensor
from heaterControl import heaterControl
from simple_pid import PID

import threading
import time

class Thermostat:
    def __init__(self):
        self.lock = threading.Condition()
        self.toggle = 1
        self.sensor = tempSensor()
        self.control = heaterControl()
        self.pid = PID(0.5, 0.0, 0.2, setpoint=70, output_limits=(0.0, 1.0))
        self.state_changed = False
        self.to_delete = False

        self.thread = threading.Thread(target=self.thermostatThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        while self.thread.is_alive():
            self.lock.notify()
            self.lock.wait()
            self.thread.join(0)
        self.lock.release()

    def getTargetTemp(self):
        return self.pid.setpoint

    def setTargetTemp(self, val):
        if self.pid.setpoint == val:
            return
        print ("Updating new target temp from", self.pid.setpoint, "to", val)
        self.pid.setpoint = val

    def getStatus(self):
        return self.control.getLevel()

    def getEnabled(self):
        return self.toggle

    def setEnabled(self, val):
        val = min(max(int(val),0),2)
        self.toggle = val

    def getTunings(self):
        return self.pid.tunings

    def setTunings(self, Kp, Ki, Kd):
        self.pid.tunings = (Kp, Ki, Kd)

    def getCurrentTemp(self):
        return self.sensor.getTemp()

    def thermostatThread(self):
        self.lock.acquire()
        next_check_time = time.time()
        while not self.to_delete:
            print ("Checking thermostat...")
            if not self.state_changed:
                self.sensor.updateTemp()
                next_check_time += 60.0
            self.state_changed = False

            status = 0
            if (self.toggle == 2):
                status = 1
            elif (self.toggle == 1):
                status = self.pid(self.sensor.getTemp())
            self.control.setLevel(status)

            cur_time = time.time()
            if cur_time < next_check_time:
                self.lock.wait(next_check_time - cur_time)
        self.lock.notify()
        self.lock.release()

    def updateState(self):
        self.lock.acquire()
        self.state_changed = True
        self.lock.notify()
        self.lock.release()

