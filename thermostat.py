from heaterControl import heaterControl
from schedule import schedule
from simple_pid import PID
from tempSensorDHT import tempSensor

import json
import os
import threading
import time

class Thermostat:
    def __init__(self, pref_file = None, schedule_file = None):
        self.lock = threading.Condition()
        self.thread = None

        self.enabled = 0
        self.pid = PID(1.0, 0.0, 0.0, setpoint=70, output_limits=(0.0, 1.0))
        self.pref_file = pref_file
        self.schedule = schedule(filename=schedule_file)

        new_temp = None
        if pref_file:
            if os.path.exists(pref_file):
                prefs_dict = {}

                self.pref_file = pref_file
                try:
                    fp = open(pref_file, "r")
                    prefs_dict = json.load(fp)
                    fp.close()
                except Exception as err:
                    print("Could note load prefs from", pref_file, err)

                if not isinstance(prefs_dict, dict):
                    print("Prefences loaded from %s invalid, discarding"
                           % pref_file)
                else:
                    if ("state" in prefs_dict and
                        prefs_dict["state"] in [0, 1, 2]):
                        self.enabled = prefs_dict["state"]

                    if ("temp" in prefs_dict and
                        isinstance(prefs_dict["temp"], (float, int))):
                        new_temp = prefs_dict["temp"]

                    if "pid" in prefs_dict:
                        self.pid.tunings = prefs_dict["pid"]
            else:
                self.writePrefs()
        if new_temp == None:
            new_temp = self.schedule.mostRecentTemp()
        if new_temp != None:
            self.pid.setpoint = new_temp

        self.sensor = tempSensor()
        self.control = heaterControl()
        self.state_changed = False
        self.to_delete = False

        self.thread = threading.Thread(target=self.thermostatThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        while self.thread and self.thread.is_alive():
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
        return self.enabled

    def setEnabled(self, val):
        val = min(max(int(val),0),2)
        self.enabled = val

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

            scheduled_temp = self.schedule.checkForUpdate()
            if scheduled_temp != None:
                self.setTargetTemp(scheduled_temp)

            status = 0
            if (self.enabled == 2):
                status = 1
            elif (self.enabled == 1):
                status = self.pid(self.sensor.getTemp())
            self.control.setLevel(status)

            if scheduled_temp:
                self.writePrefs()

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
        self.writePrefs()

    def writePrefs(self):
        if self.pref_file == None:
            return False

        directory = os.path.dirname(self.pref_file)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except Exception as err:
                print("Could not create directory %s:" % directory, err)

        prefs_dict = {"temp" : self.pid.setpoint,
                      "state" : self.enabled,
                      "pid" : self.pid.tunings}
        try:
            fp = open(self.pref_file, "w")
            json.dump(prefs_dict, fp)
            fp.close()
        except Exception as err:
            print("Could not create file %s:" % self.pref_file, err)
            return False
        return True

