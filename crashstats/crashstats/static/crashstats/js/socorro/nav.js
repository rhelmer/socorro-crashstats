$(document).ready(function () {
    var url_base = $("#url_base").val(),
        url_site = $("#url_site").val(),
        product,
        product_version,
        report;

    $("#q").focus(function () {
        $(this).attr('value', '');
    });

    // Used to handle the selection of specific product.
    if ($("#products_select")) {
        $("#products_select").change(function () {
            product = $("#products_select").val();
            window.location = url_site + 'products/' + product;
        });
    }

    // Used to handle the selection of a specific version of a specific product.
    if ($("#product_version_select")) {
        $("#product_version_select").change(function () {
            product_version = $("#product_version_select").val();
            report = $("#report_select").val();
            if (product_version == 'Current Versions') {
                window.location = url_base + '/' + report;
            } else {
                window.location = url_base + '/versions/' + product_version + '/' + report;
            }
        });
    }

    // Used to handle the selection of a specific report.
    if ($("#report_select")) {
        $("#report_select").change(function () {
            report = $("#report_select").val();

            // Handle top crasher selection. If no version was selected in the version drop-down
            // select the top most version and append to the URL.
            var report_url = url_base + '/';
            if(report.indexOf('topcrasher') !== -1) {
                var selectedVersion = $("#product_version_select").val();

                if(selectedVersion === "Current Versions") {
                    selectedVersion = $("#product_version_select")
                                      .find("option:eq(1)").val();
                    report_url += report + '/' + selectedVersion;
                } else {
                    report_url += report
                }
            } else if (report !== 'More Reports') {
                report_url += report
            }
            window.location = report_url
        });
    }
});
