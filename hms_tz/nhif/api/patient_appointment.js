frappe.ui.form.on('Patient Appointment', {
    setup: function (frm) {
        set_filters(frm);
    },
    onload: function (frm) {
        frm.trigger("mandatory_fields");
        set_filters(frm);
    },
    billing_item: function (frm) {
        frm.trigger("get_mop_amount");
    },
    refresh: function (frm) {
        set_filters(frm);
        frm.trigger("update_primary_action");
        frm.trigger("toggle_reqd_referral_no");
        add_btns(frm);
        frm.trigger("mandatory_fields");
        set_auth_number_reqd(frm);
    },
    referring_practitioner: function (frm) {
        frm.set_value("healthcare_referrer", frm.doc.referring_practitioner);
    },
    source: function (frm) {
        frm.trigger("toggle_reqd_referral_no");
        frm.set_value("referring_practitioner", "");
        frm.set_value("healthcare_referrer_type", "");
        frm.set_value("healthcare_referrer", "");
    },
    insurance_subscription: function (frm) {
        frm.trigger("mandatory_fields");
        frm.trigger("update_primary_action");
        if (frm.doc.insurance_subscription) {
            frm.set_value("mode_of_payment", "");
            frm.trigger('get_insurance_amount');
        } else {
            frm.set_value("insurance_subscription", "");
            frm.set_value("insurance_company", "");
            frm.set_value("coverage_plan_name", "");
            frm.set_value("coverage_plan_card_number", "");
            frm.set_value("insurance_company_name", "");
            frm.trigger('get_mop_amount');
        }
    },
    mode_of_payment: function (frm) {
        frm.trigger("mandatory_fields");
        frm.trigger("update_primary_action");
        if (frm.doc.mode_of_payment) {
            frm.set_value("insurance_subscription", "");
            frm.set_value("insurance_company", "");
            frm.set_value("coverage_plan_name", "");
            frm.set_value("coverage_plan_card_number", "");
            frm.set_value("insurance_company_name", "");
            frm.trigger('get_mop_amount');
        }
    },
    insurance_company: function (frm) {
        frm.set_value("authorization_number", "");
        set_auth_number_reqd(frm);
    },
    practitioner: function (frm) {
        frm.trigger("get_consulting_charge_item");
        frm.trigger('get_mop_amount');
    },
    mandatory_fields: function (frm) {
        frm.trigger("get_consulting_charge_item");
        frm.trigger("toggle_reqd_referral_no");
        if (frm.doc.insurance_subscription) {
            frm.toggle_reqd("mode_of_payment", false);
        }
        else {
            frm.toggle_reqd("mode_of_payment", true);
        }
        if (frm.doc.mode_of_payment) {
            frm.toggle_reqd("insurance_subscription", false);
        }
        else {
            frm.toggle_reqd("insurance_subscription", true);
        }
        if (frm.doc.invoiced && frm.doc.mode_of_payment) {
            frm.set_value(["insurance_subscription", "insurance_company"], "");
            frm.toggle_display('insurance_section', false);
            frm.toggle_enable(['referral_no', 'source', 'mode_of_payment', 'paid_amount'], false);
        }
        if (frm.doc.insurance_claim) {
            frm.set_value("mode_of_payment", "");
            frm.toggle_display('section_break_16', false);
            frm.toggle_enable(['referral_no', 'source', 'insurance_subscription'], false);
        }
    },
    toggle_reqd_referral_no: function (frm) {
        frm.toggle_display(['healthcare_referrer'], false);
        frm.toggle_reqd(['healthcare_referrer'], false);
        if (frm.doc.source == "External Referral") {
            if (frm.doc.insurance_subscription) {
                frm.toggle_reqd("referral_no", true);
            } else {
                frm.toggle_reqd("referral_no", false);
            }
            frm.toggle_enable(['referral_no'], true);
            frm.toggle_display(['healthcare_referrer'], true);
            frm.toggle_reqd(['healthcare_referrer'], true);
            frm.set_value("healthcare_referrer_type", "Healthcare External Referrer");
            frm.toggle_reqd("referring_practitioner", false);
            frm.toggle_enable("referring_practitioner", false);
        } else if (frm.doc.source == "Referral") {
            frm.set_value("healthcare_referrer_type", "Healthcare Practitioner");
            frm.toggle_reqd("referring_practitioner", true);
            frm.toggle_enable("referring_practitioner", true);
        } else {
            frm.toggle_reqd("referral_no", false);
            frm.toggle_enable(['referral_no'], false);
        }
    },
    get_insurance_amount: function (frm) {
        if (!frm.doc.insurance_subscription || !frm.doc.billing_item) {
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.get_insurance_amount',
            args: {
                'insurance_subscription': frm.doc.insurance_subscription,
                'billing_item': frm.doc.billing_item,
                'company': frm.doc.company,
                'insurance_company': frm.doc.insurance_company,
            },
            callback: function (data) {
                if (data.message) {
                    frm.set_value("paid_amount", data.message);
                }
            }
        });
    },
    get_mop_amount: function (frm) {
        if (!frm.doc.mode_of_payment || !frm.doc.billing_item) {
            return;
        }
        if (frm.doc.billing_item && !frm.doc.insurance_subscription) {
            frappe.call({
                method: 'hms_tz.nhif.api.patient_appointment.get_mop_amount',
                args: {
                    'billing_item': frm.doc.billing_item,
                    'mop': frm.doc.mode_of_payment,
                    'company': frm.doc.company,
                    'patient': frm.doc.patient,
                },
                callback: function (data) {
                    if (data.message) {
                        frm.set_value("paid_amount", data.message);
                    }
                }
            });
        }
    },
    get_consulting_charge_item: function (frm) {
        if (!frm.doc.practitioner || !frm.doc.appointment_type) {
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.get_consulting_charge_item',
            args: {
                'appointment_type': frm.doc.appointment_type,
                'practitioner': frm.doc.practitioner,
            },
            callback: function (data) {
                if (data.message) {
                    frm.set_value("billing_item", data.message);
                }
            }
        });
    },
    patient: function (frm) {
        if (frm.doc.patient) {
            setTimeout(() => {
                frm.toggle_display('mode_of_payment', true);
                frm.toggle_display('paid_amount', true);
            }, 100);
        }
    },
    get_authorization_number: function (frm) {
        frm.trigger("get_authorization_num");
    },
    get_authorization_num: function (frm) {
        if (frm.doc.insurance_company != "NHIF") {
            frappe.show_alert({
                message: __("This feature is not applicable for non NHIF insurance"),
                indicator: 'orange'
            }, 5);
            return;
        }
        if (!frm.doc.insurance_subscription) {
            frappe.msgprint("Select Insurance Subscription to get authorization number");
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.get_authorization_num',
            args: {
                'insurance_subscription': frm.doc.insurance_subscription,
                'company': frm.doc.company,
                'appointment_type': frm.doc.appointment_type,
                'referral_no': frm.doc.referral_no
            },
            async: true,
            callback: function (data) {
                if (data.message) {
                    const card = data.message;
                    if (card.AuthorizationStatus == 'ACCEPTED') {
                        frm.set_value("authorization_number", card.AuthorizationNo);
                        frm.save();
                        frappe.show_alert({
                            message: __("Authorization Number is updated"),
                            indicator: 'green'
                        }, 5);
                    } else {
                        frm.set_value("insurance_subscription", "");
                        frm.set_value("authorization_number", "");
                    }
                }
                else {
                    frm.set_value("insurance_subscription", "");
                    frm.set_value("authorization_number", "");
                }
            }
        });
    },
    invoiced: function (frm) {
        frm.trigger("mandatory_fields");
    },
    authorization_number: function (frm) {
        frm.trigger("insurance_subscription");
    },
    insurance_claim: function (frm) {
        frm.trigger("mandatory_fields");
    },
    update_primary_action: function (frm) {
        if (frm.is_new()) {
            if (!frm.doc.mode_of_payment && !frm.doc.insurance_subscription) {
                frm.page.set_primary_action(__('Pending'), () => {
                    frappe.show_alert({
                        message: __("Please select Insurance Subscription or Mode of Payment"),
                        indicator: 'red'
                    }, 15);
                });
            }
            else {
                frm.page.set_primary_action(__('Check Availability'), function () {
                    if (!frm.doc.patient) {
                        frappe.msgprint({
                            title: __('Not Allowed'),
                            message: __('Please select Patient first'),
                            indicator: 'red'
                        });
                    } else {
                        frappe.call({
                            method: 'hms_tz.hms_tz.doctype.patient_appointment.patient_appointment.check_payment_fields_reqd',
                            args: { 'patient': frm.doc.patient },
                            callback: function (data) {
                                if (data.message == true) {
                                    if (frm.doc.mode_of_payment && frm.doc.paid_amount) {
                                        check_and_set_availability(frm);
                                    }
                                    if (!frm.doc.mode_of_payment) {
                                        frappe.msgprint({
                                            title: __('Not Allowed'),
                                            message: __('Please select a Mode of Payment first'),
                                            indicator: 'red'
                                        });
                                    }
                                    if (!frm.doc.paid_amount) {
                                        frappe.msgprint({
                                            title: __('Not Allowed'),
                                            message: __('Please set the Paid Amount first'),
                                            indicator: 'red'
                                        });
                                    }
                                } else {
                                    check_and_set_availability(frm);
                                }
                            }
                        });
                    }
                });
            }
        } else {
            frm.page.set_primary_action(__('Save'), () => frm.save());
        }
    },
    send_vfd: function (frm) {
        if (!frm.doc.ref_sales_invoice) return;
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.send_vfd',
            args: {
                invoice_name: frm.doc.ref_sales_invoice,
            },
            callback: function (data) {
                if (data.message) {
                    if (data.message.enqueue) {
                        load_print_page(frm.doc.ref_sales_invoice, data.message.pos_rofile);
                    }
                }
            }
        });
    },
});


