$(document).ready(function() {
    $("#next-button").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-4");
    });
    $("#prev-button").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-3");
    });
});