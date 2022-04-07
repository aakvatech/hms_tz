# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _, get_cached_value
from frappe.utils import flt, nowdate
from erpnext.accounts.utils import get_balance_on

def execute(filters=None):
	args = frappe._dict(filters or {})
	
	columns = get_columns()
	ipd_details = get_data(args)
	data = sorted(ipd_details, key=lambda x: x['date'])

	report_summary = get_report_summary(args, data)

	return columns, data, None, None, report_summary

def get_columns():
	columns = [
		{"fieldname": "date", "fieldtype": "Date", "label": _("Date")},
		{"fieldname": "service_unit", "fieldtype": "Data", "label": _("Service Unit")},
		{"fieldname": "service_unit_type", "fieldtype": "Data", "label": _("Service Unit Type")},
		{"fieldname": "inpatient_charges", "fieldtype": "Currency", "label": _("Inpatient Charges")},
		{"fieldname": "total_lab_amount", "fieldtype": "Currency", "label": _("Lab Amount")},
		{"fieldname": "total_radiology_amount", "fieldtype": "Currency", "label": _("Radiology Amount")},
		{"fieldname": "total_procedure_amount", "fieldtype": "Currency", "label": _("Procedure Amount")},
		{"fieldname": "total_drug_amount", "fieldtype": "Currency", "label": _("Medication Amount")},
		{"fieldname": "total_therapy_amount", "fieldtype": "Currency", "label": _("Therapies Amount")},
		{"fieldname": "grand_total", "fieldtype": "Currency", "label": _("Amount Used Per Day")}
	]
	
	return columns

def get_data(args):
	service_list = []

	service_units = get_inpatient_details(args["inpatient_record"])
	encounter_transactions = get_encounter_data(args)

	if not service_list and not encounter_transactions:
		return service_list
	
	if not service_units and encounter_transactions:
		for encounter in encounter_transactions:
			service_list.append({
				"date": encounter["date_per_encounter"],
				"service_unit": "",
				"service_unit_type": "",
				"inpatient_charges": "",
				"total_lab_amount": encounter["lab_amount_per_encounter"],
				"total_radiology_amount": encounter["radiology_amount_per_encounter"],
				"total_procedure_amount": encounter["procedure_amount_per_encounter"],
				"total_drug_amount": encounter["drug_amount_per_encounter"],
				"total_therapy_amount": encounter["therapy_amount_per_encounter"],
				"grand_total": encounter["total_amount_per_encounter"]
			})
	
	if service_units and not encounter_transactions:
		for ipd_item in  service_units:
			service_list.append({
				"date": ipd_item["check_in"],
				"service_unit": ipd_item["service_unit"],
				"service_unit_type": ipd_item["service_unit_type"],
				"inpatient_charges": ipd_item["inpatient_charges"],
				"total_lab_amount": "",
				"total_radiology_amount": "",
				"total_procedure_amount": "",
				"total_drug_amount": "",
				"total_therapy_amount": "",
				"grand_total": ipd_item["inpatient_charges"]
			})
	dates_list = []
	if service_units and encounter_transactions:
		for service in service_units:
			checkin_date = service["check_in"].strftime("%Y-%m-%d")

			for encounter in encounter_transactions:
				encounter_date = encounter["date_per_encounter"].strftime("%Y-%m-%d")
				
				if (
					checkin_date and
					encounter_date and
					(checkin_date == encounter_date)
				):
					service_list.append({
						"date": checkin_date,
						"service_unit": service["service_unit"],
						"service_unit_type": service["service_unit_type"],
						"inpatient_charges": service["inpatient_charges"],
						"total_lab_amount": encounter["lab_amount_per_encounter"],
						"total_radiology_amount": encounter["radiology_amount_per_encounter"],
						"total_procedure_amount": encounter["procedure_amount_per_encounter"],
						"total_drug_amount": encounter["drug_amount_per_encounter"],
						"total_therapy_amount": encounter["therapy_amount_per_encounter"],
						"grand_total": service["inpatient_charges"] + encounter["total_amount_per_encounter"]
					})
				
				if (
					checkin_date and
					encounter_date and
					(checkin_date != encounter_date)
				):
					service_list.append({
						"date": checkin_date,
						"service_unit": service["service_unit"],
						"service_unit_type": service["service_unit_type"],
						"inpatient_charges": service["inpatient_charges"],
						"total_lab_amount": "",
						"total_radiology_amount": "",
						"total_procedure_amount": "",
						"total_drug_amount": "",
						"total_therapy_amount": "",
						"grand_total": service["inpatient_charges"]
					})
					
					if encounter_date not in dates_list:
						service_list.append({
							"date": encounter_date,
							"service_unit": "",
							"service_unit_type": "",
							"inpatient_charges": "",
							"total_lab_amount": encounter["lab_amount_per_encounter"],
							"total_radiology_amount": encounter["radiology_amount_per_encounter"],
							"total_procedure_amount": encounter["procedure_amount_per_encounter"],
							"total_drug_amount": encounter["drug_amount_per_encounter"],
							"total_therapy_amount": encounter["therapy_amount_per_encounter"],
							"grand_total": encounter["total_amount_per_encounter"]
						})
								
				if not checkin_date or not encounter_date:
					service_list.append({
						"date": checkin_date or encounter_date,
						"service_unit": service["service_unit"] or "",
						"service_unit_type": service["service_unit_type"] or "",
						"inpatient_charges": service["inpatient_charges"] or "",
						"total_lab_amount": encounter["lab_amount_per_encounter"] or "",
						"total_radiology_amount": encounter["radiology_amount_per_encounter"] or "",
						"total_procedure_amount": encounter["procedure_amount_per_encounter"] or "",
						"total_drug_amount": encounter["drug_amount_per_encounter"] or "",
						"total_therapy_amount": encounter["therapy_amount_per_encounter"] or "",
						"grand_total": service["inpatient_charges"] or encounter["total_amount_per_encounter"]
					})

				dates_list.append(encounter_date)

	return service_list

