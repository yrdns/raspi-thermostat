from collections import deque
from itertools import islice

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
        self.data = deque(maxlen=entry_limit)

        self.save_file = save_file
        self.last_savetime = time.time()
        self.autosave_frequency = autosave_frequency

        if save_file:
            self.load()

    def record(self, cur_time, v1, v2, v3):
        self.lock.acquire()

        entry = (cur_time, v1, v2, v3)
        if cur_time < self.data[-1][0]:
            logging.warning("Queue time %f greater then current time %f"
                             % (self.data[-1][0], cur_time))
            split = [self.data.pop()]
            while cur_time < self.data[-1][0]:
                split.append(self.data.pop)

            self.data.append(entry)
            self.data.extend(reversed(split))
        else:
            self.data.append(entry)

        self.prune(cur_time)

        if (self.autosave_frequency and
              cur_time - self.last_savetime >= self.autosave_frequency):
            self.save()

        self.lock.release()

    def getData(self, time_range, start_time = None, skip = None, stride = None, bin_count = None):
        self.lock.acquire()
        if start_time == None:
            start_time = self.data[-1][0]
        if skip != None:
            start_time -= skip
        end_time = start_time - time_range
        
        if stride == None and bin_count != None:
            stride = time_range / bin_count

        cur_bin = start_time
        cur_acc = [0,0,0]
        cur_count = 0
        result = []
        # This SHOULD be in place, which is important as we intend to only
        # partially exhaust iterator:
        for e in reversed(self.data):
            if e[0] < end_time:
                break
            if e[0] <= start_time:
                if stride == None:
                    result.append(e)
                else:
                    while cur_bin - e[0] >= stride:
                        if cur_count > 0:
                            cur_acc[0] /= cur_count
                            cur_acc[1] /= cur_count
                            cur_acc[2] /= cur_count
                        result.append((cur_bin, cur_acc[0], cur_acc[1], cur_acc[2]))
                        cur_acc = [0,0,0]
                        cur_count = 0
                        cur_bin -= stride

                    cur_acc[0] += e[1]
                    cur_acc[1] += e[2]
                    cur_acc[2] += e[3]
                    cur_count += 1

        self.lock.release()
        return result

    def prune(self, cur_time = None, age_limit = None):
        if cur_time == None:
            cur_time = time.time()
        if age_limit == None:
            age_limit = self.age_limit

        while age_limit != None and self.data[0][0] < cur_time - age_limit:
            self.data.popleft()

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

        success = True
        try:
            fp = open(filename, "w", newline='')
            writer = csv.writer(fp, delimiter=' ', quoting=csv.QUOTE_MINIMAL)

            writer.writerows(self.data)
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
        new_data = []
        try:
            fp = open(filename, "r", newline='')
            reader = csv.reader(fp, delimiter=' ')
            for row in reader:
                (t, v1, v2, v3) = (float(v) for v in row)
                if t >= age_cutoff:
                    new_data.append((t, v1, v2, v3))
            fp.close()

            new_data.sort()
            self.data = deque(new_data, self.data.maxlen)
            del new_data

        except Exception as err:
            logging.error("Could not load tracker history from %s: %s"
                           % (filename, err))

        self.lock.release()

