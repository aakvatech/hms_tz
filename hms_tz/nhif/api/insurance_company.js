frappe.ui.form.on('Healthcare Insurance Company', {
    onload: function (frm) {
        // For NHIF
        add_nhif_get_price_btn(frm);

        // For Jubilee
        add_jubilee_get_price_btn(frm);

    },
    refresh: function (frm) {
        // For NHIF
        add_nhif_get_price_btn(frm);

        // For Jubilee
        add_jubilee_get_price_btn(frm);
    },
});

var add_nhif_get_price_btn = function (frm) {
    if (!frm.doc.insurance_company_name.includes("NHIF")) { return }
    frm.add_custom_button(__('Get NHIF Price Package'), function () {
        frappe.show_alert({
            message: __("Fetching NHIF Price packages."),
            indicator: 'green'
        }, 10);

        frappe.call({
            method: 'hms_tz.nhif.api.insurance_company.enqueue_get_nhif_price_package',
            args: { company: frm.doc.company },
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    });
    frm.add_custom_button(__('Only Process NHIF Records'), function () {
        frappe.show_alert({
            message: __("Processing NHIF Price packages."),
            indicator: 'green'
        }, 10);

        frappe.call({
            method: 'hms_tz.nhif.api.insurance_company.process_nhif_records',
            args: { company: frm.doc.company },
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    });

}

var add_jubilee_get_price_btn = function (frm) {
    if (!frm.doc.insurance_company_name.includes("Jubilee")) { return }

    frm.add_custom_button(__('Get Jubilee Price Package'), function () {
        frappe.show_alert({
            message: __("Fetching Jubilee Price packages."),
            indicator: 'green'
        }, 10);

        frappe.call({
            method: 'hms_tz.jubilee.api.api.enqueue_get_jubilee_price_packages',
            args: { company: frm.doc.company },
            callback: function (data) {
                // if (data.message) {
                //     console.log(data.message)
                // }
            }
        });
    });
    frm.add_custom_button(__('Only Process Jubilee Records'), function () {
        frappe.show_alert({
            message: __("Processing Jubilee Price packages."),
            indicator: 'green'
        }, 10);

        frappe.call({
            method: 'hms_tz.jubilee.api.price_package.process_jubilee_records',
            args: { company: frm.doc.company },
            callback: function (data) {
                // if (data.message) {
                //     console.log(data.message)
                // }
            }
        });
    });

}