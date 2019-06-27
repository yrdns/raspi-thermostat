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
        temp = self.most_recent_temp
        humidity = self.most_recent_humidity
        try:
            (humidity, temp) = dht.read_retry(dht.DHT22, self.pin)
            humidity /= 100
        except Exception as err:
            logging.warning("Couldn't read sensor, returning last known value %s. %s"
                             % (self.most_recent_reading, err))
            return self.most_recent_reading

        if temp != None:
            temp = toFahrenheit(temp)
            self.most_recent_temp = temp
        if humidity != None:
            self.most_recent_humidity = humidity

        return (temp, humidity)

