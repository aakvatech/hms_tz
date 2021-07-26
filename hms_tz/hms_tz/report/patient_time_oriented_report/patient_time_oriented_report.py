# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
import numpy as np
import pandas as pd
import json


def execute(filters=None):
    if not filters:
        filter = {}
    columns = get_columns(filters)
    data = []    

    appointment_details = get_patient_appointment_details(filters)
    vitals_details = get_vital_signs_details(filters)
    encounter_details = get_patient_encounter_datails(filters)

    if not (appointment_details and vitals_details and encounter_details):
        msgprint(
            title = "Notification",
            msg = frappe.bold("No Record Found for the Date Filters You Specified..... Please set Different Date Filters...!!")
        )
    else:
        app_colnames  = [key for key in appointment_details[0].keys()]
        #frappe.msgprint("colnames are: " + str(colnames))

        appointment_data = pd.DataFrame.from_records(appointment_details, columns=app_colnames)
        #frappe.msgprint("dataframe columns are is: " + str(df.values.tolist()))

        vs_colnames = [key for key in vitals_details[0].keys()]
        #frappe.msgprint("colnames are: " + str(vs_colnames))

        vitals_data = pd.DataFrame.from_records(vitals_details, columns=vs_colnames)
        #frappe.msgprint("dataframe columns are is: " + str(vitals_data.values.tolist()))
   
        enc_colnames = [key for key in encounter_details[0].keys()]
        #frappe.msgprint("colnames are: " + str(enc_colnames))

        encounter_data = pd.DataFrame.from_records(encounter_details, columns = enc_colnames)
        #frappe.msgprint("colnames are: " + str(encounter_data))  

        merge_app_vs = pd.merge(appointment_data, vitals_data, how="inner", on=["appointment", "patient", "patient_name"])
        #frappe.msgprint(str(merge_app_vs))
        merge_app_vs_enc = pd.merge(merge_app_vs, encounter_data, how="inner", on=["appointment", "patient", "patient_name"])
        #frappe.msgprint(str(merge_app_vs_enc))


        time_details = pd.pivot_table(
            merge_app_vs_enc, 
            values = ["appointment", "patient", "patient_name", "appointment_created", "vitals_edited", "vitals_submitted",    
                        "first_time_encounter_edited", "last_time_encounter_edited", "time_card_was_taken"],
            index = ["appointment", "patient", "patient_name"],
            fill_value = " ",
            aggfunc = 'first'
        ) 
        #frappe.msgprint(str(time_details)) 

        column_order = ['appointment_created', 'vitals_edited', 'vitals_submitted', 'first_time_encounter_edited', 
                        'last_time_encounter_edited', "time_card_was_taken"]
        
        ordered_time_details = time_details.reindex(column_order, axis=1)
        #frappe.msgprint(str(table3))

        data = ordered_time_details.reset_index().values.tolist()
        #frappe.msgprint(str(data))
    
    return columns, data

def get_columns(filters):
    columns =  [
        {
            "fieldname": "appointment",
            "label": _("AppointmentNo"),
            "fieldtype": "Data",
            "width": 150
        },
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
            "fieldname": "vitals_edited",
            "label": _("Vital Edited"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "vitals_submitted",
            "label": _("Vital Submitted"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "first_time_encounter_edited",
            "label": _("Doctor Attends a Patient"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "last_time_encounter_edited",
            "label": _("Doctor Ends with Patient"),
            "fieldtype": "Date",
            "width": 150
        },
        {
            "fieldname": "time_card_was_taken",
            "label": _("Patient Takes Card"),
            "fieldtype": "Date",
            "width": 150
        }
     ]
    return columns


def get_patient_appointment_details(filters):

    conditions = ""

    if filters.get("from_date"):
        conditions += " and pa.creation >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " and pa.creation <= %(to_date)s"

    return frappe.db.sql("""select pa.name as appointment, pa.patient as patient, pa.patient_name as patient_name, 
        pa.creation as appointment_created
		from `tabPatient Appointment` pa
		where pa.status = "Closed"
		and pa.appointment_type = "Outpatient Visit" {conditions}
		group by pa.name
		""".format(conditions=conditions), filters, as_dict = 1
    )
          

def get_vital_signs_details(filters):

    conditions = ""

    if filters.get("from_date"):
        conditions += " and vs.creation >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " and vs.creation <= %(to_date)s"

    return frappe.db.sql("""
		select vs.appointment as appointment, vs.patient as patient, vs.patient_name as patient_name, 
        if(min(ver.creation) != "", min(ver.creation), vs.creation) as vitals_edited, 
        if(max(ver.creation) != "", max(ver.creation), vs.modified) as vitals_submitted
		from `tabVital Signs` vs inner join `tabVersion` ver on vs.name = ver.docname
		where vs.modified_by = ver.owner
		and vs.docstatus = 1 {conditions}
		group by vs.appointment
		""".format(conditions=conditions), filters, as_dict = 1
    )
        

def get_patient_encounter_datails(filters):
    
    conditions = ""
     
    if filters.get("from_date"):
        conditions += " and pe.creation >= %(from_date)s"

    if filters.get("to_date"):
        conditions += " and pe.creation <= %(to_date)s"
    
    return frappe.db.sql("""
        select pe.appointment as appointment, pe.patient as patient, pe.patient_name as patient_name, 
        min(ver.creation) as first_time_encounter_edited, max(ver.creation) as last_time_encounter_edited, 
        npc.creation as time_card_was_taken
        from `tabPatient Encounter` pe inner join `tabVersion` ver on pe.name = ver.docname
        left join `tabNHIF Patient Claim` npc on pe.appointment = npc.patient_appointment
        where pe.modified_by = ver.owner
        and pe.finalized = 1 {conditions}
        group by pe.appointment
        """.format(conditions=conditions), filters, as_dict = 1
    )

    



