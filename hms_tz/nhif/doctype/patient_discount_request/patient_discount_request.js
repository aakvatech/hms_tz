// Copyright (c) 2023, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patient Discount Request', {
	refresh: (frm) => {
		frm.trigger("set_field_properties");
	},
	onload: (frm) => {
		frm.trigger("set_field_properties");
	},
	payment_type: (frm) => {
		if (!frm.doc.payment_type) {
			frm.set_value("apply_discount_on", "");
			frm.set_df_property("apply_discount_on", "read_only", 0);

		} else if (frm.doc.payment_type == "Non NHIF Insurance") {
			frm.set_df_property("apply_discount_on", "options", ["Group of Items"]);
			frm.set_value("apply_discount_on", "Group of Items");
			frm.set_df_property("apply_discount_on", "read_only", 1);
		}
	},
	apply_discount_on: (frm) => {
		if (["Grand Total", "Net Total", "Group of Items"].includes(frm.doc.apply_discount_on)) {
			frm.set_df_property("items", "read_only", 1);
		} else {
			frm.set_df_property("items", "read_only", 0);
		};

		if (
			frm.doc.apply_discount_on == "Group of Items" &&
			frm.doc.item_category &&
			frm.doc.sales_invoice
		) {
			frm.clear_table("items");

			let reference_dt = get_reference_doctype(frm.doc.item_category)
			get_items(frm, reference_dt);
		}
	},
	item_category: (frm) => {
		if (
			frm.doc.apply_discount_on == "Group of Items" &&
			frm.doc.item_category &&
			frm.doc.sales_invoice
		) {
			frm.clear_table("items");

			let reference_dt = get_reference_doctype(frm.doc.item_category);
			get_items(frm, reference_dt);
		}
	},
	appointment: (frm) => {
		if (frm.doc.appointment) {
			frm.set_value("sales_invoice", "");
			frm.clear_table("items");
		}
	},
	sales_invoice: (frm) => {
		if (frm.doc.sales_invoice) {
			frm.set_value("appointment", "");
		}
	},
	set_field_properties: (frm) => {
		if (frm.doc.payment_type == "Non NHIF Insurance") {
			frm.set_df_property("apply_discount_on", "options", ["Group of Items"]);
			frm.set_value("apply_discount_on", "Group of Items");
			frm.set_df_property("apply_discount_on", "read_only", 1);
		}
		if (["Grand Total", "Net Total", "Group of Items"].includes(frm.doc.apply_discount_on)) {
			frm.set_df_property("items", "read_only", 1);
		};
	},
});

frappe.ui.form.on("Patient Discount Item", {
	items_add: (frm, cdt, cdn) => {
		if (frm.doc.sales_invoice && !["Grand Total", "Net Total", "Group of Items"].includes(frm.doc.apply_discount_on)) {
			get_items(frm, null, true);
		}
	},
	item_category: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		if (row.item_category && frm.doc.sales_invoice && !["Grand Total", "Net Total", "Group of Items"].includes(frm.doc.apply_discount_on)) {
			get_items(frm, row.item_category, true);
		}
	},
	item_code: (frm, cdt, cdn) => {
		let row = frappe.get_doc(cdt, cdn);
		if (row.item_code && frm.doc.sales_invoice && !["Grand Total", "Net Total", "Group of Items"].includes(frm.doc.apply_discount_on)) {
			get_items_details(frm, row);
		}
	},
});

var get_reference_doctype = (item_category) => {
	let reference_dt = null;
	if (item_category == "All Items") {
		reference_dt = null;
	} else if (item_category == "All Lab Prescriptions") {
		reference_dt = "Lab Prescription";
	} else if (item_category == "All Radiology Procedure Prescription") {
		reference_dt = "Radiology Procedure Prescription";
	} else if (item_category == "All Procedure Prescriptions") {
		reference_dt = "Procedure Prescription";
	} else if (item_category == "All Therapy Plan Details") {
		reference_dt = "Therapy Plan Detail";
	} else if (item_category == "All Drug Prescriptions") {
		reference_dt = "Drug Prescription";
	} else if (item_category == "All OPD Consultation") {
		reference_dt = "Patient Appointment";
	} else if (item_category == "All Other Items") {
		reference_dt = "Other Items";
	}
	return reference_dt;
};

