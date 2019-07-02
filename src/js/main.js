function formatTime1(value) {
    let s = String((value%60) + 100).substr(1);
    let m = String((value/60|0)%60 + 100).substr(1);
    if (value < 3600) { return m+":"+s; }

    let h = (value/3600|0);
    return h+":"+m+":"+s;
}
function formatTime2(value) {
    let ms = String(value%1 + .005).substr(1,3).replace(/\.?0+$/g, '');
    let s = String(((value|0)%60) + 100).substr(1);
    let m = String((value/60|0)%60 + 100).substr(1);
    if (value < 3600) { return m+"m "+s+ms+"s"; }

    let h = (value/3600|0);
    return h+"h "+m+"m "+s+ms+"s";
}

function updateLoop(state) {
    updateCharts(state);

    setTimeout(function() { updateLoop(state); }, 60000);
}

function updateCharts(state) {
    $.getJSON("update.json", {t : state.last_time}, function(data) {
        state.to_wait = data.to_wait;

        console.log(state.to_wait)

        state.usageHistoryChart.data.labels = data.runtime_labels;
        state.usageHistoryChart.data.datasets[0].data = data.runtimes;

        for (i = 0; i < data.times.length; i++) {
            state.weeklyChart.data.labels.push(data.times[i]);
            state.weeklyChart.data.datasets[0].data.push(data.temps[i]);
            state.weeklyChart.data.datasets[1].data.push(data.humis[i]);

            state.activityChart.data.labels.push(data.times[i]);
            state.activityChart.data.datasets[0].data.push(data.onvals[i]);
        }

        state.weeklyChart.update()
        state.usageHistoryChart.update()
        state.activityChart.update()

        state.last_time = data.last_time;
    });
}

function initCharts(initialUpdateTime) {
    var state = { last_time : initialUpdateTime,
                  to_wait : 60.0 };

    ctx = document.getElementById("weeklyChart").getContext("2d");
    state.weeklyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "Temperature",
                borderColor: "#ff0000",
                backgroundColor: "#ff0000",
                fill: false,
                yAxisID: "Temperature",
                lineTension: 0,
                pointRadius: 0,
                pointHitRadius: 4,
                data: [],
            }, {
                label: "Humidity",
                borderColor: "#0000ff",
                backgroundColor: "#0000ff",
                fill: false,
                yAxisID: "Humidity",
                lineTension: 0,
                pointRadius: 0,
                pointHitRadius: 4,
                data: [],
            }]
        },
        options: {
            responsive: true,
            interactive: true,
            aspectRatio: 3,
            scales: {
                xAxes: [{
                    type: "time",
                    time: {
                        unit: "hour",
                        displayFormats: {
                            hour: "M/D H:mm",
                        }
                    }
                }],
                yAxes: [{
                    id: "Temperature",
                    ticks: {
                        callback: function(value) {
                            return value + "\u{2109}";
                        }
                    }
                }, {
                    id: "Humidity",
                    position: "right",
                    ticks: {
                        callback: function(value) {
                            return value + "%";
                        }
                    }
                }],
            },
            tooltips: [{
                mode: "x",
                enabled: true,
                intersect: true,
            }],
            legend: {
                position: "right"
            },
        },
    });

    var ctx = document.getElementById("usageHistoryChart").getContext("2d");
    state.usageHistoryChart = new Chart(ctx, {
        type:"bar",
        data: {
            labels: [],
            datasets: [{data: []}],
        },
        options: {
            responsive: true,
            interactive: true,
            aspectRatio: 1.5,
            title: {
                display: true,
                text: "Usage History",
            },
            scales: {
                yAxes: [{
                    ticks: {
                        callback: formatTime1
                    }
                }]
            },
            tooltips: [{
                callbacks: {
                    title: function(tooltipItem, title) { return ''; },
                    footer: function(tooltipItem, footer) { return ''; },
                    label: function(tooltipItem, data) {
                        return formatTime2(tooltipItem.yLabel);
                    },
                }
            }],
            legend: {
                display: false
            },
        }
    });

    ctx = document.getElementById("activityChart").getContext("2d");
    state.activityChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: [],
            datasets: [{
                label: "On Value",
                fill: true,
                lineTension: 0,
                pointRadius: 0,
                pointHitRadius: 4,
                data: [],
            }]
        },
        options: {
            responsive: true,
            interactive: true,
            aspectRatio: 1.5,
            title: {
                display: true,
                text: "Heater Activity",
            },
            scales: {
                xAxes: [{
                    type: "time",
                    time: {
                        unit: "hour",
                        displayFormats: {
                            hour: "M/D H:mm",
                        }
                    }
                }],
                yAxes: [{
                    ticks: {
                        min: 0,
                        max: 100,
                        position: "right",
                        callback: function(value) { return value + "%"; }
                    }
                }],
            },
            tooltips: [{
            }],
            legend: {
                display: false
            },
        },
    });

    updateLoop(state);
}

