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

	refresh(frm){
		if (frm.doc.authorization_no){
			frm.add_custom_button(__("Merge Claims"), function() {
				frappe.call({
					method: "hms_tz.nhif.doctype.nhif_patient_claim.nhif_patient_claim.merge_nhif_claims",
					args: {"authorization_no": frm.doc.authorization_no},
					callback: function(){
						frm.reload_doc();
					}
				})
			})
		}
	}
});