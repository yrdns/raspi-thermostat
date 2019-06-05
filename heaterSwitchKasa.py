from pyHS100 import SmartPlug, Discover

import logging

class heaterSwitch():
    def __init__(self, name="Heater"):
        self.name = name
        self.state = 0

        self.initializeSmartPlug()

    def initializeSmartPlug(self):
        self.smart_plug = None
        logging.info("Searching for valid plug...")
        try:
            for (ip, plug) in Discover.discover().items():
                if self.name == plug.sys_info["alias"]:
                    logging.info("Found plug %s at address %s" % (self.name, ip))
                    self.smart_plug = plug
                    return True
        except Exception as error:
            logging.exception("Failed to initialize smart switch %s")
        logging.error("Could not find any plug named %s" % self.name)
        return False

    def setState(self, val):
        try:
            if val:
                logging.debug("Turning heater on")

                self.smart_plug.turn_on()
            else:
                logging.debug("Turning heater off")
                self.smart_plug.turn_off()
            self.state = val
        except:
            logging.exception("Plug state gave error, attempting to re-discover...")
            if (self.initializeSmartPlug()):
                logging.error("Successful, retrying state read")
                # Does python support tail recursion?
                return self.setState(val)
            else:
                logging.error("Re-discovery failed, ignoring setState")

    def getState(self):
        return self.state

    def lookupState():
        if self.smart_plug == None:
            return -2
        try:
            cur_state = self.smart_plug.state
            if cur_state == "ON":
                return 1
            if cur_state == "OFF":
                return 0
        except Exception as error:
            logging.exception("Plug state threw error attempting to re-discover...")
            if (self.initializeSmartPlug()):
                logging.error("Successful, retrying state read")
                return self.lookupState()
            logging.error("Failed, returning error")
            return -3
        return -1

