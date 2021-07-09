# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _

def execute(filters=None):
	if not filters:
		filter = {}

	columns = get_columns(filters)

	data = get_data(filters)
	if not data:
		msgprint(_("No Record Found...!!, Please Check Your Date Filters and Try Again...!!"))
		return columns, data
	
	return columns, data

def get_columns(filters):
	return [
		{
			"fieldname": "patient",
			"label": _("Patient"),
			"fieldtype": "link",
			"option": "Patient",
			"width": 150
		},
		{
			"fieldname": "patient_name",
			"label": _("Patient Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "appointment_created",
			"label": _("Appointment Created"),
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "vital_created",
			"label": _("Vital Created"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "vital_submitted",
			"label": _("Vital Submitted"),
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "first_time_encounter_edited",
			"label": _("Practitioner Attends a Patient"),
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "last_time_encounter_edited",
			"label": _("Practitioner Ends with Patient"),
			"fieldtype": "Date",
			"width": 150
		},
		{
			"fieldname": "time_card_taken",
			"label": _("Patient Takes Card"),
			"fieldtype": "Date",
			"width": 150
		}
	]



def get_conditions(filters):
	if not (filters.get("from_date") and filters.get("to_date")):
		msgprint(_("Please select From Date and To Date"), raise_exception=1)
	
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " and appointment_created >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " and time_card_taken <= %(to_date)s"
	
	return conditions



def get_data(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""select pa.patient as patient, pa.patient_name as patient_name, pa.creation as appointment_created, 
								vs.creation as vital_created, vs.modified as vital_submitted, 
								min(ver.modified) as first_time_encounter_edited,  max(ver.modified)  as last_time_encounter_edited, 
								npc.creation as time_card_taken
								from `tabPatient Appointment`pa  inner join `tabVital Signs` vs on pa.name = vs.appointment
								inner join `tabPatient Encounter` pe on pe.appointment = pa.name
								inner join `tabVersion` ver on pe.name = ver.docname  
								left join `tabNHIF Patient Claim` npc on pe.appointment = npc.patient_appointment
								where	pa.status="Closed"
								and 	pa.creation between %(from_date)s and %(to_date)s
								and     pe.creation between %(from_date)s and %(to_date)s
								and     ver.creation between %(from_date)s and %(to_date)s
								or     npc.creation between %(from_date)s and %(to_date)s 
								group by pa.creation order by pa.creation {conditions} """.format(
									conditions = conditions
								), filters, as_dict=1 )