// Copyright (c) 2020, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company Insurance Setting', {
	// refresh: function(frm) {

	// }
	auto_submit_patient_claim: (frm) => {
		if (!frm.doc.submit_claim_year || !frm.doc.submit_claim_month) {
			frappe.msgprint("Please set submit claim year or submit claim month}");
			return
		}
		if (frm.doc.api_provider == "NHIF") {
			frappe.call("hms_tz.nhif.api.healthcare_utils.auto_submit_nhif_patient_claim", {
				setting_dict: {
					"company": frm.doc.name,
					"submit_claim_year": frm.doc.submit_claim_year,
					"submit_claim_month": frm.doc.submit_claim_month
				}
			}).then(r => {
				// do nothing
			})
		}
	}
});
