from flask import Flask, render_template, request, redirect
import re

from thermostat import Thermostat

app = Flask(__name__)
thermostat = Thermostat()

dayNames = ("Every Day", "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday")
timeCommandRE = re.compile("(deleteTime|ignoreTime)([0-7])([0-2][0-9])([0-5][0-9])")

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
    templateData = {
        "currentTemp" : round(thermostat.getCurrentTemp(), 2),
        "targetTemp" : thermostat.getTargetTemp(),
        "enabled" : ("Off", "On", "Force On")[thermostat.getEnabled()],
        "status" : round(100*thermostat.getStatus(), 2),
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

            return redirect("/thermostat")
        except Exception as err:
            print("Caught", err)

    new_temp = None
    try:
        new_temp = float(request.form["temp"])
    except Exception as err:
        print("Caught", err)

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

    (Kp, Ki, Kd) = thermostat.getTunings()
    try:
        Kp = float(request.form["Kp"])
    except Exception as err:
        print("Caught", err)
    try:
        Ki = float(request.form["Ki"])
    except Exception as err:
        print("Caught", err)
    try:
        Kd = float(request.form["Kd"])
    except Exception as err:
        print("Caught", err)

    thermostat.setTargetTemp(new_temp)
    thermostat.setTunings(Kp, Ki, Kd)
    thermostat.updateState()

    return redirect("/thermostat")

if __name__ == "__main__":
    @app.route("/")
    def redirectToThermostat():
        return redirect("/thermostat")

    app.run(host='0.0.0.0', port=80)

