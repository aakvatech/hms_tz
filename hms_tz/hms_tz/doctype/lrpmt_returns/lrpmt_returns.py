# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import bold, _
from frappe.model.workflow import apply_workflow
from frappe.utils import nowdate, nowtime, flt
from frappe.model.document import Document

class LRPMTReturns(Document):
	def validate(self):
		set_missing_values(self)
	
	def before_submit(self):
		validate_reason(self)
		validate_drug_row(self)
		cancel_lrpt_doc(self)
		return_drug_item(self)
	
	def on_submit(self):
		get_sales_return(self)

def cancel_lrpt_doc(self):
	prescription_lrpmt = {
		"Lab Test": "Lab Prescription",
		"Radiology Examination": "Radiology Procedure Prescription",
		"Clinical Procedure": "Procedure Prescription"
	}

	for item in self.lrpt_items:
		if item.reference_doctype == "Therapy Plan":
			cancel_tharapy_plan_doc(self.patient, item.reference_docname)
			frappe.db.set_value("Therapy Plan Detail", item.child_name, "is_cancelled", 1)

		else:
			if not item.reference_docname:
				frappe.db.set_value(prescription_lrpmt[item.reference_doctype], item.child_name, "is_cancelled", 1)
				
				continue
			
			doc = frappe.get_doc(item.reference_doctype, item.reference_docname)
		
			if doc.docstatus < 2:
				try:
					apply_workflow(doc, "Not Serviced")
					if doc.meta.get_field("status"):
						doc.status = "Not Serviced"
					doc.save(ignore_permissions=True)
					doc.reload()

					if (
						doc.workflow_state == "Not Serviced" or 
						doc.workflow_state == "Submitted but Not Serviced"
					):
						frappe.db.set_value(prescription_lrpmt[item.reference_doctype], item.child_name, "is_cancelled", 1)
				
				except Exception:
					traceback = frappe.get_traceback()
					frappe.log_error(traceback, str(self.doctype))
					frappe.throw("There was an error while cancelling the Item, check error log for review")

	return self.name

def cancel_tharapy_plan_doc(patient, therapy_plan_id):
	therapy_sessions = frappe.get_all("Therapy Session",
		filters={"patient": patient, "therapy_plan": therapy_plan_id},
		fields=["name"], pluck="name")

	if therapy_sessions:
		for session in therapy_sessions:
			therapy_session_doc = frappe.get_doc("Therapy Session", session)
			
			if  therapy_session_doc.docstatus == 1:
				therapy_session_doc.cancel()
	
	therapy_plan_doc = frappe.get_doc("Therapy Plan", therapy_plan_id)

	for entry in therapy_plan_doc.therapy_plan_details:
		if entry.no_of_sessions:
			entry.no_of_sessions = 0
		if entry.sessions_completed:
			entry.sessions_completed = 0

	therapy_plan_doc.total_sessions = 0
	therapy_plan_doc.total_sessions_completed = 0
	therapy_plan_doc.status = "Not Serviced"
	therapy_plan_doc.save(ignore_permissions=True)
	therapy_plan_doc.reload()

	return therapy_plan_doc.name

