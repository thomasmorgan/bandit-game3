$(document).ready(function() {
    $("#consent").hide();

    $("#print-consent").click(function() {
        window.print();
    });

    $("#consent").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-1");
    });

    $("#no-consent").click(function() {
        allow_exit();
        self.close();
    });

    create_participant();
});

// make a new participant
create_participant = function() {

    // check if the local store is available, and if so, use it.
    if (typeof store != "undefined") {
        url = "/participant/" +
            store.get("worker_id") + "/" +
            store.get("hit_id") + "/" +
            store.get("assignment_id") + "/" +
            store.get("mode");
    } else {
        url = "/participant/" +
            worker_id + "/" +
            hit_id + "/" +
            assignment_id + "/" +
            mode;
    }

    if (participant_id === undefined || participant_id === "undefined") {
        reqwest({
            url: url,
            method: "post",
            type: "json",
            success: function(resp) {
                console.log(resp);
                participant_id = resp.participant.id;
                $("#consent").show();
                $("#refresh-prompt").hide();
            },
            error: function (err) {
                errorResponse = JSON.parse(err.response);
                $("body").html(errorResponse.html);
            }
        });
    }
};