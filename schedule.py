from functools import total_ordering
from heapq import heappush, heappop, heapify

import json
import os
import time

@total_ordering
class timeEntry:
    def verify(self):
        return ((self.day == None or (self.day >= 0 and self.day <= 6)) and
                self.hour >= 0 and self.hour <= 23 and
                self.minute >= 0 and self.minute <= 59)

    def __init__(self, a1=None, a2=None, a3=None):
        d = None
        h = None
        m = None
        if a2 == None:
            if a1 != None or a3 != None:
                raise ValueError
            localtime = time.localtime()
            d = localtime.tm_wday
            h = localtime.tm_hour
            m = localtime.tm_min
        else:
            if a3 == None:
                if a1 == None:
                    raise ValueError
                d = None
                h = a1
                m = a2
            else:
                d = a1
                h = a2
                m = a3

        self.day = d
        self.hour = h
        self.minute = m
        if not self.verify():
            raise ValueError((d,h,m))

    def __getitem__(self, i):
        return (self.day, self.hour, self.minute)[i]

    def __eq__(self, other):
        return (self.day == other[0] and
                self.hour == other[1] and
                self.minute == other[2])

    def __lt__(self, other):
        if self.hour != other.hour:
            return self.hour < other.hour
        if self.minute != other.minute:
            return self.minute < other.minute
        if self.day == None and other.day != None:
            return True
        if self.day != None and other.day == None:
            return False
        return self.day != other.day and self.day < other.day

    def __hash__(self):
        return (self.day, self.hour, self.minute).__hash__()

    def __repr__(self):
        return (self.day, self.hour, self.minute).__repr__()

    def timeUntil(self, target):
        if self == target:
            return 0

        d1 = self.day if self.day != None else 0
        week_minutes1 = 60*(24*d1 + self.hour) + self.minute
        d2 = target.day if target.day != None else 0
        week_minutes2 = 60*(24*d2 + target.hour) + target.minute

        return (week_minutes2 - week_minutes1)%(7*24*60)

class schedule:
    def __init__(self, filename=None):
        self.values = {}
        self.cur_time = timeEntry()
        self.cur_schedule = []
        self.cur_schedule_vals = set()

        self.filename=filename
        if filename:
            input_dict = None
            try:
                fp = open(filename, "r")
                input_data = json.load(fp)
                fp.close()
                for (i,l) in enumerate(input_data):
                    d = None
                    if i > 0:
                        d = i-1
                    for (h,m,t) in l:
                        self.addEntry(d, h, m, t)
            except Exception as err:
                print("Could not load schedule from", filename, ":", err)

    def __bool__(self):
        return self.values.__bool__()

    def addEntry(self, d, h, m, temp):
        newEntry = timeEntry(d, h, m)
        if ((newEntry.day == None or newEntry.day == self.cur_time.day) and
              newEntry > self.cur_time and
              newEntry not in self.cur_schedule_vals):
            heappush(self.cur_schedule, newEntry)
            self.cur_schedule_vals.add(newEntry)
        self.values[newEntry] = temp

    def deleteEntry(self, d, h, m):
        newEntry = timeEntry(d, h, m)
        if newEntry in self.values:
            self.values.pop(newEntry)
            # Not worth deleting froms cur_schedule, would be non-constant
            # time. Use defaults on dictionnary lookups to avoid ValueErrors,
            # and value tracking for cur_schedule to avoid duped adds

    def cleanIgnores(self):
        to_delete = set()
        for (e,v) in self.values.items():
            if v == None:
                if (e.day == None or
                    self.values.get((None,e.hour,e.minute), None) == None):
                    to_delete.add(e)
        for e in to_delete:
            self.values.pop(to_delete)

    def rebuildSchedule(self, day=None):
        d = self.cur_time.day
        new_schedule = [e for e in self.values
                          if (e.day == d or
                              (e.day == None and
                               (d, e.hour, e.minute) not in self.values))]

        heapify(new_schedule)

        self.cur_schedule = new_schedule
        self.cur_schedule_vals = set(new_schedule)

    def checkForUpdate(self):
        old_time = self.cur_time
        self.cur_time = timeEntry()

        new_temp = None
        if self.cur_time.day != old_time.day:
            while self.cur_schedule:
                new_temp = self.values.get(heappop(self.cur_schedule),
                                           new_temp)
            self.rebuildSchedule()

        while self.cur_schedule and self.cur_time >= self.cur_schedule[0]:
            new_temp = self.values.get(heappop(self.cur_schedule), new_temp)

        return new_temp

    def serialize(self):
        output = [[] for x in range(8)]
        for (time, temp) in self.values.items():
            output[0 if time.day == None else time.day+1].append(
                (time.hour, time.minute, temp))
        for l in output:
            l.sort()
        return output

    def tabled(self):
        times = []
        rows = []
        for (h,m) in sorted(set(((t.hour, t.minute) for t in self.values))):
            row = [None]*8
            row[0] = self.values.get((None,h,m), None)
            for x in list(range(7)):
                e = timeEntry(x,h,m)
                if e not in self.values:
                    row[x+1] = None
                elif self.values[e] == None and row[0] != None:
                    row[x+1] = "Ignore"
                else:
                    row[x+1] = self.values[e]
            if any(row):
                times.append((h,m))
                rows.append(row)
        return (times, rows)

    def mostRecentTemp(self):
        most_recent_val = None
        most_recent_dist = None
        for (e,v) in self.values.items():
            if v != None:
                if e.day == None:
                    for x in range(7):
                        e2 = timeEntry((self.cur_time.day - x)%7,
                                       e.hour,
                                       e.minute)
                        if e2 not in self.values:
                            e = e2
                            break
                if e.day != None:
                    if e == self.cur_time:
                        return v
                    dist = self.cur_time.timeUntil(e)
                    if most_recent_dist == None or dist < most_recent_dist:
                        most_recent_dist = dist
                        most_recent_val = v
        return most_recent_val

    def writeFile(self, filename=None):
        if filename == None:
            if self.filename == None:
                return False
            filename = self.filename

        directory = os.path.dirname(filename)
        if directory and not os.path.isdir(directory):
            try:
                os.makedirs(directory)
            except Exception as err:
                print("Could not create directory %s:" % directory, err)
                return False

        data = self.serialize()
        try:
            fp = open(filename, "w")
            json.dump(data, fp)
            fp.close()
        except Exception as err:
            print("Could not write file %s:" % fp, err)
            return False
        return True
