$(document).ready(function() {
    $("#print-consent").click(function() {
        window.print();
    });

    $("#consent").click(function() {
        go_to_page("instructions/instruct-1");
    });

    $("#no-consent").click(function() {
        allow_exit();
        self.close();
    });

    $("#instruct-1-button-next").click(function() {
        go_to_page("instructions/instruct-2");
    });
});

insert_num_trials = function() {
    reqwest({
        url: "/num_trials",
        method: 'get',
        success: function (resp) {
            trials_per_network = resp.n_trials;
            networks = resp.experiment_repeats;
            $("#number_of_trials").html(trials_per_network);
            $("#number_of_rounds").html(networks);
        }
    });
};