def return_drug_item(self):
	if len(self.drug_items) == 0:
		return 
	
	dn_names = get_unique_delivery_notes(self)

	if not dn_names:
		for item in self.drug_items:
			if item.child_name:
				update_drug_prescription(item, item.child_name)

	for dn in dn_names:
		source_doc = frappe.get_doc("Delivery Note", dn.delivery_note_no)

		target_doc = frappe.new_doc("Delivery Note")
		target_doc.customer = source_doc.customer
		if source_doc.medical_department:
			target_doc.medical_department = source_doc.medical_department
		target_doc.healthcare_service_unit = source_doc.healthcare_service_unit
		target_doc.patient = source_doc.patient
		target_doc.patient_name = source_doc.patient_name
		if source_doc.coverage_plan_name:
			target_doc.coverage_plan_name = source_doc.coverage_plan_name
		target_doc.company = source_doc.company
		target_doc.posting_date = nowdate()
		target_doc.posting_time = nowtime()
		if source_doc.form_sales_invoice:
			target_doc.form_sales_invoice = source_doc.form_sales_invoice
		target_doc.is_return = 1
		target_doc.return_against = source_doc.name
		target_doc.reference_doctype = "LRPMT Returns" #source_doc.reference_doctype
		target_doc.reference_name = self.name #source_doc.reference_name
		target_doc.currency = source_doc.currency
		target_doc.conversion_rate = source_doc.conversion_rate
		target_doc.selling_price_list = source_doc.selling_price_list
		target_doc.price_list_currency = source_doc.price_list_currency
		target_doc.plc_conversion_rate = source_doc.plc_conversion_rate
		target_doc.ignore_pricing_rule = 1
		if source_doc.healthcare_practitioner:
			target_doc.healthcare_practitioner = source_doc.healthcare_practitioner
		
		for item in self.drug_items:
			if item.child_name:
				update_drug_prescription(item, item.child_name)
			
			if (
				not item.dn_detail or 
				not item.delivery_note_no or 
				not item.status or 
				item.status == "Draft"
			):
				continue
				
			if dn.delivery_note_no == item.delivery_note_no:
				for dni in source_doc.items:
					if ((item.dn_detail == dni.name) and (item.drug_name == dni.item_code)):
						target_doc.append("items", {
							"item_code": item.drug_name,
							"item_name": item.drug_name,
							"description": dni.description,
							"qty": -1 * flt(item.quantity_to_return or 0),
							"stock_uom": dni.stock_uom,
							"uom": dni.uom,
							"rate": dni.rate,
							"conversion_factor": dni.conversion_factor,
							"warehouse": dni.warehouse,
							"target_warehouse": dni.target_warehouse or "",
							"dn_detail": dni.name,
							"healthcare_service_unit": dni.healthcare_service_unit or "",
							"healthcare_practitioner": dni.healthcare_practitioner or "",
							"department": dni.department,
							"cost_center": dni.cost_center,
							"reference_doctype": dni.reference_doctype,
							"reference_name": dni.reference_name
						})
		target_doc.save(ignore_permissions=True)
		target_doc.submit()
	
	return self.name
	
def update_drug_prescription(item, child_name):
	if (
		not item.dn_detail and
		not item.delivery_note_no and
		not item.status
	):
		frappe.db.set_value("Drug Prescription", child_name, "is_cancelled", 1)

	if (
		item.delivery_note_no and 
		item.status in ["Draft", "Submitted"] or 
		item.dn_detail
	):
		if (item.quantity_prescribed - item.quantity_to_return) == 0:
			item_cancelled = 1
		else:
			item_cancelled = 0

		frappe.db.set_value("Drug Prescription", child_name, {
			"quantity_returned": item.quantity_to_return,
			"delivered_quantity": item.quantity_prescribed - item.quantity_to_return,
			"is_cancelled": item_cancelled
		})

		if (
			item.delivery_note_no and
			item.status == "Draft"
		):
			try:
				dn_doc = frappe.get_doc("Delivery Note", item.delivery_note_no)
				if dn_doc.workflow_state != "Not Serviced":
					apply_workflow(dn_doc, "Not Serviced")
			except Exception:
				frappe.log_error(frappe.get_traceback(), str("Apply workflow error"))
				frappe.throw(str("Apply workflow error, check error log for more details"))

	
def get_sales_return(self):
	conditions = {
		"patient": self.patient,
		"company": self.company,
		"reference_name": self.name,
		"is_return": 1
	}

	returned_delivery_note_nos = frappe.get_all("Delivery Note", filters=conditions, fields=["name"], pluck="name")

	if returned_delivery_note_nos:
		doc = frappe.get_doc("LRPMT Returns", self.name)

		for dn in returned_delivery_note_nos:
			sales_doc = frappe.get_doc("Delivery Note", dn)

			for item in sales_doc.items:
				for dd_n in doc.drug_items:
					if item.item_code == dd_n.drug_name:
						doc.append("sales_items", {
							"drug_name": item.item_code,
							"quantity_prescribed": dd_n.quantity_prescribed,
							"quantity_returned": item.qty,
							"quantity_serviced": flt(dd_n.quantity_prescribed + item.qty),
							"delivery_note_no": dn,
							"dn_detail": item.name,
							"warehouse": item.warehouse,
							"reference_doctype": item.reference_doctype,
							"reference_name": item.reference_name
						})
		doc.save(ignore_permissions=True)
		doc.reload()
		
	return self.name