def get_encounter_data(args):
	encounter_services = []

	encounter_list = frappe.get_all("Patient Encounter", filters=[
			["appointment", "=", args.appointment_no], ["company", "=", args.company],
			["inpatient_record", "=", args.inpatient_record], ["patient", "=", args.patient],
			["docstatus", "=", 1]
		], fields=["name", "encounter_date"], order_by = "encounter_date desc"
	)
	
	if not encounter_list:
		return encounter_services
	
	encounter_date_list = []
	one_encounter_per_day = []
	multiple_encounter_per_day = []

	for enc in encounter_list:
		total_amount = lab_amount = radiology_amount = 0
		procedure_amount = drug_amount = therapy_amount = 0

		lab_transactions = frappe.get_all("Lab Prescription", 
			filters={"prescribe": 1, "is_not_available_inhouse": 0, "is_cancelled": 0,
			"invoiced": 0, "parent": enc.name}, fields=["amount"]
		)
		
		for lab in lab_transactions:
			lab_amount += lab.amount

		radiology_transactions = frappe.get_all("Radiology Procedure Prescription",
			filters={"prescribe": 1, "is_not_available_inhouse": 0, "is_cancelled": 0,
			"invoiced": 0, "parent": enc.name}, fields=["amount"]
		)
		for radiology in radiology_transactions:
			radiology_amount += radiology.amount

		procedure_transactions = frappe.get_list("Procedure Prescription", 
			filters={"prescribe": 1, "is_not_available_inhouse": 0, "is_cancelled": 0,
			"invoiced": 0, "parent": enc.name}, fields=["amount"]
		)
		for procedure in procedure_transactions:
			procedure_amount += procedure.amount

		drug_transactions = frappe.get_all("Drug Prescription", 
			filters={"prescribe": 1, "is_not_available_inhouse": 0, "is_cancelled": 0,
			"invoiced": 0, "parent": enc.name},
			fields=["quantity", "quantity_returned", "amount"]
		)
		for drug in drug_transactions:
			amount = (drug.quantity - drug.quantity_returned) * drug.amount
			drug_amount += amount

		therapy_transactions = frappe.get_all("Therapy Plan Detail", 
			filters={"prescribe": 1, "is_not_available_inhouse": 0, "is_cancelled": 0, "parent": enc.name},
			fields=["amount"]
		)
		for therapy in therapy_transactions:
			therapy_amount += therapy.amount
	
		total_amount += lab_amount + radiology_amount + procedure_amount + drug_amount + therapy_amount
		
		if enc.encounter_date not in encounter_date_list:
			encounter_date_list.append(enc.encounter_date)
			one_encounter_per_day.append({
				"date_per_encounter": enc.encounter_date,
				"lab_amount_per_encounter": lab_amount,
				"radiology_amount_per_encounter": radiology_amount,
				"procedure_amount_per_encounter": procedure_amount,
				"drug_amount_per_encounter": drug_amount,
				"therapy_amount_per_encounter": therapy_amount,
				"total_amount_per_encounter": total_amount
			})

		else:
			multiple_encounter_per_day.append({
				"date_per_encounter": enc.encounter_date,
				"lab_amount_per_encounter": lab_amount,
				"radiology_amount_per_encounter": radiology_amount,
				"procedure_amount_per_encounter": procedure_amount,
				"drug_amount_per_encounter": drug_amount,
				"therapy_amount_per_encounter": therapy_amount,
				"total_amount_per_encounter": total_amount
			})
	
	return get_grouped_encounter_detals(one_encounter_per_day, multiple_encounter_per_day)

