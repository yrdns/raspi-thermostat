from flask import Flask, render_template, request, redirect
from pyHS100 import SmartPlug, Discover
from wirelesstagpy import WirelessTags
from simple_pid import PID

import threading
import time

plug_name = "Heater"
tag_name = "Thermostat"

app = Flask(__name__)

gThermostatUpdateSignal = threading.Condition()

gToggle = 1
gSmartPlug = None
gMostRecentTemp = None
gMostRecentStatus = 0.0
gPid = PID(1.0, .1, .1, setpoint=70, output_limits=(0.0, 1.0))
gStatusChanged = False

def toFahrenheit(val):
    return 1.8*val + 32

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

def updateTemp():
    global gMostRecentTemp
    try:
        #print ("Searching for valid tag...")
        api = WirelessTags(username="kylej@mac.com", password="wirelesstaghomu")
        for (uuid, tag) in api.load_tags().items():
            if tag.name == tag_name:
                #print ("Found tag", tag.name, "with uuid", uuid)
                gMostRecentTemp = toFahrenheit(tag.sensor['temperature'].value)
                print ("Updated temperature to", gMostRecentTemp)
                return True
    except Exception as error:
        print ("Failed to update temperature due to exception:", error)
        return False
    print ("Failed to find tag named", tag_name)
    return False

def getCurrentTemp():
    return gMostRecentTemp

def getTargetTemp():
    return gPid.setpoint

def setTargetTemp(val):
    if gPid.setpoint == val:
        return
    print ("Updating new target temp from", gPid.setpoint, "to", val)
    gPid.setpoint = val
    updateStatus()

#def getStatus():
#    if gSmartPlug == None:
#        return -2
#    try:
#        cur_state = gSmartPlug.state
#        if cur_state == "ON":
#            return 1
#        if cur_state == "OFF":
#            return 0
#    except Exception as error:
#        print ("Plug state gave error <", error, "> attempting to re-discover...")
#        if (initializeSmartPlug()):
#            print ("Successful, retrying state read")
#            return getStatus()
#        print ("Failed, returning error")
#        return -3
#    return -1
def getStatus():
    return gMostRecentStatus

def setHeaterState(val):
    try:
        if val:
            print ("Turning heater on")
            gSmartPlug.turn_on()
        else:
            print ("Turning heater off")
            gSmartPlug.turn_off()
    except:
        print ("Plug state gave error, attempting to re-discover...")
        if (initializeSmartPlug()):
            print ("Successful, retrying state read")
            setHeaterState(val)
        else:
            print ("Failed, ignoring set state command")

#def updateStatus():
#    if getEnabled() == 2 or (getEnabled() == 1 and getCurrentTemp() != None and getCurrentTemp() < getTargetTemp()):
#        setStatus(1)
#    elif getEnabled() == 0 or (getEnabled() == 1 and getCurrentTemp() != None and getCurrentTemp() >= getTargetTemp()):
#        setStatus(0)
def updateStatus():
    global gStatusChanged
    gStatusChanged = True
    gThermostatUpdateSignal.notify()
    #gThermostatUpdateSignal.wait()

def getEnabled():
    return gToggle

def setEnabled(val):
    global gToggle
    val = min(max(int(val),0),2)
    gToggle = val
    updateStatus()

def getTunings():
    return gPid.tunings

def setTunings(Kp, Ki, Kd):
    gPid.tunings = (Kp, Ki, Kd)

def thermostatThread(update_signal):
    global gPid, gMostRecentStatus, gStatusChanged
    update_signal.acquire()
    next_check_time = time.time()
    while True:
        if not gStatusChanged:
            next_check_time += 60.0
        gStatusChanged = False

        print ("Checking thermostat...")
        updateTemp()
        #updateStatus()
        cur_status = gPid(getCurrentTemp())
        gMostRecentStatus = cur_status
        #update_signal.notify()

        cur_time = time.time()
        run_end_time = cur_time + cur_status*60.0
        if run_end_time > cur_time:
            print ("Running at ", cur_status)
            setHeaterState(1)

            cur_time = time.time()
            start_run = cur_time

            while run_end_time > cur_time and not gStatusChanged:
                update_signal.wait(min(run_end_time, next_check_time) - cur_time)
                cur_time = time.time()
            print ("Target run length:", cur_status*60.0, "Actual run length:", cur_time - start_run)

        if next_check_time > cur_time and not gStatusChanged:
            setHeaterState(0)
            cur_time = time.time()

            while next_check_time > cur_time and not gStatusChanged:
                update_signal.wait(next_check_time - cur_time)
                cur_time = time.time()

def initializeThermostat():
    if not initializeSmartPlug():
        print ("Initializing smart plug failed")
        return False

    # Setup thermostat loop
    timerThread = threading.Thread(target=thermostatThread, args=[gThermostatUpdateSignal])
    timerThread.daemon = True
    timerThread.start()

    return True

@app.route("/thermostat", methods=["GET"])
def flaskThermostat():
    (Kp, Ki, Kd) = getTunings()
    templateData = {
        "currentTemp" : round(getCurrentTemp(), 2),
        "targetTemp" : getTargetTemp(),
        "enabled" : ("Off", "On", "Force On")[getEnabled()],
        "status" : round(100*getStatus(), 2),
        "Kp" : Kp, "Ki" : Ki, "Kd" : Kd,
    }

    return render_template("main.html", **templateData)

@app.route("/thermostat", methods=["POST"])
def flaskThermostatUpdate():
    new_temp = None
    try:
        new_temp = float(request.form["temp"])
    except Exception as err:
        pass

    # Get lock to avoid concurrency & enable signaling
    # TODO: Signaling might not be working. Investigate
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

    (Kp, Ki, Kd) = getTunings()
    try:
        Kp = float(request.form["Kp"])
    except Exception as err:
        pass
    try:
        Ki = float(request.form["Ki"])
    except Exception as err:
        pass
    try:
        Kd = float(request.form["Kd"])
    except Exception as err:
        pass

    setTargetTemp(new_temp)
    setTunings(Kp, Ki, Kd)
    gThermostatUpdateSignal.release()

    return redirect("/thermostat")

if __name__ == "__main__":
    if not initializeThermostat():
        exit()

    @app.route("/")
    def redirectToThermostat():
        return redirect("/thermostat")

    app.run(host='0.0.0.0', port=80)