def validate_reason(self):
	if self.lrpt_items:
		for entry in self.lrpt_items:
			if not entry.reason:
				msg="Reason Field is Empty for Item name: {0}, Row: #{1}, please fill it to proceed"
				frappe.throw(
					title="Notification",
					msg=msg.format(bold(entry.item_name), bold(entry.idx)), 
					exc="Frappe.ValidationError"
				)

def validate_drug_row(self):
	if self.drug_items:
		msg = ""
		for row in self.drug_items:
			msg_print = ""
			if row.quantity_to_return == 0:
				msg_print += "Quantity to return can not be Zero for drug name: {0},\
							Row: #{1}:<br>".format(bold(row.drug_name), bold(row.idx))
			if not row.reason:
				msg_print += "Reason for Return Field can not be Empty for drug name: {0},\
							Row: #{1}:<br>".format(bold(row.drug_name), bold(row.idx))
			if not row.drug_condition:
				msg_print += "Drug Condition Field can not Empty for drug name: {0},\
							Row: #{1}:<br>".format(bold(row.drug_name), bold(row.idx))
		
		msg = msg_print
			
		if msg: 
			frappe.throw(title="Notification", msg=msg, exc="Frappe.ValidationError")

def get_unique_delivery_notes(self):
	return frappe.db.sql("""SELECT DISTINCT(md.delivery_note_no)
		FROM `tabMedication Return` md
		INNER JOIN `tabLRPMT Returns` lrpmt ON lrpmt.name = md.parent
		WHERE md.status NOT IN ("", "Null", "Draft")
		AND md.dn_detail != ""
		AND lrpmt.patient = %s
		AND lrpmt.appointment = %s
		AND lrpmt.name = %s
	"""%(frappe.db.escape(self.patient), frappe.db.escape(self.appointment), frappe.db.escape(self.name)), as_dict=1)
	
@frappe.whitelist()
def get_lrpt_item_list(patient, appointment, company):
	item_list = []
	child_list = get_lrpt_map()

	encounter_list = get_patient_encounters(patient, appointment, company)

	for child in child_list:
		items = frappe.get_all(child["doctype"], 
			filters={"parent": ["in", encounter_list], "is_not_available_inhouse": 0, "is_cancelled": 0},
			fields=child["fields"]
		)
		
		for item in items:
			if item.lab_test_code:
				lab_status = "Submitted"
				if not item.lab_test:
					name = get_refdoc("Lab Prescription", item.lab_test_code, item.parent)
					if name:
						lab_status = 'Draft'
					else:
						lab_status = ""
					
				item_list.append({
					"child_name": item.name,
					"item_name": item.lab_test_code,
					"quantity": 1,
					"encounter_no": item.parent,
					"reference_doctype": "Lab Test",
					"reference_docname": item.lab_test or name,
					"status": lab_status
				})
			
			if item.radiology_examination_template:
				radiology_status = "Submitted"
				if not item.radiology_examination:
					name = get_refdoc("Radiology Procedure Prescription", item.radiology_examination_template, item.parent)
					if name:
						radiology_status = 'Draft'
					else:
						radiology_status = ''

					
				item_list.append({
					"child_name": item.name,
					"item_name": item.radiology_examination_template,
					"quantity": 1,
					"encounter_no": item.parent,
					"reference_doctype": "Radiology Examination",
					"reference_docname": item.radiology_examination or name,
					"status": radiology_status
				})
			
			if item.procedure:
				procedure_status = 'Submitted'
				if not item.clinical_procedure:
					name = get_refdoc("Procedure Prescription", item.procedure, item.parent)
					if name:
						procedure_status = 'Draft'
					else:
						procedure_status = ''

				item_list.append({
					"child_name": item.name,
					"item_name": item.procedure,
					"quantity": 1,
					"encounter_no": item.parent,
					"reference_doctype": "Clinical Procedure",
					"reference_docname": item.clinical_procedure or name,
					"status": procedure_status
				})
			
			# if item.therapy_type:
			# 	therapy_plan = frappe.get_value("Patient Encounter", item.parent, "therapy_plan")
			# 	item_list.append({
			# 		"child_name": item.name,
			# 		"item_name": item.therapy_type,
			# 		"quantity": 1,
			# 		"encounter_no": item.parent,
			# 		"reference_doctype": "Therapy Plan",
			# 		"reference_docname": therapy_plan
			# 	})
	
	return item_list

