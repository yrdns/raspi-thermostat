function updateLoop(lastTime, statsTime) {
    $.getJSON("update.json", {t : lastTime, ts:statsTime}, function(data) {
        updateInfoBox(data);
        updateCharts(data);

        setTimeout(function() {
                       updateLoop(data.lastTime, data.nextStatsTime);
                   }, data.waitTime * 1000);
    }).fail(function() {
        console.log("Error: Couldn't update state");
        setTimeout(function() { updateLoop(lastTime, statsTime); },
                   60000);
    });
}

function updateTarget(temp) {
    $("#targetField").text(temp);
    $("#tempInput").not(":focus").val(temp);
}

function updateInfoBox(data) {
    $("#statusField").text(data.enabled);
    $("#tempField").text(data.currentTemp);
    updateTarget(data.targetTemp);
    $("#humidityField").text(data.currentHumidity);
    $("#onvalField").text(data.onval);
    $("#runtimeField").text(data.todaysRuntime);
}

