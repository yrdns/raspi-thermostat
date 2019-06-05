from functools import total_ordering
from heapq import heappush, heappop, heapify

import json
import os
import time

def verifyTimeEntry(e):
    return ((e[0] == None or (e[0] >= 0 and e[0] <= 6)) and
            e[1] >= 0 and e[1] <= 23 and
            e[2] >= 0 and e[2] <= 59)

def timeBetween(a, b):
    if a == b:
        return 0

    (d1, h1, m1) = a
    (d2, h2, m2) = b

    week_minutes1 = 60*(24*d1 + h1) + m1
    week_minutes2 = 60*(24*d2 + h2) + m2

    return (week_minutes2 - week_minutes1)%(7*24*60)

def curTime():
    localtime = time.localtime()
    return (localtime.tm_wday,
            localtime.tm_hour,
            localtime.tm_min)

class schedule:
    def __init__(self, filename=None):
        self.values = {}
        self.cur_time = curTime()
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

    def addEntry(self, d, h, m, t):
        (cd,ch,cm) = self.cur_time
        if ((d == None or d == cd) and
            (h, m) > (ch, cm) and
            (h, m) not in self.cur_schedule_vals):

            heappush(self.cur_schedule, (h, m))
            self.cur_schedule_vals.add((h, m))

        self.values[(d, h, m)] = t

    def deleteEntry(self, d, h, m):
        self.values.pop((d, h, m), None)
        # Not worth deleting froms cur_schedule, would be non-constant
        # time. Use defaults on dictionnary lookups to avoid ValueErrors,
        # and value tracking for cur_schedule to avoid duped adds

    def cleanIgnores(self):
        to_delete = set()
        for ((d, h, m), v) in self.values.items():
            if v == None and (d == None or
                              self.values.get((None, h, m), None) == None):
                to_delete.add((d, h, m))
        for e in to_delete:
            self.values.pop(e, None)

    def rebuildSchedule(self, day=None):
        dc = self.cur_time.day
        new_vals = set(((h,m) for (d,h,m) in self.values
                        if d == dc or d == None))
        new_schedule = list(new_vals)
        heapify(new_schedule)

        self.cur_schedule = new_schedule
        self.cur_schedule_vals = new_vals

    def lookupTime(self, d, h, m, default=None):
        result = None
        if (d, h, m) in self.values:
            result = self.values[(d, h, m)]
        else:
            result = self.values.get((None, h, m), None)
        if result != None:
            return result

        return default

    def checkForUpdate(self):
        (od, oh, om) = self.cur_time
        self.cur_time = curTime()
        (cd, ch, cm) = self.cur_time

        new_temp = None
        if cd != od:
            while self.cur_schedule:
                (h, m) = heappop(self.cur_schedule)
                new_temp = self.lookupTime(od, h, m, new_temp)
            self.rebuildSchedule()

        while self.cur_schedule and (ch, cm) >= self.cur_schedule[0]:
            (h, m) = heappop(self.cur_schedule)
            new_temp = self.lookupTime(cd, h, m, new_temp)

        return new_temp

    def serialize(self):
        output = [[] for x in range(8)]
        for ((d, h, m), t) in self.values.items():
            output[0 if d == None else d+1].append((h, m, t))
        for l in output:
            l.sort()
        return output

    def tabled(self):
        times = []
        rows = []
        for (h,m) in sorted(set(((h_, m_) for (d_, h_, m_) in self.values))):
            row = [None]*8
            row[0] = self.values.get((None,h,m), None)
            for x in list(range(7)):
                e = (x,h,m)
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

        (cd, ch, cm) = self.cur_time
        for ((d,h,m), v) in self.values.items():
            if v != None:
                if d == None:
                    d0 = cd
                    if (h,m) > (ch, cm):
                        d0 -= 1;
                    for x in range(7):
                        dn = (d0 - x)%7
                        if (dn, h, m) not in self.values:
                            d = dn
                            break
                if d != None:
                    if (d,h,m) == self.cur_time:
                        return v
                    dist = timeBetween((d,h,m), (cd, ch, cm))
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