def get_grouped_encounter_detals(one_encounter_per_day, multiple_encounter_per_day):
	grouped_service_list = []
	for enc_service in one_encounter_per_day:
		total_amount = lab_amount = radiology_amount = 0
		procedure_amount = drug_amount = therapy_amount = 0

		for enc_item in multiple_encounter_per_day:
			if (
				enc_service["date_per_encounter"] and
				enc_item["date_per_encounter"] and 
				(enc_service["date_per_encounter"] == enc_item["date_per_encounter"])
			):
				lab_amount += flt(enc_item["lab_amount_per_encounter"])
				radiology_amount += flt(enc_item["radiology_amount_per_encounter"])
				procedure_amount += flt(enc_item["procedure_amount_per_encounter"])
				drug_amount += flt(enc_item["drug_amount_per_encounter"])
				therapy_amount += flt(enc_item["therapy_amount_per_encounter"])
				total_amount += flt(enc_item["total_amount_per_encounter"])
		
		enc_service.update({
			"lab_amount_per_encounter": flt(enc_service["lab_amount_per_encounter"]) + lab_amount,
			"radiology_amount_per_encounter": flt(enc_service["radiology_amount_per_encounter"]) + radiology_amount,
			"procedure_amount_per_encounter": flt(enc_service["procedure_amount_per_encounter"]) + procedure_amount,
			"drug_amount_per_encounter": flt(enc_service["drug_amount_per_encounter"]) + drug_amount,
			"therapy_amount_per_encounter": flt(enc_service["therapy_amount_per_encounter"]) + therapy_amount,
			"total_amount_per_encounter": flt(enc_service["total_amount_per_encounter"]) + total_amount
		})
		
		grouped_service_list.append(enc_service)
	
	return grouped_service_list

