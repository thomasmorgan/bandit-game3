$(document).ready(function() {
    $("#print-consent").click(function() {
        window.print();
    });

    $("#consent").click(function() {
        allow_exit();
        window.location.href = '/instructions/instruct-1?hit_id={{ hit_id }}&assignment_id={{ assignment_id }}&worker_id={{ worker_id }}&mode={{ mode }}';
    });

    $("#no-consent").click(function() {
        allow_exit();
        self.close();
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