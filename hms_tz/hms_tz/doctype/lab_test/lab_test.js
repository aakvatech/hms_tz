// Copyright (c) 2016, ESS and contributors
// For license information, please see license.txt

cur_frm.cscript.custom_refresh = function (doc) {
	cur_frm.toggle_display('sb_sensitivity', doc.sensitivity_toggle);
	cur_frm.toggle_display('organisms_section', doc.descriptive_toggle);
	cur_frm.toggle_display('sb_descriptive', doc.descriptive_toggle);
	cur_frm.toggle_display('sb_normal', doc.normal_toggle);
};

frappe.ui.form.on('Lab Test', {
	setup: function (frm) {
		frm.get_field('normal_test_items').grid.editable_fields = [
			{ fieldname: 'lab_test_name', columns: 3 },
			{ fieldname: 'lab_test_event', columns: 2 },
			{ fieldname: 'result_value', columns: 2 },
			{ fieldname: 'lab_test_uom', columns: 1 },
			{ fieldname: 'normal_range', columns: 2 }
		];
		frm.get_field('descriptive_test_items').grid.editable_fields = [
			{ fieldname: 'lab_test_particulars', columns: 3 },
			{ fieldname: 'result_value', columns: 7 }
		];
	},

	onload: function (frm) {
		if (frm.doc.source) {
			set_source_referring_practitioner(frm)
		}
	},

	refresh: function (frm) {
		refresh_field('normal_test_items');
		refresh_field('descriptive_test_items');
		frm.set_query('referring_practitioner', function () {
			if (frm.doc.source == 'External Referral') {
				return {
					filters: {
						'healthcare_practitioner_type': 'External'
					}
				};
			}
			else {
				return {
					filters: {
						'healthcare_practitioner_type': 'Internal'
					}
				};
			}
		});

		if (frm.doc.__islocal) {
			return;
			frm.add_custom_button(__('Get from Patient Encounter'), function () {
				get_lab_test_prescribed(frm);
			});
		}
		if (frappe.defaults.get_default('lab_test_approval_required') && frappe.user.has_role('LabTest Approver')) {
			if (frm.doc.docstatus === 1 && frm.doc.status !== 'Approved' && frm.doc.status !== 'Rejected') {
				frm.add_custom_button(__('Approve'), function () {
					status_update(1, frm);
				}, __('Actions'));
				frm.add_custom_button(__('Reject'), function () {
					status_update(0, frm);
				}, __('Actions'));
			}
		}

		if (frm.doc.docstatus === 1 && frm.doc.sms_sent === 0 && frm.doc.status !== 'Rejected') {
			frm.add_custom_button(__('Send SMS'), function () {
				frappe.call({
					method: 'healthcare.healthcare.doctype.healthcare_settings.healthcare_settings.get_sms_text',
					args: { doc: frm.doc.name },
					callback: function (r) {
						if (!r.exc) {
							var emailed = r.message.emailed;
							var printed = r.message.printed;
							make_dialog(frm, emailed, printed);
						}
					}
				});
			});
		}
		frm.set_query('insurance_subscription', function () {
			return {
				filters: {
					'patient': frm.doc.patient,
					'docstatus': 1
				}
			};
		});
		if (frm.doc.workflow_state === "Sample Analyzed") {
            if (frm.doc.descriptive_test_items && frm.doc.descriptive_test_items.length > 0) {
                frm.doc.descriptive_test_items.forEach(function(row) {
                    if (!row.result_component_option) {
                        frappe.throw(`Error: Result value is missing for <b>${row.lab_test_particulars}</b>`);
                    }
                });
            }
            else if (frm.doc.normal_test_items && frm.doc.normal_test_items.length > 0) {
                frm.doc.normal_test_items.forEach(function(row) {
                    if (!row.result_value) {
                        frappe.throw(`Error: Result value is missing for <b>${row.lab_test_name}</b>`);
                    }
                });
            }
        }
	},

	source: function (frm) {
		if (frm.doc.source) {
			set_source_referring_practitioner(frm);
		}
	}

});

