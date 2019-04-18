from flask import Flask, render_template, request, redirect, url_for
from pyHS100 import SmartPlug, Discover
from wirelesstagpy import WirelessTags

import threading

plug_name = "Heater"
tag_name = "Thermostat"

app = Flask(__name__)

gThermostatUpdateSignal = threading.Condition()

gTargetTemp = 70
gToggle = 1
gSmartPlug = None
gMostRecentTemp = None
gWirelessTagUUID = None

def toFahrenheit(val):
    return 1.8*val + 32

def tagApi():
    return WirelessTags(username="kylej@mac.com", password="wirelesstaghomu")

def initializeSmartPlug():
    global gSmartPlug
    gSmartPlug = None
    print ("Searching for valid plug...")
    try:
        for (ip, plug) in Discover.discover().items():
            if plug_name == plug.sys_info["alias"]:
                print ("Found plug", plug_name, "at address", ip)
                gSmartPlug = plug
                return True
    except Exception as error:
        print ("Failed to initialize due to exception:", error)
    print ("ERROR: Could not find any plug named", plug_name)
    return False

def initializeWirelessTag():
    global gMostRecentTemp, gWirelessTagUUID
    try:
        print ("Searching for valid tag...")
        api = tagApi()
        for (uuid, tag) in api.load_tags().items():
            if tag.name == tag_name:
                print ("Found tag", tag.name, "with uuid", uuid)
                gMostRecentTemp = toFahrenheit(tag.sensor['temperature'].value)
                gWirelessTagUUID = uuid
                print ("Updated temperature to", gMostRecentTemp)
                return True
    except Exception as error:
        print ("Failed to initialize tag due to exception:", error)
        return False
    print ("ERROR: Could not find tag named", tag_name)
    return False

def updateTemp():
    global gMostRecentTemp
    try:
        api = tagApi()
        gMostRecentTemp = toFahrenheit(api.load_tags()[gWirelessTagUUID].sensor['temperature'].value)
        print ("Updated temperature to", gMostRecentTemp)
        return True
    except Exception as error:
        print ("Failed to update temperature due to exception:", error)
    return False

def getCurrentTemp():
    return gMostRecentTemp

def getTargetTemp():
    return gTargetTemp

def setTargetTemp(val):
    global gTargetTemp
    if gTargetTemp == val:
        return
    gThermostatUpdateSignal.acquire()
    print ("Updating new target temp from", gTargetTemp, "to", val)
    gTargetTemp = val
    updateStatus()

def getStatus():
    if gSmartPlug == None:
        return -2
    try:
        cur_state = gSmartPlug.state
        if cur_state == "ON":
            return 1
        if cur_state == "OFF":
            return 0
    except Exception as error:
        print ("Plug state gave error <", error, "> attempting to re-discover...")
        if (initializeSmartPlug()):
            print ("Successful, retrying state read")
            return getStatus()
        print ("Failed, returning error")
        return -3
    return -1

def setStatus(val):
    try:
        if val:
            if getStatus() != 1:
                print ("Turning heater on")
                gSmartPlug.turn_on()
        else:
            if getStatus() != 0:
                print ("Turning heater off")
                gSmartPlug.turn_off()
    except:
        print ("Plug state gave error, attempting to re-discover...")
        if (initializeSmartPlug()):
            print ("Successful, retrying state read")
            setStatus(val)
        else:
            print ("Failed, ignoring set state command")

def updateStatus():
    if getEnabled() == 2 or (getEnabled() == 1 and getCurrentTemp() != None and getCurrentTemp() < getTargetTemp()):
        setStatus(1)
    elif getEnabled() == 0 or (getEnabled() == 1 and getCurrentTemp() != None and getCurrentTemp() >= getTargetTemp()):
        setStatus(0)

def getEnabled():
    return gToggle

def setEnabled(val):
    global gToggle
    gThermostatUpdateSignal.acquire()
    val = min(max(int(val),0),2)
    gToggle = val
    updateStatus()

def thermostatThread(update_signal):
    global gSmartPlugStatus
    update_signal.acquire()
    while True:
        print ("Checking thermostat...")
        updateTemp()
        updateStatus()

        update_signal.notify()
        update_signal.wait(60)

def initializeThermostat():
    if not initializeSmartPlug():
        print ("Initializing smart plug failed")
        return False
    if not initializeWirelessTag():
        print ("Initializing tag failed")
        return False

    # Setup thermostat loop
    timerThread = threading.Thread(target=thermostatThread, args=[gThermostatUpdateSignal])
    timerThread.daemon = True
    timerThread.start()

    return True

@app.route("/thermostat", methods=["GET"])
def flaskThermostat():
    templateData = {
        "currentTemp" : round(getCurrentTemp(), 2),
        "targetTemp" : getTargetTemp(),
        "enabled" : ("Off", "On", "Force On")[getEnabled()],
        "status" : "Running" if getStatus() else ("Standby" if getEnabled() == 1 else "Disabled"),
    }

    return render_template("main.html", **templateData)

@app.route("/thermostat", methods=["POST"])
def flaskThermostatUpdate():
    new_temp = None
    try:
        new_temp = float(request.form["temp"])
    except:
        pass

    # Get lock just in case
    gThermostatUpdateSignal.acquire()

    if new_temp == None:
        new_temp = getTargetTemp()
    if "decrease_temp" in request.form:
        new_temp -= 1
    if "increase_temp" in request.form:
        new_temp += 1
    if "enable" in request.form:
        setEnabled(1)
    if "disable" in request.form:
        setEnabled(0)
    if "force_on" in request.form:
        setEnabled(2)

    setTargetTemp(new_temp)
    gThermostatUpdateSignal.release()

    return redirect("/thermostat")

if __name__ == "__main__":
    if not initializeThermostat():
        exit()

    app.run(host='0.0.0.0', port=80)
