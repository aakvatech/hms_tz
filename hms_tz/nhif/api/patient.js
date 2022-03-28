frappe.ui.form.on('Patient', {
    setup: function (frm) {
    },
    onload: function (frm) {
        frm.trigger('add_get_info_btn');
        if (frm.is_new()) {
            frm.set_value("customer_group", "Patient")
        }
        frm.trigger('update_cash_limit');
    },
    refresh: function (frm) {
        frm.trigger('add_get_info_btn');
        frm.trigger('update_cash_limit');
    },
    add_get_info_btn: function (frm) {
        frm.add_custom_button(__('Get Patient Info'), function () {
            frm.trigger('get_patient_info');
        });
    },
    card_no: function (frm) {
        frm.fields_dict.card_no.$input.focusout(function() {
            frm.trigger('get_patient_info');
            frm.set_df_property('card_no', 'read_only', 1);
        });
    },
    mobile: function (frm) {
        frappe.call({
            method: 'hms_tz.nhif.api.patient.validate_mobile_number',
            args: {
                'doc_name': frm.doc.name,
                'mobile': frm.doc.mobile,
            }
        });
    },
    get_patient_info: function (frm) {
        if (!frm.doc.card_no) return;
        let exists = false;
        frappe.call({
            method: 'hms_tz.nhif.api.patient.check_card_number',
            async: false,
            args: {
                'card_no': frm.doc.card_no,
                'is_new': frm.is_new(),
                'patient': frm.doc.name
            },
            callback: function (data) {
                if (data.message && data.message != "false") {
                    frappe.msgprint(`Card number used with patient ${data.message}`);
                    frappe.set_route('Form', 'Patient', data.message);
                    exists = true;
                    return;
                }
            }
        });
        if (exists) return;
        frappe.call({
            method: 'hms_tz.nhif.api.patient.get_patient_info',
            args: {
                'card_no': frm.doc.card_no,
            },
            callback: function (data) {
                if (data.message) {
                    const card = data.message;
                    if (!frm.is_new()) {
                        const d = new frappe.ui.Dialog({
                            title: "Patient's information",
                            primary_action_label: 'Submit',
                            primary_action(values) {
                                update_patient_info(frm, card);
                                d.hide();
                            }
                        });
                        $(`<div class="modal-body ui-front">
                        <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Field Name</th>
                                <th>Current Values</th>
                                <th>New Values</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>First Name</td>
                                <td>${frm.doc.first_name}</td>
                                <td>${card.FirstName}</td>
                            </tr>
                            <tr>
                                <td>Last Name</td>
                                <td>${frm.doc.middle_name}</td>
                                <td>${card.MiddleName}</td>
                            </tr>
                            <tr>
                                <td>Last Name</td>
                                <td>${frm.doc.last_name}</td>
                                <td>${card.LastName}</td>
                            </tr>
                            <tr>
                                <td>Full Name</td>
                                <td>${frm.doc.patient_name}</td>
                                <td>${card.FullName}</td>
                            </tr>
                            <tr> 
                                <td>Gender</td>
                                <td>${frm.doc.sex}</td>
                                <td>${card.Gender}</td>
                            </tr>
                             <tr>
                                <td>Date of birth</td>
                                <td>${frm.doc.dob}</td>
                                <td>${card.DateOfBirth.slice(0, 10)}</td>
                            </tr>
                            <tr>
                                <td>Product Code</td>
                                <td>${frm.doc.product_code}</td>
                                <td>${card.ProductCode}</td>
                            </tr>
                            <tr>
                                <td>Membership No</td>
                                <td>${frm.doc.membership_no}</td>
                                <td>${card.MembershipNo}</td>
                            </tr>
                        </tbody>
                        </table>
                    </div>`).appendTo(d.body);
                        d.show();
                    }
                    else {
                        update_patient_info(frm, card);
                    }
                }
            }
        });
    },

    update_cash_limit: function(frm) {
        if (frappe.user.has_role('Healthcare Administrator')) {
            frm.add_custom_button(__('Update Cash Limit'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Change Cash Limit',
                    fields: [
                        {
                            fieldname: 'current_cash_limit',
                            fieldtype: 'Currency',
                            label: __('Current Cash Limit'),
                            default: frm.doc.cash_limit,
                            reqd: true
                        },
                        {
                            fieldname: 'column_break_1', 
                            fieldtype: 'Column Break'
                        },
                        {
                            fieldname: 'new_cash_limit',
                            fieldtype: 'Currency',
                            label: 'New Cash Limit',
                            reqd: true
                        }
                    ],
                });
                d.set_primary_action(__('Submit'), function() {
                    if (d.get_value('new_cash_limit') == 0) {
                        frappe.msgprint({
                            title: 'Notification',
                            indicator: 'red',
                            message: __('new cash limit cannot be zero')
                        });
                    } else {
                        frappe.call('hms_tz.nhif.api.patient.enqueue_update_cash_limit', {
                            old_cash_limit: d.get_value('current_cash_limit'),
                            new_cash_limit: d.get_value('new_cash_limit')
                        }).then(r => {
                            // frm.refresh();
                            frappe.show_alert(__('Processing updating patients'))
                        })
                        d.hide();
                    }

                });
                d.show();
            });
        }
    }
});

function update_patient_info(frm, card) {
    frm.set_value("first_name", card.FirstName);
    frm.set_value("middle_name", card.MiddleName);
    frm.set_value("last_name", card.LastName);
    frm.set_value("patient_name", card.FullName);
    frm.set_value("sex", card.Gender);
    frm.set_value("dob", card.DateOfBirth);
    frm.set_value("product_code", card.ProductCode);
    frm.set_value("nhif_employername", card.EmployerName);
    frm.set_value("membership_no", card.MembershipNo);
    frm.save();
    frappe.show_alert({
        message: __("Patient's information is updated"),
        indicator: 'green'
    }, 5);
}