const set_filters = function (frm) {
    frm.set_query('insurance_subscription', function () {
        return {
            filters: {
                'is_active': 1,
                'docstatus': 1,
                'patient': frm.doc.patient
            }
        };
    });
};

const load_print_page = function (invoice_name, pos_profile) {
    const print_format = pos_profile.print_format || "AV Tax Invoice";
    const letter_head = pos_profile.letter_head || 0;
    const url =
        frappe.urllib.get_base_url() +
        "/printview?doctype=Sales%20Invoice&name=" +
        invoice_name +
        "&trigger_print=0" +
        "&format=" +
        print_format +
        "&no_letterhead=" +
        letter_head;
    const printWindow = window.open(url, "Print");
    printWindow.addEventListener(
        "load",
        function () {
            // printWindow.print();
        },
        true
    );
};

const get_previous_appointment = (frm, filters) => {
    let appointment;
    if (!frm.doc.patient) return;
    frappe.call({
        method: 'hms_tz.nhif.api.patient_appointment.get_previous_appointment',
        args: {
            'patient': frm.doc.patient,
            'filters': filters
        },
        async: false,
        callback: function (data) {
            if (data.message) {
                appointment = data.message;
            }
        }
    });
    return appointment;
};


const get_value = (doctype, name, field) => {
    let value;
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            'doctype': doctype,
            'filters': { 'name': name },
            'fieldname': field
        },
        async: false,
        callback: function (r) {
            if (!r.exc) {
                value = r.message[field];
            }
        }
    });
    return value;
};

