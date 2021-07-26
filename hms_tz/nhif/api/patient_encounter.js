frappe.ui.form.on('Patient Encounter', {
    on_submit: function (frm) {
        if (!frm.doc.patient_encounter_final_diagnosis) {
            frappe.throw(__("Final diagnosis mandatory before submit"));
        }
    },
    validate: function (frm) {
        validate_medical_code(frm);
    },
    onload: function (frm) {
        add_btn_final(frm);
        duplicate(frm);
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Create Pending Healthcare Services'), function () {
                frappe.call({
                    method: 'hms_tz.nhif.api.patient_encounter.create_healthcare_docs_from_name',
                    args: {
                        'patient_encounter_doc_name': frm.doc.name
                    },
                    callback: (function (data) {
                        //
                    })
                });
            });
        };
        frm.set_query('healthcare_service_unit', 'drug_prescription', function () {
            return {
                filters: [
                    {
                        'service_unit_type': 'Pharmacy'
                    }
                ]
            };
        });
    },
    refresh: function (frm) {
        set_medical_code(frm, true);
        if (frm.doc.duplicated == 1 || frm.doc.finalized) {
            frm.remove_custom_button("Schedule Admission");
            frm.remove_custom_button("Refer Practitioner");
            frm.remove_custom_button("Vital Signs", "Create");
            frm.remove_custom_button("Medical Record", "Create");
            frm.remove_custom_button("Clinical Procedure", "Create");
        }
        add_btn_final(frm);
        duplicate(frm);
        if (frm.doc.source == "External Referral") {
            frm.set_df_property('referring_practitioner', 'hidden', 1);
            frm.set_df_property('referring_practitioner', 'reqd', 0);
        };
        frm.set_query('lab_test_code', 'lab_test_prescription', function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
        frm.set_query('radiology_examination_template', 'radiology_procedure_prescription', function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
        frm.set_query('procedure', 'procedure_prescription', function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
        frm.set_query('drug_code', 'drug_prescription', function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
        frm.set_query('therapy_type', 'therapies', function () {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
    },
    default_healthcare_service_unit: function (frm) {
        if (frm.doc.default_healthcare_service_unit) {
            frm.doc.drug_prescription.forEach(row => {
                if (!row.healthcare_service_unit) {
                    frappe.model.set_value(
                        row.doctype,
                        row.name,
                        "healthcare_service_unit",
                        frm.doc.default_healthcare_service_unit
                    );
                }
            });
        }
    },
    get_chronic_diagnosis: function (frm) {
        if (frm.doc.docstatus == 1) {
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_encounter.get_chronic_diagnosis',
            args: {
                'patient': frm.doc.patient,
            },
            callback: function (data) {
                if (data.message) {
                    if (data.message.length == 0) {
                        frappe.show_alert({
                            message: __(`There are no Chronic Diagnosis for this patient`),
                            indicator: 'red'
                        }, 5);
                        return;
                    }
                    data.message.forEach(element => {
                        const row_idx = frm.doc.patient_encounter_preliminary_diagnosis.findIndex(x => x.medical_code === element.medical_code);
                        if (row_idx === -1) {
                            let row = frappe.model.add_child(frm.doc, "Codification Table", "patient_encounter_preliminary_diagnosis");
                            row.medical_code = element.medical_code;
                            row.code = element.code;
                            row.description = element.description;
                            frappe.show_alert({
                                message: __(`Medical Code '${element.medical_code}' added successfully`),
                                indicator: 'green'
                            }, 5);
                        } else {
                            frappe.show_alert({
                                message: __(`Medical Code '${element.medical_code}' already exists`),
                                indicator: 'red'
                            }, 5);
                        }
                    });
                    refresh_field('patient_encounter_preliminary_diagnosis');
                    set_medical_code(frm);
                }
            }
        });
    },
    get_chronic_medications: function (frm) {
        if (frm.doc.docstatus == 1) {
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_encounter.get_chronic_medications',
            args: {
                'patient': frm.doc.patient,
            },
            callback: function (data) {
                if (data.message) {
                    if (data.message.length == 0) {
                        frappe.show_alert({
                            message: __(`There is no Chronic Medications`),
                            indicator: 'red'
                        }, 5);
                        return;
                    }
                    data.message.forEach(element => {
                        const row_idx = frm.doc.drug_prescription.findIndex(x => x.drug_code === element.drug_code);
                        if (row_idx === -1) {
                            let row = frappe.model.add_child(frm.doc, "Drug Prescription", "drug_prescription");
                            row.drug_code = element.drug_code;
                            row.drug_name = element.drug_name;
                            row.dosage = element.dosage;
                            row.period = element.period;
                            row.dosage_form = element.dosage_form;
                            row.comment = element.comment;
                            row.usage_interval = element.usage_interval;
                            row.interval = element.interval;
                            row.interval_uom = element.interval_uom;
                            row.update_schedule = element.update_schedule;
                            row.intent = element.intent;
                            row.quantity = element.quantity;
                            row.sequence = element.sequence;
                            row.expected_date = element.expected_date;
                            row.as_needed = element.as_needed;
                            row.patient_instruction = element.patient_instruction;
                            row.replaces = element.replaces;
                            row.priority = element.priority;
                            row.occurrence = element.occurrence;
                            row.occurence_period = element.occurence_period;
                            row.note = element.note;
                            frappe.show_alert({
                                message: __(`Drug '${element.drug_code}' added successfully`),
                                indicator: 'green'
                            }, 5);
                        } else {
                            frappe.show_alert({
                                message: __(`Drug '${element.drug_code}' already exists`),
                                indicator: 'red'
                            }, 5);
                        }
                    });
                    refresh_field('drug_prescription');
                }
            }
        });
    },
    copy_from_preliminary_diagnosis: function (frm) {
        if (frm.doc.docstatus == 1) {
            return;
        }
        frm.doc.patient_encounter_preliminary_diagnosis.forEach(element => {
            const row_idx = frm.doc.patient_encounter_final_diagnosis.findIndex(x => x.medical_code === element.medical_code);
            if (row_idx === -1) {
                let row = frappe.model.add_child(frm.doc, "Codification Table", "patient_encounter_final_diagnosis");
                row.medical_code = element.medical_code;
                row.code = element.code;
                row.description = element.description;
                row.mtuha = element.mtuha;
                // frappe.show_alert({
                //     message: __(`Medical Code '${element.medical_code}' added successfully`),
                //     indicator: 'green'
                // }, 5);
            } else {
                frappe.show_alert({
                    message: __(`Medical Code '${element.medical_code}' already exists`),
                    indicator: 'red'
                }, 5);
            }
        });
        refresh_field('patient_encounter_final_diagnosis');
        set_medical_code(frm);
    },
    encounter_category: function (frm) {
        if (frm.doc.patient_encounter_preliminary_diagnosis && frm.doc.patient_encounter_preliminary_diagnosis.length > 0) {
            return;
        } else if (frm.doc.encounter_category.includes("Direct Cash")) {
            let preliminary_row = frappe.model.add_child(frm.doc, "Codification Table", "patient_encounter_preliminary_diagnosis");
            preliminary_row.medical_code = "ICD-10 R69";
            preliminary_row.code = "R69";
            preliminary_row.description = "Illness, unspecified";
            preliminary_row.mtuha = "Other";
            refresh_field('patient_encounter_preliminary_diagnosis');
            let final_row = frappe.model.add_child(frm.doc, "Codification Table", "patient_encounter_final_diagnosis");
            final_row.medical_code = "ICD-10 R69";
            final_row.code = "R69";
            final_row.description = "Illness, unspecified";
            final_row.mtuha = "Other";
            refresh_field('patient_encounter_final_diagnosis');
        }
        set_medical_code(frm);

    },
    create_sales_invoice: function (frm) {
        if (frm.doc.docstatus != 0 || !frm.doc.encounter_mode_of_payment || !frm.doc.encounter_category || frm.doc.sales_invoice) {
            frappe.show_alert(__("The criteria for this button to work not met!"))
            return;
        }
        frappe.call({
            method: 'hms_tz.nhif.api.patient_encounter.create_sales_invoice',
            args: {
                'encounter': frm.doc.name,
                'encounter_category': frm.doc.encounter_category,
                'encounter_mode_of_payment': frm.doc.encounter_mode_of_payment,
            },
            callback: function (data) {
                frm.reload_doc();
            }
        });
    },
    sent_to_vfd: function (frm) {
        if (!frm.doc.sales_invoice) return;
        frappe.call({
            method: 'hms_tz.nhif.api.patient_appointment.send_vfd',
            args: {
                invoice_name: frm.doc.sales_invoice,
            },
            callback: function (data) {
                if (data.message) {
                    if (data.message.enqueue) {
                        load_print_page(frm.doc.sales_invoice, data.message.pos_rofile);
                    }
                }
            }
        });
    },
    undo_set_as_final: function (frm) {
        if (!frm.doc.finalized) return;
        frappe.call({
            method: "hms_tz.nhif.api.patient_encounter.undo_finalized_encounter",
            args: {
                ref_encounter: frm.doc.reference_encounter,
                cur_encounter: frm.doc.name,
            },
            callback: function (data) {
                frm.reload_doc();
            },
        });
    },
});

frappe.ui.form.on('Drug Prescription', {
    drug_prescription_add: function (frm, cdt, cdn) {
        var row = frappe.get_doc(cdt, cdn);
        if (!row.healthcare_service_unit) row.healthcare_service_unit = frm.doc.default_healthcare_service_unit;
        refresh_field("drug_prescription");
    }
});

frappe.ui.form.on('Codification Table', {
    patient_encounter_preliminary_diagnosis_remove: set_medical_code,
    patient_encounter_final_diagnosis_remove: set_medical_code,
    medical_code: set_medical_code,
});

function get_diagnosis_list(frm, table_name) {
    const diagnosis_list = [];
    if (frm.doc[table_name]) {
        frm.doc[table_name].forEach(element => {
            if (!element.medical_code) return;
            diagnosis_list.push(element.medical_code);
        });
    }
    return diagnosis_list;
}

const medical_code_mapping = {
    "patient_encounter_preliminary_diagnosis": [
        'lab_test_prescription',
        'radiology_procedure_prescription'
    ],
    "patient_encounter_final_diagnosis": [
        'procedure_prescription',
        'drug_prescription',
        'therapies',
        'diet_recommendation'
    ]
}

function set_medical_code(frm, reset_columns) {
    function set_options_for_fields(fields, from_table) {
        const options = get_diagnosis_list(frm, from_table);

        for (const fieldname of fields) {
            const grid = frm.fields_dict[fieldname].grid;

            if (reset_columns) {
                grid.visible_columns = undefined;
                grid.setup_visible_columns();
            }

            grid.fields_map.medical_code.options = options;
            grid.refresh();
        }
    }

    for (const [from_table, fields] of Object.entries(medical_code_mapping)) {
        set_options_for_fields(fields, from_table);
    }
};

function validate_medical_code(frm) {

    for (const [from_table, fields] of Object.entries(medical_code_mapping)) {
        const options = get_diagnosis_list(frm, from_table);

        for (const fieldname of fields) {
            if (!frm.doc[fieldname]) continue;

            frm.doc[fieldname].forEach(element => {
                if (!options.includes(element.medical_code)) {
                    frappe.throw(__(`The Medical Code in the
                    ${frm.fields_dict[fieldname].df.label} table
                    at line ${element.idx} is empty or does not exist in the
                    ${frm.fields_dict[from_table].df.label} table.`));
                }
            })
        }
    }
};

var add_btn_final = function (frm) {
    if (frm.doc.docstatus == 1 && frm.doc.encounter_type != 'Final' && frm.doc.duplicated == 0) {
        frm.add_custom_button(__('Set as Final'), function () {
            frappe.call({
                method: 'hms_tz.nhif.api.patient_encounter.finalized_encounter',
                args: {
                    'ref_encounter': frm.doc.reference_encounter,
                    'cur_encounter': frm.doc.name
                },
                callback: (function (data) {
                    frm.reload_doc();
                })
            });
        });
    }
};

var duplicate = function (frm) {
    if (frm.doc.docstatus != 1 || frm.doc.encounter_type == 'Final' || frm.doc.duplicated == 1 || frm.doc.healthcare_practitioner == "Direct Cash") {
        return;
    }
    frm.add_custom_button(__('Duplicate'), function () {
        if (frm.is_dirty()) {
            frm.save();
        }

        frappe.call({
            method: 'hms_tz.nhif.api.patient_encounter.duplicate_encounter',
            args: {
                'encounter': frm.doc.name
            },
            callback: function (data) {
                if (data.message) {
                    frappe.set_route('Form', 'Patient Encounter', data.message);
                    setTimeout(function () {
                        frm.reload_doc();
                    }, 2000);
                }
            }
        });
    });
};

frappe.ui.form.on('Lab Prescription', {
    lab_test_code: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            msgprint = "NOTE: This healthcare service item, <b>" + row.lab_test_code + "</b>, is not available inhouse and has been marked as prescribe.<br><br>Request the patient to get it from another healthcare service provider."
            frappe.show_alert(__(msgprint))
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
        if (!row.lab_test_code) { return; }
        validate_stock_item(frm, row.lab_test_code, 1, row.healthcare_service_unit, "Lab Test Template");
    },
    is_not_available_inhouse: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            frappe.model.set_value(cdt, cdn, "prescribe", 1);
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
    },
    prescribe: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.prescribe || !row.lab_test_code) {
            frappe.model.set_value(cdt, cdn, "override_subscription", 0);
        }
    },
    override_subscription: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.override_subscription) {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
            validate_stock_item(frm, row.lab_test_code, 1, row.healthcare_service_unit, "Lab Test Template");
        }
    },
});

