from flask import Flask, render_template, request, redirect

from thermostat import Thermostat

app = Flask(__name__)
thermostat = Thermostat()

@app.route("/thermostat", methods=["GET"])
def flaskThermostat():
    (Kp, Ki, Kd) = thermostat.getTunings()
    templateData = {
        "currentTemp" : round(thermostat.getCurrentTemp(), 2),
        "targetTemp" : thermostat.getTargetTemp(),
        "enabled" : ("Off", "On", "Force On")[thermostat.getEnabled()],
        "status" : round(100*thermostat.getStatus(), 2),
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
        pass
    try:
        Ki = float(request.form["Ki"])
    except Exception as err:
        pass
    try:
        Kd = float(request.form["Kd"])
    except Exception as err:
        pass

    thermostat.setTargetTemp(new_temp)
    thermostat.setTunings(Kp, Ki, Kd)
    thermostat.updateState()

    return redirect("/thermostat")

if __name__ == "__main__":
    @app.route("/")
    def redirectToThermostat():
        return redirect("/thermostat")

    app.run(host='0.0.0.0', port=80)

