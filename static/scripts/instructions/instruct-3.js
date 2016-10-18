$(document).ready(function() {
    $("#next-button").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-4");
    });
    $("#prev-button").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-2");
    });
    reqwest({
        url: "/experiment/trials_per_round",
        method: 'get',
        type: 'json',
        success: function (resp) {
            trials_per_round = resp.trials_per_round;
            $(".trials").html(trials_per_round);
        },
        error: function (err) {
            console.log(err);
        }
    });
    reqwest({
        url: "/experiment/rounds",
        method: 'get',
        type: 'json',
        success: function (resp) {
            rounds = resp.rounds;
            $(".rounds").html(rounds);
        },
        error: function (err) {
            console.log(err);
        }
    });
});