from functools import total_ordering
from heapq import heappush, heappop, heapify
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

    def __eq__(self, other):
        return (self.day == other.day and
                self.hour == other.hour and
                self.minute == other.minute)

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

class schedule:
    def __init__(self):
        self.values = {}
        self.cur_time = timeEntry()
        self.cur_schedule = []
        self.cur_schedule_vals = set()

    def addEntry(self, d, h, m, temp):
        newEntry = timeEntry(d, h, m)
        if ((newEntry.day == None or newEntry.day == self.cur_time.day) and
              newEntry > self.cur_time and
              newEntry not in self.cur_schedule_vals):
            heappush(self.cur_schedule, newEntry)
            self.cur_schedule_vals.add(newEntry)
        self.values[newEntry] = temp

    def delEntry(self, d, h, m):
        newEntry = timeEntry(d, h, m)
        if newEntry in self.values:
            self.values.pop(newEntry)
            # Not worth deleting froms cur_schedule, would be non-constant
            # time. Use defaults on dictionnary lookups to avoid ValueErrors,
            # and value tracking for cur_schedule to avoid duped adds

    def rebuildSchedule(self):
        new_schedule = [e for e in self.values
                          if e.day == None or e.day == self.cur_time.day]
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

