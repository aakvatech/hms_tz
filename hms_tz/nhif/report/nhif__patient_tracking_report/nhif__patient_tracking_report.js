// Copyright (c) 2022, Aakvatech and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["NHIF  Patient Tracking Report"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "status",
			"fieldtype": "Select",
			"label": __("Status"),
			"options": ["", "Open", "Closed"],
			"default": "",
			"reqd": 0,
		}
	]
};
