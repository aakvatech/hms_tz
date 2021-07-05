# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _

def execute(filters=None):
	if not filters:
		filter = {}

	#conditions, filters = get_conditions(filters)

	columns = get_columns()

	data = get_data(filters)
	if not data:
		msgprint(_("No Record Found...!!"))
		return columns, data
	
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "patient",
			"label": _("Patient"),
			"fieldtype": "link",
			"option": "Patient",
			"width": 100
		},
		{
			"fieldname": "patient_name",
			"label": _("Patient Name"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "appointment_created",
			"label": _("Appointment Created"),
			"fieldtype": "Date",
			"width": 100
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
			"width": 100
		},
		{
			"fieldname": "first_encounter_edited",
			"label": _("Practitioner Attends a Patient"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "last_encounter_edited",
			"label": _("Practitioner Ends with Patient"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "card",
			"label": _("Patient Takes Card"),
			"fieldtype": "Date",
			"width": 100
		}
	]



def get_conditions(filters):
	if not (filters.get("from_date") and filters.get("to_date")):
		msgprint(_("Please select From Date and To Date"), raise_exception=1)
	
	conditions = ""
	
	if filters.get("from_date"):
		conditions += " and pa.creation >= %(from_date)s"

	if filters.get("to_date"):
		conditions += " and pa.creation <= %(to_date)s"
	
	return conditions



def get_data(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""select pa.patient as "PATIENT NO:100", pa.patient_name as "PATIENT NAME:100", pa.creation as "APPOINTMENT CREATED:150", 
								vs.creation as "VITALS CREATED:100", vs.modified as "VITALS SUBMITTED:100", 
								min(ver.modified) as "FIRTS TIME DOCTOR ATTENDS A PATIENT:70",  max(ver.modified)  as "LAST TIME DOCTOR TOUCHES THE ENCOUNTER:70", 
								npc.creation as "PATIENT TAKES HIS/HER CARD:70"
								from `tabPatient Appointment`pa  inner join `tabVital Signs` vs on pa.name = vs.appointment
								inner join `tabPatient Encounter` pe on pe.appointment = pa.name
								inner join `tabVersion` ver on pe.name = ver.docname  
								left join `tabNHIF Patient Claim` npc on pe.appointment = npc.patient_appointment
								where pa.status="Closed"
								group by pa.creation order by pa.creation %s """ %
								conditions, filters)


"""
where   pa.creation between %(from_date)s and %(to_date)s
and     pe.creation between %(from_date)s and %(to_date)s
and     ver.creation between %(from_date)s and %(to_date)s
or     npc.creation between %(from_date)s and %(to_date)s

"""