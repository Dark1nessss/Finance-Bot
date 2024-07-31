$(document).ready(function() {
    $(".stock-row").click(function() {
        var symbol = $(this).data("symbol");
        $.get("/stock_details/" + symbol, function(data) {
            $("#modal-body").html(data);
            $("#stockModal").css("display", "block");

            // Fetch historical data and render chart
            var historicalData = JSON.parse($("#historical-data").text());
            var labels = historicalData.map(item => item.date);
            var prices = historicalData.map(item => item.close);

            var ctx = document.getElementById('stockChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Stock Price',
                        data: prices,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day'
                            }
                        },
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });
        });
    });

    $(".close").click(function() {
        $("#stockModal").css("display", "none");
    });

    $(window).click(function(event) {
        if (event.target == document.getElementById("stockModal")) {
            $("#stockModal").css("display", "none");
        }
    });
});
