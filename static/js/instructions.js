
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