function apiCommand(command, args = {}) {
    $.getJSON("api", Object.assign({"q":command}, args), updateInfoBox);
}

function setTemp() {
    apiCommand("setTemp", {"v" : $("#tempInput").val()});
}

function increaseTemp() {
    apiCommand("increaseTemp");
}

function decreaseTemp() {
    apiCommand("decreaseTemp");
}

function setPIDs() {
    apiCommand("setPIDs", {"Kp" : $("#KpInput").val(),
                           "Ki" : $("#KiInput").val(),
                           "Kd" : $("#KdInput").val()});
}

function setState(state) {
    apiCommand("setState", {"v" : state});
}