frappe.ui.form.on('Lab Test', 'patient', function (frm) {
	if (frm.doc.patient) {
		frappe.call({
			'method': 'hms_tz.hms_tz.doctype.patient.patient.get_patient_detail',
			args: { patient: frm.doc.patient },
			callback: function (data) {
				var age = null;
				if (data.message.dob) {
					age = calculate_age(data.message.dob);
				}
				let values = {
					'patient_age': age,
					'patient_sex': data.message.sex,
					'email': data.message.email,
					'mobile': data.message.mobile,
					'report_preference': data.message.report_preference
				};
				frm.set_value(values);
			}
		});
	}
});

frappe.ui.form.on('Normal Test Result', {
	normal_test_items_remove: function () {
		frappe.msgprint(__('Not permitted, configure Lab Test Template as required'));
		cur_frm.reload_doc();
	}
});

frappe.ui.form.on('Descriptive Test Result', {
	descriptive_test_items_remove: function () {
		frappe.msgprint(__('Not permitted, configure Lab Test Template as required'));
		cur_frm.reload_doc();
	}
});

var status_update = function (approve, frm) {
	var doc = frm.doc;
	var status = null;
	if (approve == 1) {
		status = 'Approved';
	}
	else {
		status = 'Rejected';
	}
	frappe.call({
		method: 'hms_tz.hms_tz.doctype.lab_test.lab_test.update_status',
		args: { status: status, name: doc.name },
		callback: function () {
			cur_frm.reload_doc();
		}
	});
};

var get_lab_test_prescribed = function (frm) {
	if (frm.doc.patient) {
		frappe.call({
			method: 'hms_tz.hms_tz.doctype.lab_test.lab_test.get_lab_test_prescribed',
			args: { patient: frm.doc.patient },
			callback: function (r) {
				show_lab_tests(frm, r.message);
			}
		});
	}
	else {
		frappe.msgprint(__('Please select Patient to get Lab Tests'));
	}
};

var show_lab_tests = function (frm, lab_test_list) {
	var d = new frappe.ui.Dialog({
		title: __('Lab Tests'),
		fields: [{
			fieldtype: 'HTML', fieldname: 'lab_test'
		}]
	});
	var html_field = d.fields_dict.lab_test.$wrapper;
	html_field.empty();
	$.each(lab_test_list, function (x, y) {
		var row = $(repl(
			'<div class="col-xs-12" style="padding-top:12px;">\
				<div class="col-xs-3"> %(lab_test)s </div>\
				<div class="col-xs-4"> %(practitioner_name)s<br>%(encounter)s</div>\
				<div class="col-xs-3"> %(date)s </div>\
				<div class="col-xs-1">\
					<a data-name="%(name)s" data-lab-test="%(lab_test)s"\
					data-encounter="%(encounter)s" data-practitioner="%(practitioner)s"\
					data-invoiced="%(invoiced)s" data-source="%(source)s"\
					data-referring-practitioner="%(referring_practitioner)s" href="#"><button class="btn btn-default btn-xs">Get</button></a>\
				</div>\
			</div><hr>',
			{ name: y[0], lab_test: y[1], encounter: y[2], invoiced: y[3], practitioner: y[4], practitioner_name: y[5], date: y[6], source: y[7], referring_practitioner: y[8] })
		).appendTo(html_field);

		row.find("a").click(function () {
			frm.doc.template = $(this).attr('data-lab-test');
			frm.doc.prescription = $(this).attr('data-name');
			frm.doc.practitioner = $(this).attr('data-practitioner');
			frm.set_df_property('template', 'read_only', 1);
			frm.set_df_property('patient', 'read_only', 1);
			frm.set_df_property('practitioner', 'read_only', 1);
			frm.doc.invoiced = 0;
			if ($(this).attr('data-invoiced') === 1) {
				frm.doc.invoiced = 1;
			}
			frm.doc.source = $(this).attr('data-source');
			frm.set_df_property('source', 'read_only', 1);
			frm.doc.referring_practitioner = $(this).attr('data-referring-practitioner');
			if (frm.doc.referring_practitioner) {
				frm.set_df_property('referring_practitioner', 'hidden', 0);
				frm.set_df_property('referring_practitioner', 'read_only', 1);
			}
			frm.refresh_field('invoiced');
			frm.refresh_field('template');
			frm.refresh_field('source');
			frm.refresh_field('referring_practitioner');

			d.hide();
			return false;
		});
	});
	if (!lab_test_list.length) {
		var msg = __('No Lab Tests found for the Patient {0}', [frm.doc.patient_name.bold()]);
		html_field.empty();
		$(repl('<div class="col-xs-12" style="padding-top:0px;" >%(msg)s</div>', { msg: msg })).appendTo(html_field);
	}
	d.show();
};

