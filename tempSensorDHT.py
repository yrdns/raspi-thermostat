from tracker import dataTracker

import Adafruit_DHT as dht
import logging

def toFahrenheit(val):
    return 1.8*val + 32

class tempSensor:
    def __init__(self, save_file = None, pin = 25):
        self.pin = pin

        self.tracker = dataTracker(2, save_file = save_file,
                                   autosave_frequency = 10*60,
                                   age_limit = 7*24*60*60,
                                   noise_filters = [10.0/60, 0.1/60])

        # To update most recents
        (temp, humidity) = self.read()

        if temp == None or humidity == None:
            raise ValueError("Can't detect sensor on pin %d")

    def mostRecent(self):
        return self.tracker.mostRecent()

    def read(self, cur_time = None, ntries = 10):
        temp = None
        humidity = None

        for i in range(ntries):
            try:
                (humidity, temp) = dht.read_retry(dht.DHT22, self.pin)
            except Exception as err:
                logging.error("Sensor read caught error: %s" % err)
                continue

            if humidity != None and temp != None:
                humidity /= 100
                temp = toFahrenheit(temp)

                if (cur_time == None or
                    self.tracker.record(cur_time,
                                        temp,
                                        humidity)):
                    break
            temp = None
            humidity = None

        if temp == None or humidity == None:
            most_recent_vals = self.mostRecent()

            logging.warning(
 "Failed to read sensor, returning last known values (%s, %s)."
                             % most_recent_vals)
            return most_recent_vals

        return (temp, humidity)

