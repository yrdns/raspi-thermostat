from thermostat import Thermostat

from flask import Flask, render_template, request, redirect
import logging
import re
import signal
import time

def format_runtime(t):
    t = int(t+.5)
    return "%02dh:%02dm:%02ds" % (t//3600, (t%3600)//60, t%60)

def format_date(d):
    return "%d-%d" % (d[1], d[2])

def format_datetime_short(t):
    return time.strftime("%Y%m%dT%H%M%S", time.localtime(t))

logging.basicConfig(level="INFO")

app = Flask(__name__)
thermostat = Thermostat(pref_file="prefs/thermostat.json",
                        schedule_file="prefs/schedule.json",
                        runhistory_file="prefs/usage_history.csv",
                        trackerdata_file="prefs/stats.csv")

dayNames = ["Every Day", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"]
timeCommandRE = re.compile(
"(deleteTime|ignoreTime)([0-7])([0-2][0-9])([0-5][0-9])")

@app.route("/thermostat", methods=["GET"])
def flaskThermostat():
    (Kp, Ki, Kd) = thermostat.getTunings()
    (scheduleTimes, scheduleRows) = thermostat.schedule.tabled()
    if not scheduleTimes:
        scheduleTimes = [(0,0)]
        scheduleRows = [[None]*8]
    scheduleTimes = [("%02d:%02d %s" % ((h+11)%12 + 1, m,
                                          "AM" if h<12 else "PM"),
                      "%02d%02d" % (h, m))
                       for (h,m) in scheduleTimes]
    run_times = [(format_date(d), t) for (d, t) in
                  reversed(thermostat.getPastRuntimes(7))]
    temp_history = [(format_datetime_short(t), v1, v2, v3)
                    for (t, v1, v2, v3)
                    in thermostat.getSensorHistory(7*24*60*60)]

    (temp, humidity) = thermostat.readSensor()
    templateData = {
        "currentTemp" : round(temp, 2),
        "currentHumidity" : round(100*humidity, 2),
        "targetTemp" : thermostat.getTargetTemp(),
        "enabled" : ("Off", "On", "Force On")[thermostat.getEnabled()],
        "status" : round(100*thermostat.getStatus(), 2),
        "todaysRuntime" : format_runtime(run_times[-1][1]),
        "usageHistory" : run_times,
        "tempHistory" : temp_history,
        "Kp" : Kp, "Ki" : Ki, "Kd" : Kd,
        "dayNames" : dayNames,
        "scheduleTimes" : scheduleTimes,
        "scheduleRows" : scheduleRows,
    }

    return render_template("main.html", **templateData)

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

    if "edit_tunings" in request.form:
        try:
            Kp = float(request.form["Kp"])
            Ki = float(request.form["Ki"])
            Kd = float(request.form["Kd"])
            thermostat.setTunings(Kp, Ki, Kd)
            thermostat.updateState()
        except Exception as err:
            logging.exception("Parsing edit_tunings caught exception")
        return redirect("/thermostat")

    new_temp = None
    try:
        new_temp = float(request.form["temp"])
    except Exception as err:
        logging.exception("Parsing temp caught exception")

    # Get lock to avoid concurrency & enable signaling
    if new_temp == None:
        new_temp = thermostat.getTargetTemp()
    if "decrease_temp" in request.form:
        new_temp -= 1
    if "increase_temp" in request.form:
        new_temp += 1
    if "enable" in request.form:
        thermostat.setEnabled(1)
    if "disable" in request.form:
        thermostat.setEnabled(0)
    if "force_on" in request.form:
        thermostat.setEnabled(2)

    thermostat.setTargetTemp(new_temp)
    thermostat.updateState()

    return redirect("/thermostat")

if __name__ == "__main__":
    def graceful_exit(signum, frame):
        logging.warning("Received signal %d, exiting gracefully...", signum)
        thermostat.savePrefs()
        thermostat.schedule.saveSchedule()
        thermostat.saveRunHistory()
        thermostat.saveSensorHistory()
        logging.warning("Cleanup complete.")
        exit()

    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    @app.route("/")
    def redirectToThermostat():
        return redirect("/thermostat")

    app.run(host='0.0.0.0', port=80)

