// Copyright (c) 2023, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["NHIF Tracking Claim Change Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company Insurance Setting",
			"reqd": 1,
		},
		{
			"fieldname": "claim_month",
			"label": __("Claim Month"),
			"fieldtype": "Int",
			"reqd": 1,
		},
		{
			"fieldname": "claim_year",
			"label": __("Claim Year"),
			"fieldtype": "Int",
			"reqd": 1,
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["", "Item Replaced", "Item Removed", "Item Cancelled", "Amount Changed", "Item Unconfirmed"],
		},
		{
			"fieldname": "nhif_patient_claim",
			"label": __("NHIF Patient Claim"),
			"fieldtype": "Link",
			"options": "NHIF Patient Claim",
		},
		{
			"fieldname": "claim_submitted_by",
			"label": __("Claim Submitted By"),
			"fieldtype": "Link",
			"options": "User",

		},
	],
	"formatter": (value, row, column, data, default_formatter) => {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == 'status') {
			if (data[column.fieldname] == "Item Replaced") {
				value = `<span class='font-weight-bold text-success'>${value}</span>`;
			}
			else if (data[column.fieldname] == "Item Removed") {
				value = `<span class='font-weight-bold text-danger'>${value}</span>`;
			}
			else if (data[column.fieldname] == "Item Cancelled") {
				value = `<span class='font-weight-bold text-primary'>${value}</span>`;
			}
			else if (data[column.fieldname] == "Amount Changed") {
				value = `<span class='font-weight-bold text-info'>${value}</span>`;
			}
			else if (data[column.fieldname] == "Item Unconfirmed") {
				value = `<span class='font-weight-bold text-secondary'>${value}</span>`;
			}
		}
		return value;
	}
};