var get_items = (frm, reference_dt, reset_options = null) => {
	frappe.call({
		method: "hms_tz.nhif.doctype.patient_discount_request.patient_discount_request.get_items",
		args: {
			invoice_no: frm.doc.sales_invoice,
			reference_dt: reference_dt,
			reset_options: reset_options,
		}
	}).then((r) => {
		if (r.message) {
			let data = r.message;
			if (data.length > 0) {
				if (!reset_options) {
					data.forEach((row) => {
						let discount_amount = 0;
						if (frm.doc.discount_percent) {
							discount_amount = (row.amount * frm.doc.discount_percent) / 100;
						} else if (frm.doc.discount_amount) {
							discount_amount = frm.doc.discount_amount;
						}
						frm.add_child("items", {
							item_category: row.reference_dt,
							item_code: row.item_code,
							item_name: row.item_name,
							actual_price: row.amount,
							discount_amount: discount_amount,
							amount_after_discount: row.amount - discount_amount,
							si_detail: row.si_detail,
							sales_invoice: row.sales_invoice,
						});
					});
					frm.refresh_field("items");
				} else {
					set_options_for_fields(frm, data, "items");
				}
			}
		} else {
			frappe.show_alert({
				message: __("No items found for the selected Invoice"),
				indicator: "red",
				title: __("Error")
			});
		}
	});
};

var set_options_for_fields = (frm, options, fieldname) => {
	const grid = frm.get_field(fieldname).grid;

	grid.visible_columns = undefined;
	grid.setup_visible_columns();

	grid.fields_map.item_code.options = options;
	grid.refresh();

	frm.get_field(fieldname).grid.grid_rows.forEach(row => {
		row.docfields.forEach(docfield => {
			if (docfield.fieldname === "item_code") {
				docfield.options = options;
			}
		});
	});

	frm.refresh_field(fieldname);
	grid.refresh();
	grid.setup_visible_columns();
};

var get_items_details = (frm, row) => {
	frappe.call({
		method: "hms_tz.nhif.doctype.patient_discount_request.patient_discount_request.get_item_details",
		args: {
			invoice_no: frm.doc.sales_invoice,
			item_category: row.item_category,
			item_code: row.item_code,
		}
	}).then((r) => {
		if (r.message) {
			let data = r.message;
			if (data.length > 0) {
				let discount_amount = 0;
				if (frm.doc.discount_percent) {
					discount_amount = data[0].amount * (frm.doc.discount_percent / 100);
				} else if (frm.doc.discount_amount) {
					discount_amount = frm.doc.discount_amount;
				}
				row.item_name = data[0].item_name;
				row.actual_price = data[0].amount;
				row.discount_amount = discount_amount
				row.amount_after_discount = data[0].amount - discount_amount;
				row.si_detail = data[0].si_detail;
				row.sales_invoice = data[0].sales_invoice;
			}
			if (data.slice(1).length > 0) {
				let additonal_data = data.slice(1);
				additonal_data.forEach((row) => {
					let discount_amount = 0;
					if (frm.doc.discount_percent) {
						discount_amount = (row.amount * frm.doc.discount_percent) / 100;
					} else if (frm.doc.discount_amount) {
						discount_amount = frm.doc.discount_amount;
					}
					frm.add_child("items", {
						item_category: row.reference_dt,
						item_code: row.item_code,
						item_name: row.item_name,
						actual_price: row.amount,
						discount_amount: discount_amount,
						amount_after_discount: row.amount - discount_amount,
						si_detail: row.si_detail,
						sales_invoice: row.sales_invoice,
					});

					frappe.show_alert({
						message: __("Additional items added to the list for same Item Code"),
						indicator: "green",
						title: __("Success")
					});
				});
			}
			frm.refresh_field("items");
		}
	});
};