from display import displayControl
from heaterControl import heaterControl
from schedule import schedule
from simple_pid import PID
from tempSensorDHT import tempSensor
from tracker import thermostatStatTracker

import json
import logging
import os
import threading
import time

class Thermostat:
    def __init__(self, pref_file = None, schedule_file = None,
                 runhistory_file = None, trackerdata_file = None,
                 update_frequency = 60.0):
        self.lock = threading.Condition()
        self.thread = None
        self.next_check_time = time.time()
        self.period = update_frequency

        self.enabled = 0
        self.pid = PID(1.0, 0.0, 0.0, setpoint=70, output_limits=(0.0, 1.0))
        self.schedule = schedule(save_file=schedule_file)

        self.tracker = thermostatStatTracker(trackerdata_file,
                                             autosave_frequency = 10*60,
                                             age_limit = 7*24*60*60)

        self.pref_file = pref_file
        self.loadPrefs()

        self.sensor = tempSensor()
        self.control = heaterControl(save_file=runhistory_file)
        self.display = displayControl(self)

        self.to_delete = False
        self.thread = threading.Thread(target=self.thermostatThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True

        # Abuses evaluation order to join right before the is_alive check
        while (self.thread and not self.thread.join(0) and
               self.thread.is_alive()):
            self.lock.notify()
            self.lock.wait()
        self.lock.release()

    def getTargetTemp(self):
        return self.pid.setpoint

    def setTargetTemp(self, val):
        if self.pid.setpoint == val:
            return
        logging.info("Updating new target temp from %f to %f"
                      % (self.pid.setpoint, val))
        self.pid.setpoint = val

    def increaseTemp(self, amount=1.0):
        self.pid.setpoint += amount
        self.updateState()

    def decreaseTemp(self, amount=1.0):
        self.pid.setpoint -= amount
        self.updateState()

    def getStatus(self):
        return self.control.getLevel()

    def getPastRuntimes(self, days=None, skip=None, start_day=None):
        return self.control.getPastRuntimes(days, skip, start_day)

    def saveRunHistory(self):
        return self.control.saveHistory()

    def getSensorHistory(self, time_range, start_time = None, skip = None, stride=None, bin_count=None):
        return self.tracker.getData(time_range, start_time, skip, stride, bin_count)

    def saveSensorHistory(self):
        return self.tracker.save()

    def getEnabled(self):
        return self.enabled

    def setEnabled(self, val):
        val = min(max(int(val),0),2)
        self.enabled = val

    def getTunings(self):
        return self.pid.tunings

    def setTunings(self, Kp, Ki, Kd):
        self.pid.tunings = (Kp, Ki, Kd)

    def readSensor(self):
        return self.sensor.read()

    def thermostatThread(self):
        self.lock.acquire()
        while not self.to_delete:
            logging.info("Checking thermostat...")
            cur_time = time.time()
            while cur_time > self.next_check_time:
                self.next_check_time += self.period

            scheduled_temp = self.schedule.checkForUpdate()
            if scheduled_temp != None:
                self.setTargetTemp(scheduled_temp)

            (temp, humidity) = self.sensor.read()
            status = 0
            if (self.enabled == 2):
                status = 1
            elif (self.enabled == 1):
                status = self.pid(temp)
            self.control.setLevel(status)

            self.tracker.record(cur_time, temp, humidity, status)

            self.display.updateDisplay(temp, self.pid.setpoint, status,
                                       self.control.getCurRuntime())

            if scheduled_temp:
                self.savePrefs()

            cur_time = time.time()
            if cur_time < self.next_check_time:
                self.lock.wait(self.next_check_time - cur_time)
        self.lock.notify()
        self.lock.release()

    def updateState(self):
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()
        self.savePrefs()

    def savePrefs(self, filename=None):
        if filename == None:
            filename = self.pref_file
        if filename == None:
            return False

        success = True
        logging.debug("Writing prefs to %s" % filename)
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except Exception as err:
                logging.error("Could not create directory %s: %s"
                               % (directory, err))

        prefs_dict = {"temp" : self.pid.setpoint,
                      "state" : self.enabled,
                      "pid" : self.pid.tunings}
        try:
            fp = open(filename, "w")
            json.dump(prefs_dict, fp)
            fp.close()
        except Exception as err:
            logging.error("Could not create file %s: %s" % (filename, err))
            success = False

        return success

    def loadPrefs(self, filename=None):
        if filename == None:
            filename = self.pref_file

        new_temp = None
        if filename:
            if os.path.exists(filename):
                prefs_dict = {}
                try:
                    fp = open(filename, "r")
                    prefs_dict = json.load(fp)
                    fp.close()
                except Exception as err:
                    logging.error("Could note load prefs from %s: %s"
                                   % (filename, err))

                if not isinstance(prefs_dict, dict):
                    logging.error(
                        "Prefences loaded from %s invalid, discarding"
                                   % filename)
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
                logging.warning(
                    "Prefs file %s does not exist, attempting to create..."
                                 % filename)
                if self.savePrefs(filename):
                    logging.warning("Creating %s successful" % filename)
                else:
                    logging.error("Creating pref file %s failed !!"
                                   % filename)

        if new_temp == None:
            new_temp = self.schedule.mostRecentTemp()
        if new_temp != None:
            self.pid.setpoint = new_temp

