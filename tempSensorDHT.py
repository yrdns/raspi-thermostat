import Adafruit_DHT as dht

import logging

def toFahrenheit(val):
    return 1.8*val + 32

class tempSensor:
    def __init__(self, pin=25):
        self.pin = pin

        self.most_recent_temp = None
        self.most_recent_humidity = None

    def read(self):
        temp = None
        humidity = None
        try:
            (humidity, temp) = dht.read_retry(dht.DHT22, self.pin)
            humidity /= 100
        except Exception as err:
            logging.warning(
 "Couldn't read sensor, returning last known values (%s, %s). %s"
                             % (self.most_recent_temp,
                                self.most_recent_humidity,
                                err))
            return (self.most_recent_temp, self.most_recent_humidity)

        if temp == None or humidity == None:
            logging.warning(
 "Failed to read sensor, returning last known values (%s, %s)."
                             % (self.most_recent_temp,
                                self.most_recent_humidity))
            temp = self.most_recent_temp
            humidity = self.most_recent_humidity
        else:
            temp = toFahrenheit(temp)
            self.most_recent_temp = temp
            self.most_recent_humidity = humidity

        return (temp, humidity)

