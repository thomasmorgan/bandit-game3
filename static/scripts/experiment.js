$(document).ready(function() {
    create_agent();
});


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
        }
    });
};
