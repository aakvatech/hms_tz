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
        // check if appointment is cancelled and hide fields for authorization
        // this will stop getting authorization number for cancelled appointment and
        // vital sign will not be created
        frm.trigger("check_for_cancelled_appointment");
        if (frm.doc.healthcare_package_order) {
            frm.disable_form();
        }
        set_filters(frm);
        frm.trigger("update_primary_action");
        frm.trigger("toggle_reqd_referral_no");
        add_btns(frm);
        frm.trigger("mandatory_fields");
        set_auth_number_reqd(frm);

        if (frm.doc.status == 'Open' || (frm.doc.status == 'Scheduled' && !frm.doc.__islocal)) {
            frm.add_custom_button(__('Reschedule'), function () {
                check_and_set_availability(frm);
            });
        }
    },
    referring_practitioner: function (frm) {
        frm.set_value("healthcare_referrer", frm.doc.referring_practitioner);
    },
    appointment_type: function (frm) {
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
            validate_insurance_company(frm);
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
        frm.toggle_display(['referral_no'], false);
        frm.toggle_display(['remarks'], false);

        if (frm.doc.appointment_type == "NHIF External Referral") {
            if (frm.doc.insurance_subscription) {
                frm.toggle_display(['referral_no'], true);
                frm.toggle_reqd("referral_no", true);
                frm.toggle_display(['remarks'], true);
                frm.toggle_reqd("remarks", true);

            } else {
                frm.toggle_reqd("referral_no", false);
                frm.toggle_display(['referral_no'], false);
                frm.toggle_display(['remarks'], true);
                frm.toggle_reqd("remarks", true);

            }
            frm.toggle_enable(['referral_no'], true);
            frm.toggle_display(['healthcare_referrer'], true);
            frm.toggle_reqd(['healthcare_referrer'], true);
            frm.set_value("healthcare_referrer_type", "Healthcare External Referrer");
            frm.toggle_reqd("referring_practitioner", false);
            frm.toggle_enable("referring_practitioner", false);
        }

        if (frm.doc.appointment_type == "Emergency") {
            if (frm.doc.insurance_subscription) {
                frm.toggle_display(['remarks'], true);
                frm.toggle_reqd("remarks", true);

            } else {
                frm.toggle_reqd("remarks", false);
                frm.toggle_display(['remarks'], false);

            }
            frm.toggle_enable(['remarks'], true);
        }

        if (frm.doc.appointment_type == "Follow up Visit") {
            if (frm.doc.insurance_subscription) {
                frm.toggle_display(['referral_no'], true);
                frm.toggle_reqd("referral_no", true);

            } else {
                frm.toggle_reqd("referral_no", false);
                frm.toggle_display(['referral_no'], false);

            }
            frm.toggle_enable(['referral_no'], true);
        }

        if (frm.doc.source == "Referral") {
            frm.set_value("healthcare_referrer_type", "Healthcare Practitioner");
            frm.toggle_reqd("referring_practitioner", true);
            frm.toggle_enable("referring_practitioner", true);
        }
    },
    get_insurance_amount: function (frm) {
        if (!frm.doc.insurance_subscription || !frm.doc.billing_item || frm.doc.healthcare_package_order) {
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.get_insurance_amount',
            args: {
                'insurance_subscription': frm.doc.insurance_subscription,
                'billing_item': frm.doc.billing_item,
                'company': frm.doc.company,
                'insurance_company': frm.doc.insurance_company,
                "has_no_consultation_charges": frm.doc.has_no_consultation_charges
            },
            callback: function (data) {
                if (data.message) {
                    frm.set_value("paid_amount", data.message[0]);
                }
            }
        });
    },
    get_mop_amount: function (frm) {
        if (!frm.doc.mode_of_payment || !frm.doc.billing_item || frm.doc.healthcare_package_order) {
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
        if (!frm.doc.practitioner || !frm.doc.appointment_type || frm.doc.healthcare_package_order) {
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
            frappe.call("hms_tz.nhif.api.patient.validate_missing_patient_dob", {
                patient: frm.doc.patient
            }).then(r => {
                if (!r.message) {
                    let d = frm.doc.patient;
                    frm.set_value("patient", "")
                    frappe.set_route("Form", "Patient", d);
                    frappe.msgprint("<h4 style='background-color:LightCoral'>Please update date of birth for this patient</h4>");
                }
            }),
                setTimeout(() => {
                    frm.toggle_display('mode_of_payment', true);
                    frm.toggle_display('paid_amount', true);
                }, 100);
            frm.set_value("insurance_subscription", "");
            if (!frm.doc.ref_vital_signs) {
                frm.set_df_property("follow_up", "read_only", 0);
            } else {
                frm.set_df_property("follow_up", "read_only", 1);
            }
        }
    },
    ref_vital_signs: function (frm) {
        if (frm.doc.ref_vital_signs) {
            frm.set_df_property("follow_up", "read_only", 1);
        } else {
            frm.set_df_property("follow_up", "read_only", 0);
        }
    },
    get_authorization_number: function (frm) {
        if (frm.doc.status == "Cancelled") {
            frappe.msgprint("Appointment is already cancelled")
            return
        }

        if (frm.doc.insurance_company.includes("NHIF")) {
            // get auth number for NHIF Patients
            frm.trigger("get_nhif_authorization_num");
        }
        if (frm.doc.insurance_company.includes("Jubilee")) {
            // get auth number for Jubilee Patients
            frm.trigger("get_jubilee_authorization_number");
        }
    },
    get_nhif_authorization_num: function (frm) {
        if (!frm.doc.insurance_subscription) {
            frappe.msgprint("Select Insurance Subscription to get authorization number");
            return;
        }
        if (frm.is_dirty()) {
            frm.save();
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.get_authorization_num',
            args: {
                'insurance_subscription': frm.doc.insurance_subscription,
                'company': frm.doc.company,
                'appointment_type': frm.doc.appointment_type,
                'card_no': frm.doc.coverage_plan_card_number,
                'referral_no': frm.doc.referral_no,
                'remarks': frm.doc.remarks
            },
            async: true,
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
            callback: function (data) {
                if (data.message) {
                    const card = data.message;
                    if (card.AuthorizationStatus == 'ACCEPTED') {
                        frm.set_value("coverage_plan_name", card.CoveragePlanName);
                        frm.set_value("authorization_number", card.AuthorizationNo);
                        frm.set_value("nhif_employer_name", card.EmployerName);
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
    get_jubilee_authorization_number: (frm) => {
        if (!frm.doc.insurance_subscription) {
            frappe.msgprint("Select Insurance Subscription to get authorization number");
            return;
        }
        if (frm.is_dirty()) {
            frm.save();
        }
        frappe.call({
            method: 'hms_tz.jubilee.api.api.get_authorization_number',
            args: {
                'company': frm.doc.company,
                'card_no': frm.doc.coverage_plan_card_number,
                "appointment_no": frm.doc.name,
                'insurance_subscription': frm.doc.insurance_subscription,
                "insurance_provider": "Jubilee"
            },
            async: true,
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
            callback: function (data) {
                console.log(data);
                if (data.message) {
                    const card = data.message;
                    if (card.Status == 'OK') {
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
        if (frm.doc.healthcare_package_order) {
            return;
        }
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
        if (!frm.doc.ref_sales_invoice || frm.doc.healthcare_package_order) return;
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
    check_for_cancelled_appointment: (frm) => {
        if (frm.doc.status == "Cancelled" && !frm.doc.authorization_number) {
            frm.set_df_property("get_authorization_number", "hidden", 1)
            frm.set_df_property("authorization_number", "hidden", 1)
        } else {
            frm.set_df_property("get_authorization_number", "hidden", 0)
            frm.set_df_property("authorization_number", "hidden", 0)
        }
    }
});


const check_and_set_availability = (frm) => {
    let selected_slot = null;
    let service_unit = null;
    let duration = null;
    let practitioner_availability = null

    show_availability();

    function show_empty_state(practitioner, appointment_date) {
        frappe.msgprint({
            title: __('Not Available'),
            message: __('Healthcare Practitioner {0} not available on {1}', [practitioner.bold(), appointment_date.bold()]),
            indicator: 'red'
        });
    }

    function show_availability() {
        let selected_practitioner = '';
        let d = new frappe.ui.Dialog({
            title: __('Available slots'),
            fields: [
                {
                    fieldname: "practitioner",
                    label: "Healthcare Practitioner",
                    fieldtype: 'Link',
                    options: 'Healthcare Practitioner',
                    reqd: 1,
                    get_query: () => {
                        return {
                            filters: {
                                "status": "Active",
                                "hms_tz_company": frm.doc.company

                            }
                        };
                    }
                },
                { fieldtype: 'Column Break' },
                {
                    fieldname: "appointment_date",
                    label: "Date",
                    fieldtype: "Date",
                    reqd: 1,
                },
                { fieldtype: "Section Break" },
                { fieldtype: "HTML", fieldname: "available_slots" }

            ],
            primary_action_label: __("Book"),
            primary_action: function () {
                frm.set_value('appointment_time', selected_slot);
                if (!frm.doc.duration) {
                    frm.set_value('duration', duration);
                }
                frm.set_value('practitioner', d.get_value('practitioner'));
                frm.set_value('practitioner_availability', practitioner_availability || '');
                frm.set_value('appointment_date', d.get_value('appointment_date'));
                if (service_unit) {
                    frm.set_value('service_unit', service_unit);
                }
                if (!frm.doc.department) {
                    frappe.db.get_value("Healthcare Practitioner", d.get_value("practitioner"), "department")
                        .then(r => {
                            if (r && r.department) {
                                frm.set_value('department', r.department);
                            }
                        });
                }
                d.hide();
                frm.enable_save();
                frm.save();
                d.get_primary_btn().attr('disabled', true);
                if (frm.doc.patient_referral) {
                    frappe.db.set_value('Patient Referral', frm.doc.patient_referral, {
                        status: 'Completed',
                    }).then(r => {
                    })
                }
            }
        });

        d.set_values({
            'practitioner': frm.doc.practitioner,
            'appointment_date': frappe.datetime.get_today()
        });


        // disable dialog action initially
        d.get_primary_btn().attr('disabled', true);

        // Field Change Handler
        let fd = d.fields_dict;

        d.fields_dict['appointment_date'].df.onchange = () => {
            if (frappe.datetime.get_today() > d.get_value('appointment_date')) {
                d.get_primary_btn().attr('disabled', true);
                frappe.msgprint('Older date or time cannot be selected in this appointment.')
            }
            show_slots(d, fd);
        };
        d.fields_dict['practitioner'].df.onchange = () => {
            if (d.get_value('practitioner') && d.get_value('practitioner') != selected_practitioner) {
                selected_practitioner = d.get_value('practitioner');
                show_slots(d, fd);
            }
        };

        d.$wrapper.find('.modal-dialog').css({
            "width": "800px",
            "max-height": "1600px",
            "overflow": "auto",
        });
        d.show();
    }

    function show_slots(d, fd) {
        if (d.get_value('appointment_date') && d.get_value('practitioner')) {
            fd.available_slots.html('');
            frappe.call({
                method: 'hms_tz.hms_tz.doctype.patient_appointment.patient_appointment.get_availability_data',
                args: {
                    practitioner: d.get_value('practitioner'),
                    date: d.get_value('appointment_date')
                },
                callback: (r) => {
                    let data = r.message;
                    if (data.slot_details.length > 0 || data.present_events.length > 0) {
                        let $wrapper = d.fields_dict.available_slots.$wrapper;

                        // make buttons for each slot
                        let slot_details = data.slot_details;
                        let slot_html = '';
                        for (let i = 0; i < slot_details.length; i++) {
                            slot_html = slot_html + `<label>${slot_details[i].slot_name}</label>`;
                            slot_html = slot_html + `<br/>` + slot_details[i].avail_slot.map(slot => {
                                let appointment_count = 0;
                                let disabled = false;
                                let start_str = slot.from_time;
                                let slot_start_time = moment(slot.from_time, 'HH:mm:ss');
                                let slot_to_time = moment(slot.to_time, 'HH:mm:ss');
                                let interval = (slot_to_time - slot_start_time) / 60000 | 0;
                                // iterate in all booked appointments, update the start time and duration
                                slot_details[i].appointments.forEach(function (booked) {
                                    let booked_moment = moment(booked.appointment_time, 'HH:mm:ss');
                                    let end_time = booked_moment.clone().add(booked.duration, 'minutes');
                                    // Deal with 0 duration appointments
                                    if (booked_moment.isSame(slot_start_time) || booked_moment.isBetween(slot_start_time, slot_to_time)) {
                                        if (booked.duration == 0) {
                                            disabled = true;
                                            return false;
                                        }
                                    }
                                    // Check for overlaps considering appointment duration
                                    if (slot_details[i].allow_overlap != 1) {
                                        if (slot_start_time.isBefore(end_time) && slot_to_time.isAfter(booked_moment)) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    }
                                    else {
                                        if (slot_start_time.isBefore(end_time) && slot_to_time.isAfter(booked_moment)) {
                                            appointment_count++
                                        }
                                        if (appointment_count >= slot_details[i].service_unit_capacity) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    }
                                });
                                //iterate in all absent events and disable the slots
                                slot_details[i].absent_events.forEach(function (event) {
                                    let event_from_time = moment(event.from_time, 'HH:mm:ss');
                                    let event_to_time = moment(event.to_time, 'HH:mm:ss');
                                    // Check for overlaps considering event start and end time
                                    if (slot_start_time.isBefore(event_to_time) && slot_to_time.isAfter(event_from_time)) {
                                        // There is an overlap
                                        disabled = true;
                                        return false;
                                    }
                                });
                                let count = ''
                                if (slot_details[i].allow_overlap == 1 && slot_details[i].service_unit_capacity > 1) {
                                    count = '' - '' + (slot_details[i].service_unit_capacity - appointment_count)
                                    // document.getElementById("count").style.fontSize = "xx-large";
                                }
                                return `<button class="btn btn-default"
									data-name=${start_str}
									data-duration=${interval}
									data-service-unit="${slot_details[i].service_unit || ''}"
									style="margin: 0 10px 10px 0; width: 72px;" ${disabled ? 'disabled="disabled"' : ""}>
									${start_str.substring(0, start_str.length - 3)} ${count}
								</button>`;
                            }).join("");
                            slot_html = slot_html + `<br/>`;
                        }
                        if (data.present_events && data.present_events.length > 0) {
                            slot_html = slot_html + `<br/>`;
                            var present_events = data.present_events
                            for (let i = 0; i < present_events.length; i++) {

                                slot_html = slot_html + `<label>${present_events[i].slot_name}</label>`;
                                slot_html = slot_html + `<br/>` + present_events[i].avail_slot.map(slot => {
                                    let appointment_count = 0;
                                    let disabled = false;
                                    let start_str = slot.from_time;
                                    let slot_start_time = moment(slot.from_time, 'HH:mm:ss');
                                    let slot_to_time = moment(slot.to_time, 'HH:mm:ss');
                                    let interval = (slot_to_time - slot_start_time) / 60000 | 0;
                                    //checking current time in slot
                                    var today = frappe.datetime.nowdate();
                                    if (today == d.get_value('appointment_date')) {
                                        // disable before  current  time in current date
                                        var curr_time = moment(frappe.datetime.now_time(), 'HH:mm:ss');
                                        if (slot_start_time.isBefore(curr_time)) {
                                            disabled = true;
                                        }
                                    }
                                    //iterate in all booked appointments, update the start time and duration
                                    present_events[i].appointments.forEach(function (booked) {
                                        let booked_moment = moment(booked.appointment_time, 'HH:mm:ss');
                                        let end_time = booked_moment.clone().add(booked.duration, 'minutes');
                                        // Deal with 0 duration appointments
                                        if (booked_moment.isSame(slot_start_time) || booked_moment.isBetween(slot_start_time, slot_to_time)) {
                                            if (booked.duration == 0) {
                                                disabled = true;
                                                return false;
                                            }
                                        }
                                        // Check for overlaps considering appointment duration
                                        if (present_events[i].allow_overlap != 1) {
                                            if (slot_start_time.isBefore(end_time) && slot_to_time.isAfter(booked_moment)) {
                                                // There is an overlap
                                                disabled = true;
                                                return false;
                                            }
                                        }
                                        else {
                                            if (slot_start_time.isBefore(end_time) && slot_to_time.isAfter(booked_moment)) {
                                                appointment_count++
                                            }
                                            if (appointment_count >= present_events[i].service_unit_capacity) {
                                                // There is an overlap
                                                disabled = true;
                                                return false;
                                            }
                                        }
                                    });
                                    //iterate in all absent events and disable the slots
                                    present_events[i].absent_events.forEach(function (event) {
                                        let event_from_time = moment(event.from_time, 'HH:mm:ss');
                                        let event_to_time = moment(event.to_time, 'HH:mm:ss');
                                        // Check for overlaps considering event start and end time
                                        if (slot_start_time.isBefore(event_to_time) && slot_to_time.isAfter(event_from_time)) {
                                            // There is an overlap
                                            disabled = true;
                                            return false;
                                        }
                                    });
                                    let count = ''
                                    if (present_events[i].allow_overlap == 1 && present_events[i].service_unit_capacity > 1) {
                                        count = '' - '' + (present_events[i].service_unit_capacity - appointment_count)
                                    }
                                    return `<button class="btn btn-default"
										data-name=${start_str}
										data-duration=${interval}
										data-service-unit="${present_events[i].service_unit || ''}"
										data-availability="${present_events[i].availability || ''}"
										flag-fixed-duration=${1}
										style="margin: 0 10px 10px 0; width: 72px;" ${disabled ? 'disabled="disabled"' : ""}>
										${start_str.substring(0, start_str.length - 3)} ${count}
									</button>`;
                                }).join("");
                                slot_html = slot_html + `<br/>`;
                            }
                        }
                        $wrapper
                            .css('margin-bottom', 0)
                            .addClass('text-center')
                            .html(slot_html);

                        // primtary button when clicked
                        $wrapper.on('click', 'button', function () {
                            if (frappe.datetime.get_today() > d.get_value('appointment_date')) {
                                d.get_primary_btn().attr('disabled', true);
                                frappe.msgprint('Older date or time cannot be selected in this appointment.')
                                return
                            }
                            let $btn = $(this);
                            $wrapper.find('button').removeClass('btn-primary');
                            $btn.addClass('btn-primary');
                            selected_slot = $btn.attr('data-name');
                            service_unit = $btn.attr('data-service-unit');
                            duration = $btn.attr('data-duration');
                            practitioner_availability = $btn.attr('data-availability')
                            // enable dialog action
                            d.get_primary_btn().attr('disabled', null);
                        });


                    } else {
                        //	fd.available_slots.html('Please select a valid date.'.bold())
                        show_empty_state(d.get_value('practitioner'), d.get_value('appointment_date'));
                    }
                },
                freeze: true,
                freeze_message: __('Fetching records......')
            });
        } else {
            fd.available_slots.html(__('Appointment date and Healthcare Practitioner are Mandatory').bold());
        }
    }
};


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
    if (
        !frm.doc.patient ||
        frm.is_new() ||
        frm.doc.invoiced ||
        frm.doc.status == "Closed" ||
        frm.doc.status == "Cancelled" ||
        frm.doc.healthcare_package_order
    ) {
        return;
    }

    var vitals_btn_required = false;
    var valid_days = null
    if (frm.doc.insurance_subscription) {
        valid_days = get_value("Healthcare Insurance Coverage Plan", frm.doc.coverage_plan_name, "no_of_days_for_follow_up")

        if (!valid_days || valid_days == 0) {
            valid_days = get_value("Healthcare Insurance Company", frm.doc.insurance_company, "no_of_days_for_follow_up")
        }
    } else if (frm.doc.mode_of_payment) {
        valid_days = get_value("Healthcare Settings", "Healthcare Settings", "valid_days");
    }

    let filters = {
        name: ["!=", frm.doc.name],
        department: frm.doc.department,
        status: ["in", ["Open", "Closed"]]
    }
    if (frm.doc.insurance_subscription) {
        filters.insurance_subscription = frm.doc.insurance_subscription;
    } else {
        filters.mode_of_payment = ["!=", ""]
    }
    const appointment = get_previous_appointment(frm, filters);
    if (typeof appointment != "undefined") {
        const last_appointment_date = appointment.appointment_date;
        const diff = frappe.datetime.get_day_diff(frm.doc.appointment_date, last_appointment_date);
        if (diff >= 0 && diff <= valid_days) {
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
    if (frm.doc.invoiced) return;
    frm.add_custom_button(__('Create Sales Invoice'), function () {
        frm.save();
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.invoice_appointment',
            freeze: true,
            freeze_message: __('Processing ...'),
            args: {
                'name': frm.doc.name
            },
            callback: function (data) {
                frm.reload_doc();
            }
        });
    });
};

const add_vital_btn = (frm) => {
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
};

const validate_insurance_company = (frm) => {
    frappe.call('hms_tz.nhif.api.patient_appointment.validate_insurance_company', {
        insurance_company: frm.doc.insurance_company
    })
        .then(r => {
            if (r.message) {
                frm.set_value("insurance_subscription", "");
                frm.set_value("insurance_company", "");
                frm.set_value("coverage_plan_name", "");
                frm.set_value("coverage_plan_card_number", "");
                frm.set_value("insurance_company_name", "");
            }
        });
}