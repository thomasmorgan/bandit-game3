available_strategies = [
    "deer",
    "roots",
    "berries",
    "fish",
    "mushrooms",
    "eggs",
    "fruit",
    "boar",
    "birds",
    "eels",
    "clams",
    "grubs",
    "nuts",
    "seeds",
    "greens",
    "rabbits",
    "rats",
    "insects",
    "shrimp",
    "lizards"
];
var strategies = {
    left: "none", left_image: "none", left_mean_1: "none", left_mean_2: "none",
    right: "none", right_image: "none", right_mean_1: "none", right_mean_2: "none",
};
temperatures = [
    "extremely cold",
    "very cold",
    "cold",
    "chilly",
    "cool",
    "mild",
    "warm",
    "very warm",
    "hot",
    "very hot",
    "extremely hot"
];

$(document).ready(function() {
    get_experiment_parameters();
    create_agent();
});

get_experiment_parameters = function () {
    reqwest({
        url: "/experiment/trials_per_round",
        method: 'get',
        type: 'json',
        success: function (resp) {
            trials_per_round = resp.trials_per_round;
            $(".trials_per_round").html(trials_per_round);
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
            start_first_round();
        }
    });
};

start_first_round = function() {
    round = 1;
    trial = 1;
    update_trial_text();
    choose_two_strategies();
    pick_temperature();
    update_ui();
};

update_trial_text = function() {
    $(".round").html(round);
    $(".trial").html(trial);
};

choose_two_strategies = function() {
    index = Math.floor(Math.random()*available_strategies.length);
    strategies.left = available_strategies[index];
    available_strategies.splice(index, 1);
    strategies.left_image = "static/images/" + strategies.left + ".png";
    strategies.left_mean_1 = Math.random();
    strategies.left_mean_2 = Math.random();

    index = Math.floor(Math.random()*available_strategies.length);
    strategies.right = available_strategies[index];
    available_strategies.splice(index, 1);
    strategies.right_image = "static/images/" + strategies.right + ".png";
    strategies.right_mean_1 = Math.random();
    strategies.right_mean_2 = Math.random();
};

update_ui = function() {
    $(".left-td").html("<img src=" + strategies.left_image + "></img>");
    $(".right-td").html("<img src=" + strategies.right_image + "></img>");
    $(".thermometer-div").html("<img src=" + temperature.image + "></img>");
    $(".temp-description").html(temperature.name);
};

pick_temperature = function() {
    num = Math.floor(Math.random()*11);
    temperature = {
        number: num,
        name: temperatures[num],
        image: "static/images/" + num + ".png"
    };
};