const add_btns = (frm) => {
    if (!frm.doc.patient || frm.is_new() || frm.doc.invoiced || frm.doc.status == "Cancelled") return;
    var vitals_btn_required = false;
    const valid_days = get_value("Healthcare Settings", "Healthcare Settings", "valid_days");
    const appointment = get_previous_appointment(frm, { name: ["!=", frm.doc.name], insurance_subscription: frm.doc.insurance_subscription, department: frm.doc.department, status: "Closed" });
    if (typeof appointment != "undefined") {
        const last_appointment_date = appointment.appointment_date;
        const diff = frappe.datetime.get_day_diff(frm.doc.appointment_date, last_appointment_date);
        if (diff <= valid_days) {
            vitals_btn_required = true;
            if (!frm.doc.invoiced) {
                frm.set_value("invoiced", 1);
                frappe.show_alert(__({ message: "Previous appointment found valid for free follow-up.<br>Skipping invoice for this appointment!", indicator: "green" }));
            }
        }
    }
    if (!frm.doc.mode_of_payment || frm.doc.insurance_subscription) return;
    if (vitals_btn_required || frm.doc.follow_up) {
        add_vital_btn(frm);
    } else {
        add_invoice_btn(frm);
    }
};

const add_invoice_btn = (frm) => {
    frm.add_custom_button(__('Create Sales Invoice'), function () {
        frm.save();
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.invoice_appointment',
            args: {
                'name': frm.doc.name
            },
            callback: function (data) {
                frm.reload_doc();
            }
        });
    });
};

const add_vital_btn = frm => {
    frm.add_custom_button(__('Create Vitals'), function () {
        if (frm.is_dirty()) {
            frm.save();
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.create_vital',
            args: {
                'appointment': frm.doc.name
            },
            callback: function (data) {
                frm.reload_doc();
            }
        });
    });
};

const set_auth_number_reqd = frm => {
    if (frm.doc.insurance_subscription) {
        // Removed reqd for time being 2021-03-21 10:36:11
        frm.toggle_reqd("authorization_number", false);
    }
    else {
        frm.toggle_reqd("authorization_number", false);
    }
}