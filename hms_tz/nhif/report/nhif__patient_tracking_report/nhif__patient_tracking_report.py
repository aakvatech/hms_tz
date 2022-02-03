# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		return
		
	appointment_nos, appointments = get_appointment_details(filters)

	columns = get_columns()
	data = get_data(filters, appointment_nos, appointments)
		
	return columns, data

def get_columns():
	return [
		{"fieldname": "patient", "label": _("Patient"), "fieldtype": "Data"},
		{"fieldname": "patient_name", "label": _("Patient Name"), "fieldtype": "Data"},
		{"fieldname": "appointment_no", "label": _("AppointmentNo"), "fieldtype": "Data"},
		{"fieldname": "appointment_status", "label": _("Appointment Status"), "fieldtype": "Data"},
		{"fieldname": "encounter", "label": _("Final Encounter"), "fieldtype": "Data"},
		{"fieldname": "encounter_status", "label": _("Status of Final Encounter"), "fieldtype": "Data"},
		{"fieldname": "nhif_claim_no", "label": _("NHIF Patient Claim"), "fieldtype": "Data"},
		{"fieldname": "signature", "label": _("Signature Captured"), "fieldtype": "Data"},
	]

def get_data(filters, appointment_nos, appointments):
	nhif_records = []
	patient_details = get_encounter_details(filters, appointment_nos, appointments)

	nhif_claims = frappe.get_all("NHIF Patient Claim",
		filters={"patient_appointment": ["in", appointment_nos], "company": filters.company},
		fields=["patient_appointment", "patient", "name", "patient_signature"], order_by="attendance_date"
	)
	if not nhif_claims:
		return patient_details
	
	for d in patient_details:
		for claim in nhif_claims:
			if (
				d["appointment_no"] == claim["patient_appointment"] and 
				d["patient"] == claim["patient"]
			):
				if claim["patient_signature"]:
					signature = "Yes"
				else:
					signature = ""
				
				nhif_records.append({
					"patient": d["patient"],
					"patient_name": d["patient_name"],
					"appointment_no": d["appointment_no"],
					"appointment_status": d["appointment_status"],
					"encounter": d["encounter"],
					"encounter_status": d["encounter_status"],
					"nhif_claim_no": claim["name"],
					"signature": signature
				})

			if (
				d["appointment_no"] and 
				not claim["patient_appointment"]
			):
				nhif_records.append({
					"patient": d["patient"],
					"patient_name": d["patient_name"],
					"appointment_no": d["appointment_no"],
					"appointment_status": d["appointment_status"],
					"encounter": d["encounter"],
					"encounter_status": d["encounter_status"]
				})
	
	return nhif_records

def get_encounter_details(filters, appointment_nos, appointments):
	encounters = frappe.get_all("Patient Encounter", 
		filters={"appointment": ["in", appointment_nos], "company": filters.company, "duplicated": 0,
		"insurance_company": "NHIF"}, fields=["appointment", "patient", "name", "docstatus"],
		order_by="encounter_date"
	)

	if not encounters:		
		return appointments

	encounter_details = []
	for appointment in appointments:
		for enc in encounters:
			if (
				appointment["appointment_no"] == enc["appointment"] and 
				appointment["patient"] == enc["patient"]
			):
				status = ""
				if enc["docstatus"] == 0:
					status += "Draft"
				if enc["docstatus"] == 1:
					status += "Submitted"
				if enc["docstatus"] == 2:
					status += "Cancelled"

				appointment.update({
					"encounter": enc["name"],
					"encounter_status": status
				})
				encounter_details.append(appointment)

			if (
				appointment["appointment_no"] and
				not enc["appointment"]
			):
				frappe.msgprint("Hello")
				appointment.update({
					"encounter": "",
					"encounter_status": ""
				})
				encounter_details.append(appointment)
	frappe.msgprint(str(encounter_details))
	
	return encounter_details

def get_appointment_details(filters):
	name_list = []
	appointment_list = []
	
	conditions = get_conditions(filters)
	
	appointments = frappe.get_all("Patient Appointment", filters=conditions,
		fields=["name", "patient", "patient_name", "status"], order_by="appointment_date"
	)

	if not appointments:
		frappe.throw("No Appointment(s) Found for the filters: #{0}, #{1} and #{2}".format(
			frappe.bold(filters.date),
			frappe.bold(filters.company),
			frappe.bold(filters.status)
		))
	
	for pa in appointments:
		name_list.append(pa["name"])
		appointment_list.append({
			"patient": pa["patient"],
			"patient_name": pa["patient_name"],
			"appointment_no": pa["name"],
			"appointment_status": pa["status"]
		})

	return name_list, appointment_list

def get_conditions(filters):
	if filters:
		conditions = {}
		if filters.date:
			conditions["appointment_date"] = filters.date
		if filters.company:
			conditions["company"] = filters.company
			conditions["insurance_company"] = "NHIF"
		if filters.status == "Open":
			conditions["status"] = "Open"
		if filters.status == "Closed":
			conditions["status"] = "Closed"

		return conditions