def get_lrpt_map():
	child_map = [
		{
			"doctype": "Lab Prescription",
			"fields": [
				"name",
				"lab_test_code",
				"lab_test_name",
				"lab_test",
				"parent"
			]
		},
		{
			"doctype": "Radiology Procedure Prescription",
			"fields": [
				"name",
				"radiology_examination_template",
				"radiology_procedure_name",
				"radiology_examination",
				"parent"
			]
		},
		{
			"doctype": "Procedure Prescription",
			"fields": [
				"name",
				"procedure",
				"procedure_name",
				"clinical_procedure",
				"parent"
			]
		},
		# {
		# 	"doctype": "Therapy Plan Detail",
		# 	"fields": [
		# 		"name",
		# 		"therapy_type",
		# 		"parent"
		# 	]
		# }
	]
	return child_map

def get_refdoc(doctype, template, encounter):
	ref_docs = [
		{
			"ref_d": "Lab Test",
			"table": "Lab Prescription",
			"field": "template"
		},
		{
			"ref_d": "Radiology Examination",
			"table": "Radiology Procedure Prescription",
			"field": "radiology_examination_template"
		},
		{
			"ref_d": "Clinical Procedure",
			"table": "Procedure Prescription",
			"field": "procedure_template"
		}
	]

	for refd in ref_docs:
		if refd.get("table") == doctype:
			docname =  frappe.get_value(refd.get("ref_d"), {"ref_doctype": "Patient Encounter",
					"ref_docname": encounter, refd.get("field"): template}, ["name"]
				)
			return docname or ""

def set_missing_values(doc):
	appointment_list = frappe.get_all("Patient Appointment", filters={"patient": doc.patient, "status": "Closed"}, 
		fields=["name", "company"], order_by="appointment_date desc", page_length=1
	)

	if appointment_list:
		if not doc.appointment:
			doc.appointment = appointment_list[0]["name"]
		doc.company = appointment_list[0]["company"]

		record = frappe.get_all("Inpatient Record", 
			filters={"patient": doc.patient, "patient_appointment": appointment_list[0]["name"], "status": "Admitted"}, 
			fields=["name", "status", "admitted_datetime"], page_length=1
		)
		if record:
			if (record[0]["name"] and record[0]["status"] and record[0]["admitted_datetime"]):
				doc.inpatient_record = record[0]["name"]
				doc.status = record[0]["status"]
				doc.admitted_datetime = record[0]["admitted_datetime"]
			else:
				pass
	else:
		frappe.throw(
			title='Notification',
			msg='No any Appointment found for this Patient: {0}-{1}'.format(
				frappe.bold(doc.patient),
				frappe.bold(doc.patient_name)
			)
		)

def get_patient_encounters(patient, appointment, company):
	if (patient and appointment and company):
		conditions = {
			"patient": patient,
			"appointment": appointment,
			"company": company,
			"docstatus": 1
		}

		patient_encounter_List = frappe.get_all("Patient Encounter", filters=conditions, 
			fields=["name"], pluck="name", order_by="encounter_date desc"
		)
		return patient_encounter_List

@frappe.whitelist()
def set_checked_lrpt_items(doc, checked_items):
	doc = frappe.get_doc(json.loads(doc))
	checked_items = json.loads(checked_items)
	
	doc.lrpt_items = []
	
	for checked_item in checked_items:
		item_row = doc.append("lrpt_items", {})
		item_row.item_name = checked_item["item"]
		item_row.quantity = checked_item["quantity"]
		item_row.encounter_no = checked_item["encounter"]
		item_row.reference_doctype = checked_item["reference_doctype"] or ""
		item_row.reference_docname = checked_item["reference_docname"] or ""
		item_row.child_name = checked_item["child_name"]
	doc.save()
	return doc.name