frappe.ui.form.on('Radiology Procedure Prescription', {
    radiology_examination_template: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.is_not_available_inhouse) {
            msgprint = "NOTE: This healthcare service item, <b>" + row.radiology_examination_template + "</b>, is not available inhouse and has been marked as prescribe.<br>Request the patient to get it from another healthcare service provider."
            frappe.show_alert(__(msgprint))
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
        if (!row.radiology_examination_template) { return; }
        validate_stock_item(frm, row.radiology_examination_template, 1, row.healthcare_service_unit, "Radiology Examination Template");
    },
    is_not_available_inhouse: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            frappe.model.set_value(cdt, cdn, "prescribe", 1);
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
    },
    prescribe: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.prescribe || !row.radiology_examination_template) {
            frappe.model.set_value(cdt, cdn, "override_subscription", 0);
        }
    },
    override_subscription: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.override_subscription) {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
            validate_stock_item(frm, row.radiology_examination_template, 1, row.healthcare_service_unit, "Radiology Examination Template");
        }
    },
});

frappe.ui.form.on('Procedure Prescription', {
    procedure: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.is_not_available_inhouse) {
            msgprint = "NOTE: This healthcare service item, <b>" + row.procedure + "</b>, is not available inhouse and has been marked as prescribe.<br>Request the patient to get it from another healthcare service provider."
            frappe.show_alert(__(msgprint))
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
        if (!row.procedure) { return; }
        validate_stock_item(frm, row.procedure, 1, row.healthcare_service_unit, "Clinical Procedure Template");
    },
    is_not_available_inhouse: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            frappe.model.set_value(cdt, cdn, "prescribe", 1);
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
    },
    prescribe: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.prescribe || !row.procedure) {
            frappe.model.set_value(cdt, cdn, "override_subscription", 0);
        }
    },
    override_subscription: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.override_subscription) {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
            validate_stock_item(frm, row.procedure, 1, row.healthcare_service_unit, "Clinical Procedure Template");
        }
    },
});