def get_inpatient_details(inpatient_record):
	inpatient_list = []	

	bed_details = get_occupancy_details(inpatient_record)
	cons_details = get_consultancy_details(inpatient_record)

	if not bed_details and not cons_details:
		return inpatient_list
	
	if not bed_details and cons_details:
		for cons in cons_details:
			inpatient_list.append({
				"check_in": cons.date,
				"service_unit": "",
				"service_unit_type": "",
				"inpatient_charges": cons.rate
			})
		return inpatient_list
	
	if bed_details and not cons_details:
		for bed in bed_details:
			inpatient_list.append({
			"check_in": bed.check_in,
			"service_unit": bed.service_unit,
			"service_unit_type": bed.service_unit_type,
			"inpatient_charges": bed.amount
		})
		return inpatient_list
	
	if bed_details and cons_details:
		for bed in bed_details:
			inpatient_record_charges, inpatient_record_costs = 0, 0
			
			for cons in cons_details:
				if bed.check_in == cons.date:
					inpatient_record_charges += bed.amount + cons.rate
				
				if bed.check_in != cons.date:
					inpatient_record_costs += bed.amount or cons.rate
			
			inpatient_list.append({
				"check_in": bed.check_in,
				"service_unit": bed.service_unit,
				"service_unit_type": bed.service_unit_type,
				"inpatient_charges": inpatient_record_charges or inpatient_record_costs
			})
		
		return inpatient_list

def get_consultancy_details(inpatient_record):
	date_list = []
	cons_list = []
	consultancy_list = []
	duplicated_date_list = []
	
	consultancies = frappe.get_all("Inpatient Consultancy", 
		filters={"parent": inpatient_record,"is_confirmed": 1, "hms_tz_invoiced": 0},
        fields=["date", "rate"], order_by="date ASC"
    )

	if not consultancies:
		return consultancy_list

	for cons in consultancies:
		if cons.date not in date_list:
			date_list.append(cons.date)
			cons_list.append(cons)
		else:
			duplicated_date_list.append(cons)
	
	for item in cons_list:
		rate = 0
		if duplicated_date_list:
			for d in duplicated_date_list:
				if item.date == d.date:
					rate += d.rate
		item.update({
			"rate": flt(item.rate) + rate
		})
		consultancy_list.append(item)
	
	return consultancy_list

def get_occupancy_details(inpatient_record):
	unit_list = []

	service_unit_details = frappe.db.sql("""
        SELECT io.service_unit, Date(io.check_in) AS check_in, io.amount AS amount, 
                hsu.service_unit_type
        FROM `tabInpatient Occupancy` io
        INNER JOIN `tabHealthcare Service Unit` hsu ON io.service_unit = hsu.name
        WHERE io.is_confirmed = 1
		AND io.invoiced = 0
        AND io.parent = %s
        ORDER BY io.check_in ASC
    """%frappe.db.escape(inpatient_record), as_dict=1)

	checkin_list = []
	occupancy_list = []
	duplicated_checkin_list = []
	for unit in service_unit_details:
		if unit.check_in not in checkin_list:
			checkin_list.append(unit.check_in)
			occupancy_list.append(unit)
		else:
			duplicated_checkin_list.append(unit)

	for service in occupancy_list:
		d_amount = 0
		if duplicated_checkin_list:
			for d in duplicated_checkin_list:
				if service.check_in == d.check_in:
					d_amount += d.amount
        
		service.update({
            "amount": flt(service.amount) + d_amount
        })
		unit_list.append(service)
	return unit_list

def get_patient_balance(patient, company):
	customer = frappe.get_value("Patient", {"name": patient}, ["customer"])

	balance = get_balance_on(party_type="Customer", party=customer, company=company)

	return balance

def get_report_summary(args, summary_data):

	deposit_balance = get_patient_balance(args.patient, args.company)

	total_amount = 0
	for entry in summary_data:
		total_amount += entry["grand_total"]

	balance = (-1 * deposit_balance)

	current_balance = balance - total_amount

	currency = frappe.get_cached_value("Company", args.company, "default_currency")

	return [
		{
			"value": balance,
			"label": _("Total Deposited Amount"),
			"datatype": "Currency",
			"currency": currency
		},
		{
			"value": total_amount,
			"label": _("Total Amount Used"),
			"datatype": "Currency",
			"currency": currency
		},
		{
			"value": current_balance,
			"label": _("Current Balance"),
			"datatype": "Currency",
			"currency": currency
		}
	]