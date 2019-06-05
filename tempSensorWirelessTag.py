from wirelesstagpy import WirelessTags

import logging

def toFahrenheit(val):
    return 1.8*val + 32

class tempSensor:
    def __init__(self, name = "Thermostat"):
        self.name = name
        self.most_recent_temp = None

    def updateTemp(self):
        try:
            logging.debug("Searching for valid tag...")
            api = WirelessTags(username="kylej@mac.com", password="wirelesstaghomu")
            for (uuid, tag) in api.load_tags().items():
                if tag.name == self.name:
                    logging.debug("Found tag %s with uuid %s" % (tag.name, uuid))
                    self.most_recent_temp = toFahrenheit(tag.sensor['temperature'].value)
                    logging.debug("Updated temperature to %f" % self.most_recent_temp)
                    return True
        except Exception as error:
            logging.exception("Failed to update temperature due to exception")
            return False
        logging.error("Failed to find tag named %s" % tag_name)
        return False

    def getTemp(self):
        return self.most_recent_temp

