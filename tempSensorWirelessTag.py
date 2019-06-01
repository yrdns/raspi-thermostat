from wirelesstagpy import WirelessTags

def toFahrenheit(val):
    return 1.8*val + 32

class tempSensor:
    def __init__(self, name = "Thermostat"):
        self.name = name
        self.most_recent_temp = None

    def updateTemp(self):
        try:
            #print ("Searching for valid tag...")
            api = WirelessTags(username="kylej@mac.com", password="wirelesstaghomu")
            for (uuid, tag) in api.load_tags().items():
                if tag.name == self.name:
                    #print ("Found tag", tag.name, "with uuid", uuid)
                    self.most_recent_temp = toFahrenheit(tag.sensor['temperature'].value)
                    print ("Updated temperature to", self.most_recent_temp)
                    return True
        except Exception as error:
            print ("Failed to update temperature due to exception:", error)
            return False
        print ("Failed to find tag named", tag_name)
        return False

    def getTemp(self):
        return self.most_recent_temp

