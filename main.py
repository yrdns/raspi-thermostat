from thermostat import Thermostat

from flask import Flask, jsonify, redirect, render_template, request
import logging
import re
import signal
import time

def format_runtime(t):
    t = int(t+.5)
    return "%02dh:%02dm:%02ds" % (t//3600, (t%3600)//60, t%60)

def format_date(d):
    return "%d/%d" % (d[1], d[2])

def format_datetime_short(t):
    return time.strftime("%Y%m%dT%H%M%S", time.localtime(t))

logging.basicConfig(level="INFO")

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

thermostat = Thermostat(pref_file         = "prefs/thermostat.json",
                        schedule_file     = "prefs/schedule.json",
                        runhistory_file   = "prefs/usage.csv",
                        activitydata_file = "prefs/activity.csv",
                        tempdata_file     = "prefs/stats.csv")

dayNames = ["Every Day", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]
timeCommandRE = re.compile(
"(deleteTime|ignoreTime)([0-7])([0-2][0-9])([0-5][0-9])")

def simpleStats():
    (last_temp, last_humi) = thermostat.getLastReading()
    if last_temp != None:
        last_temp = round(last_temp, 2)
    if last_humi != None:
        last_humi = round(100*last_humi, 2)

    data = {
        "currentTemp" : last_temp,
        "currentHumidity" : last_humi,
        "targetTemp" : round(thermostat.getTargetTemp(), 2),
        "enabled" : ("Off", "On", "Force On")[thermostat.getEnabled()],
        "onval" : round(100*thermostat.getStatus(), 2),
        "todaysRuntime" : format_runtime(thermostat.getCurRuntime()),
    }
    return data

def updateStats(start_time):
    data = simpleStats()

    runtimes = thermostat.getPastRuntimes(7)
    runtimes.reverse()
    data["runtimeLabels"] = [format_date(e[0]) for e in runtimes]
    data["runtimes"]      = [e[1] for e in runtimes]

    cur_time = time.time()
    stats = thermostat.getSensorHistory(start_time = start_time,
                                        end_time = cur_time)
    data["times"]  = [format_datetime_short(e[0]) for e in reversed(stats)]
    data["temps"]  = [e[1] for e in reversed(stats)]
    data["humis"]  = [100*e[2] for e in reversed(stats)]

    stats = thermostat.getActivityHistory(start_time = start_time,
                                          end_time = cur_time)
    data["ontimes"] = [format_datetime_short(e[0]) for e in reversed(stats)]
    data["onvals"]  = [100*e[1] for e in reversed(stats)]

    data["lastTime"] = cur_time
    data["waitTime"] = thermostat.getWaitTime() + 2.0

    return data

def templateStats():
    data = simpleStats()

    (Kp, Ki, Kd) = thermostat.getTunings()
    data["Kp"] = Kp
    data["Ki"] = Ki
    data["Kd"] = Kd

    (scheduleTimes, scheduleRows) = thermostat.schedule.tabled()
    if not scheduleTimes:
        scheduleTimes = [(0,0)]
        scheduleRows = [[None]*8]
    scheduleTimes = [("%02d:%02d %s" % ((h+11)%12 + 1, m,
                                          "AM" if h<12 else "PM"),
                      "%02d%02d" % (h, m))
                       for (h,m) in scheduleTimes]
    data["dayNames"]      = dayNames
    data["scheduleTimes"] = scheduleTimes
    data["scheduleRows"]  = scheduleRows

    return data

@app.route("/update.json")
def flaskUpdate():
    try:
        last_time = float(request.args.get("t"))
    except (ValueError, TypeError):
        last_time = None

    return jsonify(updateStats(last_time))

def apiError():
    return jsonify({"success": False})

@app.route("/api")
def flaskAPI():
    command = request.args.get("q")

    if command == "setTemp":
        try:
            val = float(request.args["v"])
        except (KeyError, ValueError, TypeError):
            return apiError()

        thermostat.setTargetTemp(val)
        thermostat.updateState(True)

    elif command == "increaseTemp":
        thermostat.setTargetTemp(thermostat.getTargetTemp() + 1)
        thermostat.updateState(True)

    elif command == "decreaseTemp":
        thermostat.setTargetTemp(thermostat.getTargetTemp() - 1)
        thermostat.updateState(True)

    elif command == "setPIDs":
        try:
            Kp = float(request.args["Kp"])
            Ki = float(request.args["Ki"])
            Kd = float(request.args["Kd"])
        except (KeyError, ValueError, TypeError):
            return apiError()

        thermostat.setTunings(Kp, Ki, Kd)
        thermostat.updateState(True)

    elif command == "setState":
        try:
            val = ("off","on","force").index(request.args["v"])
        except (ValueError, KeyError):
            return apiError()

        thermostat.setEnabled(val)
        thermostat.updateState(True)

    data = simpleStats()
    data["success"] = True

    return jsonify(data)

@app.route("/thermostat", methods=["GET"])
def flaskThermostat():
    return render_template("main.html", **templateStats())

@app.route("/thermostat", methods=["POST"])
def flaskThermostatUpdate():
    for name in request.form:
        m = timeCommandRE.fullmatch(name)
        if m:
            day = int(m.group(2))
            day = None if day == 0 else day-1
            hour = int(m.group(3))
            minute = int(m.group(4))
            if m.group(1) == "ignoreTime":
                thermostat.schedule.addEntry(day, hour, minute, None)
            else:
                thermostat.schedule.deleteEntry(day, hour, minute)

            thermostat.schedule.saveSchedule()
            return redirect("/thermostat")

    if "add_time" in request.form:
        try:
            day = int(request.form["schedule_day"])
            day = None if day == 0 else day-1

            (hour, minute) = request.form["schedule_time"].split(":")
            hour = int(hour)
            minute = int(minute)

            temp = float(request.form["schedule_temp"])
            thermostat.schedule.addEntry(day, hour, minute, temp)

            thermostat.schedule.saveSchedule()
        except Exception as err:
            logging.exception("Parsing add_time caught exception")

        return redirect("/thermostat")

    return redirect("/thermostat")

if __name__ == "__main__":
    def graceful_exit(signum, frame):
        logging.warning("Received signal %d, exiting gracefully...", signum)
        thermostat.savePrefs()
        thermostat.schedule.saveSchedule()
        thermostat.saveRunHistory()
        thermostat.saveDataFiles()

        thermostat.display.clear()
        logging.warning("Cleanup complete.")
        exit()

    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    @app.route("/")
    def redirectToThermostat():
        return redirect("/thermostat")

    app.run(host='0.0.0.0', port=80)

