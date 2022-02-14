// Copyright (c) 2020, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('NHIF Patient Claim', {
	setup: function (frm) {
		frm.set_query("patient_appointment", function () {
			return {
				"filters": {
					"nhif_patient_claim": ["in", ["", "None"]],
					"insurance_company": ["like", "NHIF%"],
					"insurance_subscription": ["not in", ["", "None"]]
				}
			};
		});
	},

	refresh(frm) {
		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__("Merge Claims"), function () {
				frm.call("get_appointments", { self: frm.doc }
				).then(r => {
					frm.save()
					frm.trigger("validate");
				});
			});
			
			frm.set_value("allow_changes", 0);
			frm.save();
		}
	}
});