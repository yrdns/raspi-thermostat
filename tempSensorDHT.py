import Adafruit_DHT as dht

def toFahrenheit(val):
    return 1.8*val + 32

class tempSensor:
    def __init__(self, pin=25):
        self.pin = pin
        self.most_recent_temp = None

    def updateTemp(self):
        return True

    def getTemp(self):
        try:
            (humidity, temp) = dht.read_retry(dht.DHT22, self.pin)
        except:
            return self.most_recent_temp

        temp = toFahrenheit(temp)
        self.most_recent_temp = temp
        return temp

