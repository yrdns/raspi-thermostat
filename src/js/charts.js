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

var WeeklyChart = null;
var UsageHistoryChart = null;
var ActivityChart = null;

function updateCharts(data) {
    UsageHistoryChart.data.labels = data.runtimeLabels;
    UsageHistoryChart.data.datasets[0].data = data.runtimes;

    for (i = 0; i < data.times.length; i++) {
        WeeklyChart.data.labels.push(data.times[i]);
        WeeklyChart.data.datasets[0].data.push(data.temps[i]);
        WeeklyChart.data.datasets[1].data.push(data.humis[i]);
    }

    for (i = 0; i < data.ontimes.length; i++) {
        ActivityChart.data.labels.push(data.ontimes[i]);
        ActivityChart.data.datasets[0].data.push(data.onvals[i]);
    }

    WeeklyChart.update()
    UsageHistoryChart.update()
    ActivityChart.update()
}

function initCharts() {
    ctx = document.getElementById("weeklyChart").getContext("2d");
    WeeklyChart = new Chart(ctx, {
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
    UsageHistoryChart = new Chart(ctx, {
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
    ActivityChart = new Chart(ctx, {
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
                            hour: "h:mm a",
                        }
                    }
                }],
                yAxes: [{
                    position: "right",
                    ticks: {
                        min: 0,
                        max: 100,
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

    updateLoop(0.0, 0.0);
}

