from heaterSwitchGPIO import heaterSwitch

import datetime
import json
import logging
import os
import threading 
import time

class heaterControl():
    def __init__(self, period = 60.0, save_file=None):
        self.lock = threading.Condition()
        self.thread = None

        self.period = period
        self.level = 0.0
        self.cur_start_time = None

        self.cur_day = datetime.date.today()
        self.cur_runtime = 0.0
        self.past_runtimes = {}
        self.to_delete = False
        self.switch = heaterSwitch()

        self.save_file = save_file
        self.loadHistory()

        self.thread = threading.Thread(target=self.heaterThread)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.lock.acquire()
        self.to_delete = True
        while self.thread and self.thread.is_alive():
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

    def getCurRunTime(self):
        return self.cur_runtime

    def getPastRunTimes(self, days=None, skip=None, start_day=None):
        if skip == None:
            skip = 0
        self.lock.acquire()
        if start_day == None:
            start_day = self.cur_day
        start_day -= datetime.timedelta(skip)

        if days == None:
            days = (start_day - min(self.past_runtimes)).days + 1
        if days <= 0:
            return []

        result = [self.past_runtimes.get(start_day -
                    datetime.timedelta(days-1-i), 0.0) for i in range(days)]
        self.lock.release()
        return result

    def serializeHistory(self):
        result = []
        for k in sorted(self.past_runtimes):
            result.append(k.year, k.month, k.day, self.past_runtimes[k])
        return result

    def stashRunTime(self, cur_time = None):
        if cur_time == None:
            cur_time = time.time()

        self.lock.acquire()
        if self.cur_start_time != None and cur_time > self.cur_start_time:
            self.cur_start_time += self.cur_run_start_time - cur_time
            self.cur_run_start_time = cur_time
        self.past_runtimes[self.cur_day] = self.cur_runtime
        self.cur_runtime = 0.0
        self.lock.release()

    def heaterThread(self):
        self.lock.acquire()
        start_time = time.time()
        while not self.to_delete:
            cur_time = time.time()
            new_day = datetime.date.fromtimestamp(cur_time)
            if new_day != self.cur_day:
                self.stashRunTime(cur_time)
                self.cur_day = new_day
                self.saveHistory()

            period_pos = (cur_time - start_time) % self.period
            period_threshold = self.period * self.level

            if period_pos < period_threshold:
                if self.cur_start_time == None:
                    self.cur_start_time = cur_time
                self.switch.setState(1)

                cur_time = time.time()
                period_pos = (cur_time - start_time) % self.period
                if period_pos < period_threshold:
                    self.lock.wait(period_threshold - period_pos)
            else:
                self.switch.setState(0)

                cur_time = time.time()
                if self.cur_start_time != None:
                    self.cur_runtime += cur_time - self.cur_start_time
                    self.cur_start_time = None

                period_pos = (cur_time - start_time) % self.period
                if period_pos > period_threshold:
                    self.lock.wait(self.period - period_pos)
        self.lock.notify()
        self.lock.release()

    def getState(self):
        return self.switch.getState()

    def lookupState(self):
        return self.switch.setState()

    def saveHistory(self, filename=None):
        if filename == None:
            filename = self.save_file
        if not filename:
            return False

        success = True
        directory = os.path.dirname(filename)
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except Exception as err:
                logging.error("Could not create directory %s: %s" % (directory, err))

        self.lock.acquire()
        cur_runtime = self.cur_runtime
        cur_time = time.time()
        if self.cur_start_time != None and cur_time > self.cur_start_time:
            cur_runtime = cur_runtime + (cur_time - self.cur_start_time)

        data = {"cur_day" : (self.cur_day.year, self.cur_day.month, self.cur_day.day),
                "cur_runtime" : cur_runtime,
                "history" : self.serializeHistory()}
        try:
            fp = open(filename, "w")
            json.dump(data, fp)
            fp.close()
        except Exception as err:
            logging.error("Could not write file %s: %s" % (filename, err))
            success = False
        self.lock.release()
        return success

    def loadHistory(self, filename=None):
        if filename == None:
            filename = self.save_file
        if not filename or not os.path.exists(filename):
            return

        self.lock.acquire()
        try:
            fp = open(filename, "r")
            input_data = json.load(fp)
            fp.close()

            new_day = None
            new_runtime = None
            new_history = {}

            (y, m, d) = input_data["cur_day"]
            new_day = datetime.date(y, m, d)
            new_runtime = input_data["cur_runtime"]
            for (y, m, d, t) in input_data["history"]:
                self.past_runtimes[datetime.date(y,m,d)] = t

            self.cur_day = new_day
            self.cur_runtime = new_runtime
            self.past_runtimes = new_history
        except Exception as err:
            logging.error("Could not load schedule from %s: %s" % (filename, err))
        self.lock.release()

