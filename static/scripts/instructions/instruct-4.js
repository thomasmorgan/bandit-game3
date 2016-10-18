$(document).ready(function() {
    $("#begin-button").click(function() {
        allow_exit();
        go_to_page("experiment");
    });
    $("#prev-button").click(function() {
        allow_exit();
        go_to_page("instructions/instruct-3");
    });
});