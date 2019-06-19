from heapq import heappush, heappop, heappushpop

import csv
import logging
import os
import time
import threading

class thermostatStatTracker:
    def __init__(self, save_file = None, autosave_frequency = None,
                 age_limit = None, entry_limit = None):
        self.lock = threading.RLock()

        self.age_limit = age_limit
        self.entry_limit = entry_limit

        self.save_file = save_file
        self.last_savetime = time.time()
        self.autosave_frequency = None
        self.data = {}
        self.data_exp = []

        if save_file:
            self.load()

    def record(self, cur_time, v1, v2, v3):
        self.lock.acquire()

        self.data[cur_time] = (v1, v2, v3)
        heappush(self.data_exp, cur_time)

        self.prune(cur_time)

        if (self.autosave_frequency and
              cur_time - self.last_savetime >= self.autosave_frequency):
            self.save()

        self.lock.release()

    def getData(self, time_range, cur_time = None, skip = None):
        if skip == None:
            skip = 0
        self.lock.acquire()
        if cur_time == None:
            cur_time = time.time()

        high_time = cur_time - skip
        low_time = high_time - time_range
        data = [(t, self.data[t]) for t in sorted((t for t in self.data
                                                   if (t <= high_time and
                                                       t >= low_time)))]

        self.lock.release()
        return data

    def prune(self, cur_time = None, age_limit = None, entry_limit = None):
        if cur_time == None:
            cur_time = time.time()
        if age_limit == None:
            age_limit = self.age_limit
        if entry_limit == None:
            entry_limit = self.entry_limit

        while ((age_limit != None and
                self.data_exp[0] < cur_time - age_limit) or
               (entry_limit != None and
                len(self.data) > entry_limit)):
            self.data.pop(heappop(self.data_exp))

    def save(self, filename = None, cur_time = None):
        if filename == None:
            filename = self.save_file
        if cur_time == None:
            cur_time = time.time()
        if filename == None:
            self.last_savetime = cur_time
            return False

        logging.debug("Writing data history to %s" % filename)
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except Exception as err:
                logging.error("Could not create directory %s: %s"
                               % (directory, err))
        self.lock.acquire()
        self.data_exp.sort()

        success = True
        try:
            fp = open(filename, "w", newline='')
            writer = csv.writer(fp, delimiter=' ', quoting=csv.QUOTE_MINIMAL)
            for t in self.data_exp:
                writer.writerow([t] + list(self.data[t]))
            fp.close()
        except Exception as err:
            logging.error("Could not write file %s: %s" % (filename, err))
            success = False

        self.lock.release()
        return success

    def load(self, filename = None, cur_time = None):
        if filename == None:
            filename = self.save_file
        if not filename or not os.path.exists(filename):
            return

        self.lock.acquire()
        if cur_time == None:
            cur_time = time.time()
        age_cutoff = (cur_time - self.age_limit
                      if self.age_limit != None else 0)
        new_data = {}
        new_data_exp = []
        try:
            fp = open(filename, "r", newline='')
            reader = csv.reader(fp, delimiter=' ')
            for row in reader:
                (t, v1, v2, v3) = (float(v) for v in row)
                if t >= age_cutoff:
                    new_data[t] = (v1, v2, v3)
                    if (self.entry_limit != None and
                          len(new_data) > self.entry_limit):
                        new_data.pop(heappushpop(new_data_exp, t))
                    else:
                        heappush(new_data_exp, t)
            fp.close()

            self.data = new_data
            self.data_exp = new_data_exp
            self.prune()
        except Exception as err:
            logging.error("Could not load tracker history from %s: %s"
                           % (filename, err))
        self.lock.release()