var make_dialog = function (frm, emailed, printed) {
	var number = frm.doc.mobile;

	var dialog = new frappe.ui.Dialog({
		title: 'Send SMS',
		width: 400,
		fields: [
			{ fieldname: 'result_format', fieldtype: 'Select', label: 'Result Format', options: ['Emailed', 'Printed'] },
			{ fieldname: 'number', fieldtype: 'Data', label: 'Mobile Number', reqd: 1 },
			{ fieldname: 'message', fieldtype: 'Small Text', label: 'Message', reqd: 1 }
		],
		primary_action_label: __('Send'),
		primary_action: function () {
			var values = dialog.fields_dict;
			if (!values) {
				return;
			}
			send_sms(values, frm);
			dialog.hide();
		}
	});
	if (frm.doc.report_preference === 'Print') {
		dialog.set_values({
			'result_format': 'Printed',
			'number': number,
			'message': printed
		});
	} else {
		dialog.set_values({
			'result_format': 'Emailed',
			'number': number,
			'message': emailed
		});
	}
	var fd = dialog.fields_dict;
	$(fd.result_format.input).change(function () {
		if (dialog.get_value('result_format') === 'Emailed') {
			dialog.set_values({
				'number': number,
				'message': emailed
			});
		} else {
			dialog.set_values({
				'number': number,
				'message': printed
			});
		}
	});
	dialog.show();
};

var send_sms = function (vals, frm) {
	var number = vals.number.value;
	var message = vals.message.last_value;

	if (!number || !message) {
		frappe.throw(__('Did not send SMS, missing patient mobile number or message content.'));
	}
	frappe.call({
		method: 'frappe.core.doctype.sms_settings.sms_settings.send_sms',
		args: {
			receiver_list: [number],
			msg: message
		},
		callback: function (r) {
			if (r.exc) {
				frappe.msgprint(r.exc);
			} else {
				frm.reload_doc();
			}
		}
	});
};

var calculate_age = function (dob) {
	var ageMS = Date.parse(Date()) - Date.parse(dob);
	var age = new Date();
	age.setTime(ageMS);
	var years = age.getFullYear() - 1970;
	return years + ' Year(s) ' + age.getMonth() + ' Month(s) ' + age.getDate() + ' Day(s)';
};

let set_source_referring_practitioner = function (frm) {
	if (frm.doc.source == 'Direct') {
		frm.set_value('referring_practitioner', '');
		frm.set_df_property('referring_practitioner', 'hidden', 1);
		frm.set_df_property('referring_practitioner', 'reqd', 0);
	}
	else if (frm.doc.source == 'External Referral' || frm.doc.source == 'Referral') {
		if (frm.doc.practitioner) {
			frm.set_df_property('referring_practitioner', 'hidden', 0);
			if (frm.doc.source == 'External Referral') {
				frappe.db.get_value('Healthcare Practitioner', frm.doc.practitioner, 'healthcare_practitioner_type', function (r) {
					if (r && r.healthcare_practitioner_type && r.healthcare_practitioner_type == 'External') {
						frm.set_value('referring_practitioner', frm.doc.practitioner);
					}
					else {
						frm.set_value('referring_practitioner', '');
					}
				});
				frm.set_df_property('referring_practitioner', 'read_only', 0);
			}
			else {
				frappe.db.get_value('Healthcare Practitioner', frm.doc.practitioner, 'healthcare_practitioner_type', function (r) {
					if (r && r.healthcare_practitioner_type && r.healthcare_practitioner_type == 'Internal') {
						frm.set_value('referring_practitioner', frm.doc.practitioner);
						frm.set_df_property('referring_practitioner', 'read_only', 1);
					}
					else {
						frm.set_value('referring_practitioner', '');
						frm.set_df_property('referring_practitioner', 'read_only', 0);
					}
				});
			}
			frm.set_df_property('referring_practitioner', 'reqd', 1);
		}
		else {
			frm.set_df_property('referring_practitioner', 'read_only', 0);
			frm.set_df_property('referring_practitioner', 'hidden', 0);
			frm.set_df_property('referring_practitioner', 'reqd', 1);
		}
	}
};
