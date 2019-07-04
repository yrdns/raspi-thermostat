$(document).ready(function () {
    initCharts();

    $("#tempInput").keyup(function (event) {
        if (event.which == 13) { // Enter key
            event.preventDefault();
            setTemp();
        }
    });

    var pidcallback = function (event) {
        if (event.which == 13) { // Enter Key
            event.preventDefault();
            setTemp();
        }
    };
    $("#KpInput").keyup(pidcallback);
    $("#KiInput").keyup(pidcallback);
    $("#KdInput").keyup(pidcallback);
});

