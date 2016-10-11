$(document).ready(function() {
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
});