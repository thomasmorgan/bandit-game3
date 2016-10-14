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
strategies = {
    left: {
        name: "none", image: "none", mean_1: "none", mean_2: "none", payoff: "none"
    },
    right: {
        name: "none", image: "none", mean_1: "none", mean_2: "none", payoff: "none"
    }
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
temperature = {
    number: "none",
    name: "none",
    image: "none"
};

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
    pick_temperature();
    change_left_strategy();
    change_right_strategy();
    update_ui();
    create_event_listeners();
};

update_trial_text = function() {
    $(".round").html(round);
    $(".trial").html(trial);
};

change_left_strategy = function() {
    index = Math.floor(Math.random()*available_strategies.length);
    strategies.left.name = available_strategies[index];
    available_strategies.splice(index, 1);
    strategies.left.image = "static/images/" + strategies.left.name + ".png";
    strategies.left.mean_1 = Math.random();
    strategies.left.mean_2 = Math.random();
    strategies.left.payoff = Math.round(
        scaled_normal_pdf(temperature.number/10, strategies.left.mean_1, 0.1) +
        scaled_normal_pdf(temperature.number/10, strategies.left.mean_2, 0.2)
    );
};

change_right_strategy = function() {
    index = Math.floor(Math.random()*available_strategies.length);
    strategies.right.name = available_strategies[index];
    available_strategies.splice(index, 1);
    strategies.right.image = "static/images/" + strategies.right.name + ".png";
    strategies.right.mean_1 = Math.random();
    strategies.right.mean_2 = Math.random();
    strategies.right.payoff = Math.round(
        scaled_normal_pdf(temperature.number/10, strategies.right.mean_1, 0.1) +
        scaled_normal_pdf(temperature.number/10, strategies.right.mean_2, 0.2)
    );
};

update_ui = function() {
    $(".left-td").html("<img class='left-img' src=" + strategies.left.image + "></img>");
    $(".right-td").html("<img class='right-img' src=" + strategies.right.image + "></img>");
    $(".thermometer-div").html("<img src=" + temperature.image + "></img>");
    $(".temp-description").html(temperature.name);
};

pick_temperature = function() {
    num = Math.floor(Math.random()*11);
    temperature.number = num;
    temperature.name = temperatures[num];
    temperature.image = "static/images/" + temperature.number + ".png";
};

normal_pdf = function(x, u, v) {
    exponent = -(Math.pow((x-u),2)/(2*v));
    denominator = Math.pow((2*v*Math.PI), 0.5);
    return (1/denominator)*Math.exp(exponent);
};

scaled_normal_pdf = function(x, u, v) {
    density = normal_pdf(x, u, v);
    max_density = normal_pdf(u, u, v);
    return (density/max_density)*10;
};

create_event_listeners = function() {
    $(".left-img").on('click', function() {
        remove_event_listeners();
        show_payoff("left");
    });
    $(".right-img").on('click', function() {
        remove_event_listeners();
        show_payoff("right");
    });
    $(".check-button").on('click', function() {
        remove_event_listeners();
        show_payoff("both");
    });
};

remove_event_listeners = function () {
    $(".left-img").off('click');
    $(".right-img").off('click');
    $(".check-button").off('click');
};

show_payoff = function(which) {
    if (which == "left" || which == "both") {
        $(".left-td").html(strategies.left.payoff);
    }
    if (which == "right" || which == "both") {
        $(".right-td").html(strategies.right.payoff);
    }
};