frappe.ui.form.on('Drug Prescription', {
    drug_code: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.is_not_available_inhouse) {
            msgprint = "NOTE: This healthcare service item, <b>" + row.drug_code + "</b>, is not available inhouse and has been marked as prescribe.<br>Request the patient to get it from another healthcare service provider."
            frappe.show_alert(__(msgprint))
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
        if (!row.drug_code) { return; }
        validate_stock_item(frm, row.drug_code, row.quantity, row.healthcare_service_unit, "Drug Prescription");
    },
    healthcare_service_unit: function (frm, cdt, cdn) {
        if (frm.healthcare_service_unit) frm.trigger("drug_code");
    },
    is_not_available_inhouse: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            frappe.model.set_value(cdt, cdn, "prescribe", 1);
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
    },
    prescribe: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.prescribe || !row.drug_code) {
            frappe.model.set_value(cdt, cdn, "override_subscription", 0);
        }
    },
    quantity: function (frm, cdt, cdn) {
        if (frm.quantity) frm.trigger("drug_code");
    },
    override_subscription: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.override_subscription) {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
            validate_stock_item(frm, row.drug_code, row.quantity, row.healthcare_service_unit, "Drug Prescription");
        }
    },
    dosage: function (frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "quantity", 0);
        frm.refresh_field("drug_prescription");
    },
});

