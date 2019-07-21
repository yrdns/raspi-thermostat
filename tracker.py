from collections import deque
from itertools import islice

import csv
import logging
import os
import time
import threading

class dataTracker:
    def __init__(self, nvals=1, save_file = None, autosave_frequency = None,
                 age_limit = None, entry_limit = None, noise_filters = []):
        self.lock = threading.RLock()

        self.nvals = nvals

        self.age_limit = age_limit
        self.data = deque(maxlen=entry_limit)
        self.noise_filters = noise_filters

        self.save_file = save_file
        self.last_savetime = time.time()
        self.autosave_frequency = autosave_frequency

        if save_file:
            self.load()

    def mostRecent(self):
        return self.data[-1][1:] if self.data else (None, None)

    def record(self, cur_time, *vals):
        if len(vals) > self.nvals:
            vals = vals[:self.nvals]
        if len(vals) != self.nvals:
            raise ValueError("Tracker expected %d values, got %d"
                              % (self.nvals, len(vals)))
        cur_time = int(cur_time + .5)
        add_entry = True
        success = True

        split = None
        entry = (cur_time,) + tuple(vals)

        self.lock.acquire()
        if self.data:
            if self.data[-1][0] == cur_time:
                logging.warning(
                    "Duplicate time code on entry %s, discarding"
                             % (entry,))
                add_entry = False
            else:
                if cur_time < self.data[-1][0]:
                    logging.warning(
                        "Queue time %f greater then current time %f"
                                     % (self.data[-1][0], cur_time))
                    split = [self.data.pop()]
                    while cur_time < self.data[-1][0]:
                        split.append(self.data.pop())

                for i in range(min(len(self.noise_filters), self.nvals)):
                    if self.noise_filters[i]:
                        # Sample d/dt
                        d_dt = ((vals[i]-self.data[-1][i+1]) /
                                (cur_time-self.data[-1][0]))

                        if abs(d_dt) > self.noise_filters[i]:
                            logging.warning(
"Change on entry %s[%d] from record %s is greater than threshold (d/dt = %f)"
                                % (entry, i, self.data[-1], d_dt))
                            success = False
                            add_entry = False

        if add_entry:
            self.data.append(entry)
            if split:
                self.data.extend(reversed(split))

        self.prune(cur_time)

        if (self.autosave_frequency and
            cur_time - self.last_savetime >= self.autosave_frequency):
            self.save()

        self.lock.release()
        return success

    def getData(self, start_time = None, end_time = None,
                stride = None, bin_count = None):
        self.lock.acquire()
        if start_time == None:
            start_time = self.data[0][0]
        if end_time == None:
            end_time = self.data[-1][0]

        if stride == None and bin_count != None:
            stride = time_range / bin_count

        cur_bin = end_time
        cur_acc = [0]*self.nvals
        cur_count = 0
        result = []
        # This SHOULD be in place, which is important as we intend to only
        # partially exhaust iterator:
        for e in reversed(self.data):
            if stride != None and (cur_bin - e[0] >= stride or
                                   e[0] < start_time):
                if cur_count > 0:
                    result.append((cur_bin, *(x / cur_count
                                              for x in cur_acc)))
                cur_acc = [0]*self.nvals
                cur_count = 0
                cur_bin -= stride*((cur_bin-e[0]) // stride)

            if e[0] < start_time:
                break
            if e[0] <= end_time:
                if stride == None:
                    result.append(e)
                else:
                    for i in range(self.nvals):
                        cur_acc[i] += e[i+1]
                    cur_count += 1

        self.lock.release()
        return result

    def prune(self, cur_time = None, age_limit = None):
        if cur_time == None:
            cur_time = time.time()
        if age_limit == None:
            age_limit = self.age_limit

        if self.data and age_limit != None:
            while self.data[0][0] < cur_time - age_limit:
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

        old_data = self.data
        try:
            fp = open(filename, "r", newline='')
            reader = csv.reader(fp, delimiter=' ')

            self.data = deque(maxlen=self.data.maxlen)
            error_count = 0
            for row in reader:
                try:
                    row = [float(v) for v in row]
                    if row[0] >= age_cutoff:
                        self.record(*row)
                except (IndexError, ValueError) as err:
                    if error_count == 0:
                        logging.error(
                            "Bad tracker csv line < %s > in file \"%s\""
                             % (row, filename))
                        logging.error(
                            "Skipping line, suppressing further errors")
                        error_count += 1
            if error_count > 0:
                logging.Error("%d bad lines found")
            fp.close()

        except Exception as err:
            logging.error("Could not load data from %s: %s"
                           % (filename, err))
            self.data = old_data

        self.lock.release()

