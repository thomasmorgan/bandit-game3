var tiles_checked = 0;
var decided = false;
var trials_per_network;
var trial_in_this_network = 0;
var round_number = 0;
var number_of_rounds;
var available_bandit_names = ["Afghanistan", "Albania", "Argentina", "Australia", "Austria", "Bangladesh", "Belgium", "Botswana", "Brasil", "Bulgaria", "Burundi", "Canada", "Chad", "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Denmark", "Ecuador", "Egypt", "England", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Germany", "Ghana", "Greece", "Greenland", "Guatemala", "Holland", "India", "Iran", "Ireland", "Italy", "Japan", "Laos", "Libya", "Madagascar", "Mali", "Mexico", "Mongolia", "Morocco", "Mozambique", "Myanmar", "Nepal", "New Zealand", "Nigeria", "Norway", "Pakistan", "Papua New Guinea", "Poland", "Portugal", "Romania", "Russia", "Scotland", "Senegal", "Sierra Leone", "South Korea", "Spain", "Sri Lanka", "Sweden", "Thailand", "The United States", "Tonga", "Tunisia", "Turkey", "Turkmenistan", "Ukraine", "Wales", "Yemen"];
var bandit_names;
var lock = false;
var p_change = 0.4;
bandit_mapping = [];

// get all the details to correctly present the trial number bar
get_num_trials = function() {
    reqwest({
        url: "/num_trials",
        method: 'get',
        success: function (resp) {
            trials_per_network = resp.n_trials;
            number_of_rounds = resp.practice_repeats + resp.experiment_repeats;
            prepare_trial_info_text();
        }
    });
};

// make a new node
create_agent = function() {
    reqwest({
        url: "/node/" + participant_id,
        method: 'post',
        type: 'json',
        success: function (resp) {
            my_node_id = resp.node.id;
            my_network_id = resp.node.network_id;
            get_genes();
        },
        error: function (err) {
            console.log(err);
            err_response = JSON.parse(err.response);
            if (err_response.hasOwnProperty('html')) {
                $('body').html(err_response.html);
            } else {
                allow_exit();
                window.location = "/debriefing/debrief-1?participant_id=" + participant_id;
            }
        }
    });
};

// what is my memory and curiosity?
get_genes = function() {
    reqwest({
        url: "/node/" + my_node_id + "/infos",
        method: 'get',
        type: 'json',
        data: {
            info_type: "Gene"
        },
        success: function (resp) {
            infos = resp.infos;
            for (i = 0; i < infos.length; i++) {
                info = infos[i];
                if (info.type == "learning_gene") {
                    learning_capacity = info.contents;
                } else {
                    memory_capacity = info.contents;
                }
            }
        }
    });
};