frappe.ui.form.on('Therapy Plan Detail', {
    therapy_type: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.is_not_available_inhouse) {
            msgprint = "NOTE: This healthcare service item, <b>" + row.therapy_type + "</b>, is not available inhouse and has been marked as prescribe.<br>Request the patient to get it from another healthcare service provider."
            frappe.show_alert(__(msgprint))
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
        if (!row.therapy_type) { return; }
        validate_stock_item(frm, row.therapy_type, 1, row.healthcare_service_unit, "Therapy Type");
    },
    is_not_available_inhouse: function (frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.is_not_available_inhouse) {
            frappe.model.set_value(cdt, cdn, "prescribe", 1);
        } else {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
        }
    },
    prescribe: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.prescribe || !row.therapy_type) {
            frappe.model.set_value(cdt, cdn, "override_subscription", 0);
        }
    },
    override_subscription: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.override_subscription) {
            frappe.model.set_value(cdt, cdn, "prescribe", 0);
            validate_stock_item(frm, row.therapy_type, 1, row.healthcare_service_unit, "Therapy Type");
        }
    },
});


const validate_stock_item = function (frm, healthcare_service, qty = 1, healthcare_service_unit = "", caller = "Unknown") {
    if (healthcare_service_unit == "") {
        healthcare_service_unit = frm.doc.healthcare_service_unit;
    }
    frappe.call({
        method: 'hms_tz.nhif.api.patient_encounter.validate_stock_item',
        args: {
            'healthcare_service': healthcare_service,
            'qty': qty,
            'caller': caller,
            'healthcare_service_unit': healthcare_service_unit
        },
        callback: function (data) {
            if (data.message) {
                // console.log(data.message)
            }
        }
    });
};
const load_print_page = function (invoice_name, pos_profile) {
    const print_format = pos_profile.print_format || "AV Tax Invoice";
    const letter_head = pos_profile.letter_head || 0;
    const url =
        frappe.urllib.get_base_url() +
        "/printview?doctype=Sales%20Invoice&name=" +
        invoice_name +
        "&trigger_print=1" +
        "&format=" +
        print_format +
        "&no_letterhead=" +
        letter_head;
    const printWindow = window.open(url, "Print");
    printWindow.addEventListener(
        "load",
        function () {
            printWindow.print();
        },
        true
    );
};