@frappe.whitelist()
def get_drug_item_list(patient, appointment, company):
	drug_list = []
	delivery_note_items = []

	item_list, name_list = get_drugs(patient, appointment, company)

	if name_list:
		delivery_note_items += frappe.get_all("Delivery Note Item", filters={
			"reference_name": ["in", name_list], 
			'reference_doctype': "Drug Prescription", 'docstatus': ['!=', 2]
			}, fields=["name", "parent", "item_code", 'docstatus', 'reference_name', 'si_detail']
		)
	
		si_parent = frappe.get_all('Sales Invoice Item', filters={
				'reference_dn': ['in', name_list],
				'reference_dt': 'Drug Prescription'
			}, fields=['parent'], pluck='parent'
		)
		if si_parent:
			delivery_note_items += frappe.get_all("Delivery Note Item", filters={
				"against_sales_invoice": ["in", si_parent], 'docstatus': ['!=', 2]
				}, fields=["name", "parent", "item_code", 'docstatus', 'reference_name', 'si_detail']
			)

	avoid_duplicate_list = []
	if item_list:
		for item in item_list:
			for delivery_note in delivery_note_items:
				if delivery_note.docstatus == 0:
					status = 'Draft'
				else:
					status = 'Submitted'
				
				if (
					item.dn_detail and
					item.drug_prescription_created == 1 and
					item.dn_detail == delivery_note.name and
					delivery_note.docstatus == 1
				):
					drug_list.append({
						"child_name": item.name,
						"item_name": item.drug_code,
						"quantity": item.quantity - item.quantity_returned,
						"encounter_no": item.parent,
						"delivery_note": delivery_note.parent,
						"dn_detail": item.dn_detail,
						'status': status
					})
					avoid_duplicate_list.append(item.name)
				
				if (
					delivery_note.reference_name and 
					item.name == delivery_note.reference_name and
					item.drug_prescription_created == 1 and
					delivery_note.docstatus == 0 and
					not item.dn_detail and 
					not delivery_note.si_detail
				):					
					drug_list.append({
						"child_name": item.name,
						"item_name": item.drug_code,
						"quantity": item.quantity - item.quantity_returned,
						"encounter_no": item.parent,
						"delivery_note": delivery_note.parent,
						"dn_detail": item.dn_detail or "",
						'status': status
					})
					avoid_duplicate_list.append(item.name)

				if (
					not item.dn_detail and 
					not delivery_note.reference_name and 
					item.drug_prescription_created == 1 and
					delivery_note.si_detail and
					delivery_note.docstatus == 0
				):
					if item.name not in avoid_duplicate_list:
						drug_list.append({
							"child_name": item.name,
							"item_name": item.drug_code,
							"quantity": item.quantity - item.quantity_returned,
							"encounter_no": item.parent,
							"delivery_note": delivery_note.parent,
							"dn_detail": item.dn_detail or "",
							'status': status
						})
						avoid_duplicate_list.append(item.name)

			if item.name not in avoid_duplicate_list:
				drug_list.append({
					"child_name": item.name,
					"item_name": item.drug_code,
					"quantity": item.quantity - item.quantity_returned,
					"encounter_no": item.parent,
					"delivery_note": "",
					"dn_detail": "",
					"status": ""
				})
	
	return drug_list

def get_drugs(patient, appointment, company):
	item_list = []
	name_list = []

	encounter_list = get_patient_encounters(patient, appointment, company)
	drugs = frappe.get_all("Drug Prescription", filters={"parent": ["in", encounter_list], "is_not_available_inhouse": 0, "is_cancelled": 0},
		fields=["name", "drug_code", "quantity", "quantity_returned", "drug_prescription_created", "parent", "dn_detail"]
	)

	for drug in drugs:
		item_list.append(drug)
		name_list.append(drug.name)
	return item_list, name_list

@frappe.whitelist()
def set_checked_drug_items(doc, checked_items):
	doc = frappe.get_doc(json.loads(doc))
	checked_items = json.loads(checked_items)
	
	doc.drug_items = []
	
	for checked_item in checked_items:
		item_row = doc.append("drug_items", {})
		item_row.drug_name = checked_item["item_name"]
		item_row.quantity_prescribed = checked_item["quantity_prescribed"]
		item_row.encounter_no = checked_item["encounter_no"]
		item_row.delivery_note_no = checked_item["delivery_note"] or ""
		item_row.status = checked_item["status"] or ""
		item_row.dn_detail = checked_item["dn_detail"] or ""
		item_row.child_name = checked_item["child_name"]

	doc.save()
	return doc.name
