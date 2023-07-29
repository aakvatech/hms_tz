# Copyright (c) 2023, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import nowdate, nowtime, get_fullname, get_url_to_form, flt
from frappe.model.document import Document

class PatientDiscountRequest(Document):
	def before_insert(self):
		self.set_missing_values()

	def after_insert(self):
		if self.sales_invoice:
			invoice_doc = frappe.get_doc("Sales Invoice", self.sales_invoice)
			invoice_doc.hms_tz_discount_requested = 1
			invoice_doc.hms_tz_discount_status = "Pending"
			invoice_doc.save(ignore_permissions=True)

			url = get_url_to_form("Patient Discount Request", self.name)
			invoice_doc.add_comment(
				comment_type="Comment",
				text=f"Patient Discount Request: <b>{invoice_doc.name}<b>\
					was successfully created. <br><br><br>\
					View it here: <a href='{url}'><b>{self.name}</b></a>"
			)
	
	def validate(self):
		self.validate_patient()
		self.get_insurance_details()
		self.set_discount_amount()
	
	def before_submit(self):
		self.approved_by = get_fullname(frappe.session.user)
		self.apply_cash_discount()
	
	def on_submit(self):
		self.apply_insurance_discount()
	
	def set_missing_values(self):
		self.posting_date = nowdate()
		self.posting_time = nowtime()

		inpatient_record = frappe.get_value("Patient", self.patient, "inpatient_record")
		if inpatient_record:
			self.inpatient_record = inpatient_record
		
		self.requested_by = get_fullname(frappe.session.user)

	def validate_patient(self):
		if self.patient:
			if (
				self.sales_invoice and
				self.patient != frappe.db.get_value("Sales Invoice", self.sales_invoice, "patient")
			):
				frappe.throw(f"This sales invoice: {self.sales_invoice} is not for this patient: {self.patient}")
			
			if (
				self.inpatient_record and
				self.patient != frappe.db.get_value("Inpatient Record", self.inpatient_record, "patient")
			):
				frappe.throw(f"This inpatient record: {self.inpatient_record} is not for this patient: {self.patient}")

	def get_insurance_details(self):
		if self.appointment:
			(
				self.insurance_subscription,
				self.insurance_coverage_plan,
				self.insurance_company
			) = frappe.db.get_value(
				"Patient Appointment", self.appointment,
				["insurance_subscription", "coverage_plan_name", "insurance_company_name"]
			)
				
			if not self.insurance_subscription:
				frappe.throw(f"This appointment: {self.appointment} does not have an insurance subscription")

			if "NHIF" in self.insurance_company:
				frappe.throw(
					f"This appointment: <b>{self.appointment}</b> is for NHIF insurance. <br>Note:\
					<br>You can only request discount for Cash and Non NHIF Patients."
				)
	
	def set_discount_amount(self):
		if (
			self.apply_discount_on == "Grand Total"
			and self.sales_invoice
		):
			self.total_actual_amount = frappe.db.get_value("Sales Invoice", self.sales_invoice, "grand_total")
			discount_amount = 0
			if self.discount_percent:
				discount_amount = self.total_actual_amount * (self.discount_percent/100)
			elif self.discount_amount:
				discount_amount = self.discount_amount
			self.total_amount_after_discount = self.total_actual_amount - discount_amount
			self.total_discounted_amount = discount_amount

		elif (
			self.apply_discount_on == "Net Total"
			and self.sales_invoice
		):
			self.total_actual_amount = frappe.db.get_value("Sales Invoice", self.sales_invoice, "net_total")
			discount_amount = 0
			if self.discount_percent:
				discount_amount = self.total_actual_amount * (self.discount_percent/100)
			elif self.discount_amount:
				discount_amount = self.discount_amount
			self.total_amount_after_discount = self.total_actual_amount - discount_amount
			self.total_discounted_amount = discount_amount
		
		elif (
			self.apply_discount_on in ["Single Items", "Group of Items"]
			and self.sales_invoice
			and len(self.items) > 0
		):
			self.total_discounted_amount = 0
			self.total_actual_amount = 0
			self.total_amount_after_discount = 0
			for item in self.items:
				self.total_actual_amount += flt(item.actual_price)
				self.total_amount_after_discount += flt(item.amount_after_discount)
				self.total_discounted_amount += flt(item.discount_amount)

	def apply_cash_discount(self):
		if self.sales_invoice and not self.appointment:
			url  = get_url_to_form("Patient Discount Request", self.name)
			si_doc = frappe.get_doc("Sales Invoice", self.sales_invoice)

			if self.apply_discount_on in ["Grand Total", "Net Total"]:
				si_doc.apply_discount_on = self.apply_discount_on
				si_doc.additional_discount_percent = self.discount_percent if self.discount_percent else 0
				si_doc.discount_amount = self.discount_amount if self.discount_amount else 0

			elif self.apply_discount_on in ["Single Items", "Group of Items"]:
				for item in self.items:
					for row in si_doc.items:
						if item.si_detail == row.name and item.item_code == row.item_code:
							row.discount_percentage = self.discount_percent if self.discount_percent else 0
							row.discount_amount = item.discount_amount if item.discount_amount else 0
			
			si_doc.hms_tz_discount_status = "Approved"
			si_doc.save(ignore_permissions=True)
			si_doc.reload()
			si_doc.add_comment(
				comment_type="Comment",
				text=f"Discount was successfully applied on this Sales Invoice: <b>{si_doc.name}</b><br><br>\
					Please refer to Patient Discount Request: <a href='{url}'><b>{self.name}</b></a> for more details."
			)
			frappe.msgprint(f"Discount applied on Sales Invoice: {self.sales_invoice}", alert=True)

	def apply_insurance_discount(self):
		if self.appointment:
			frappe.enqueue(
				method=equeue_apply_insurance_discount,
				queue='default',
				timeout=100000,
				is_async=True, 
				job_name="apply_insurance_discount",
				kwargs={"self": self}
			)
			frappe.msgprint(
				f"Equeued applying discount for Non NHIF Insurance",
				alert=True
			)

@frappe.whitelist()
def get_item_details(invoice_no, item_category, item_code):
	items = []
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_no)
	for item in invoice_doc.items:
		if item.item_code == item_code:
			items.append({
				"item_category": item_category,
				"item_code": item.item_code,
				"item_name": item.item_name,
				"amount": item.amount,
				"si_detail": item.name,
				"sales_invoice": invoice_no,
			})

	return items

@frappe.whitelist()
def get_items(invoice_no, reference_dt=None, reset_options=None):
	items = []
	item_codes = []
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_no)
	for item in invoice_doc.items:
		if (
			item.reference_dt and
			reference_dt and
			item.reference_dt == reference_dt
		):
			item_codes.append(item.item_code)
			items.append({
				"item_code": item.item_code,
				"item_name": item.item_name,
				"amount": item.amount,
				"reference_dt": item.reference_dt,
				"si_detail": item.name,
				"sales_invoice": invoice_no,
			})
		
		elif (
			not item.reference_dt and
			item.sales_order and
			reference_dt and
			reference_dt == "Drug Prescription"
		):
			item_codes.append(item.item_code)
			items.append({
				"item_code": item.item_code,
				"item_name": item.item_name,
				"amount": item.amount,
				"reference_dt": reference_dt,
				"si_detail": item.name,
				"sales_invoice": invoice_no,
			})

		elif (
			not item.reference_dt and
			not item.sales_order and
			reference_dt == "Other Items"
		):
			item_codes.append(item.item_code)
			items.append({
				"item_code": item.item_code,
				"item_name": item.item_name,
				"amount": item.amount,
				"reference_dt": reference_dt,
				"si_detail": item.name,
				"sales_invoice": invoice_no,
			})
		
		elif not reference_dt:
			item_group = None
			if not item.reference_dt and not item.sales_order:
				item_group = "Other Items"
			elif not item.reference_dt and item.sales_order:
				item_group = "Drug Prescription"

			item_codes.append(item.item_code)
			items.append({
				"item_code": item.item_code,
				"item_name": item.item_name,
				"amount": item.amount,
				"reference_dt": item.reference_dt or item_group,
				"si_detail": item.name,
				"sales_invoice": invoice_no,
			})
	
	if reset_options:
		return item_codes
	return items

def equeue_apply_insurance_discount(kwargs):
	self = kwargs.get("self")
	url  = get_url_to_form("Patient Discount Request", self.name)

	def apply_discount_on_appointment(self, url):
		if not self.appointment:
			return
		
		discount_amount = 0
		appointment_doc = frappe.get_doc("Patient Appointment", self.appointment)
		if self.discount_percent:
			discount_amount = appointment_doc.paid_amount * (self.discount_percent/100)
		elif self.discount_amount:
			discount_amount = self.discount_amount
		
		frappe.db.set_value("Patient Appointment", self.appointment, {
			"paid_amount": appointment_doc.paid_amount - discount_amount,
			"hms_tz_is_discount_applied": 1,
		})

		appointment_doc.add_comment(
			comment_type="Comment",
			text=f"Discount was successfully applied on this Patient Appointment: <b>{appointment_doc.name}</b><br><br>\
				Please refer to Patient Discount Request: <a href='{url}'><b>{self.name}</b></a> for more details."
		)

	def apply_discount_on_encounters(self, url, table_field_to_apply_discount_on=None):
		encounters = frappe.get_all("Patient Encounter", filters={"appointment": self.appointment}, fields=["name"], pluck="name")
		if len(encounters) == 0:
			return
		
		for encounter in encounters:
			encounter_doc = frappe.get_doc("Patient Encounter", encounter)

			for table_field in [
				"lab_test_prescription",
				"radiology_procedure_prescription",
				"procedure_prescription",
				"drug_prescription",
				"therapy_plan_detail",
			]:
				if table_field_to_apply_discount_on and table_field != table_field_to_apply_discount_on:
					continue
				
				if not encounter_doc.get(table_field):
					continue

				for row in encounter_doc.get(table_field):
					if row.hms_tz_is_discount_applied:
						continue

					enc_discount = 0
					if self.discount_percent:
						enc_discount = row.amount * (self.discount_percent/100)
					elif self.discount_amount:
						enc_discount = self.discount_amount
					
					frappe.db.set_value(row.doctype, row.name, {
						"amount": row.amount - enc_discount,
						"hms_tz_is_discount_applied": 1,
					})
			
				encounter_doc.add_comment(
					comment_type="Comment",
					text=f"Discount was successfully applied on this  Patient Encounter: <b>{encounter_doc.name}</b><br><br>\
						Please refer to Patient Discount Request: <a href='{url}'><b>{self.name}</b></a> for more details."
				)

	def apply_discount_on_inpatient(self, url):
		if not self.inpatient_record:
			return
		
		inpatient_record_doc = frappe.get_doc("Inpatient Record", self.inpatient_record)

		discounted_items = []
		for bed in inpatient_record_doc.inpatient_occupancies:
			if bed.hms_tz_is_discount_applied:
				continue

			disocunt_amount = 0
			if self.discount_percent:
				disocunt_amount = bed.amount * (self.discount_percent/100)
			elif self.discount_amount:
				disocunt_amount = self.discount_amount
			
			frappe.db.set_value("Inpatient Occupancy", bed.name, {
				"amount": bed.amount - disocunt_amount,
				"hms_tz_is_discount_applied": 1,
			})

			discounted_items.append(bed.name)
		
		for cons in inpatient_record_doc.consultancy:
			if cons.hms_tz_is_discount_applied:
				continue

			disocunt_amount = 0
			if self.discount_percent:
				disocunt_amount = cons.rate * (self.discount_percent/100)
			elif self.discount_amount:
				disocunt_amount = self.discount_amount
			
			frappe.db.set_value("Inpatient Consultancy", cons.name, {
				"amount": cons.rate - disocunt_amount,
				"hms_tz_is_discount_applied": 1,
			})

			discounted_items.append(cons.name)

		if len(discounted_items) > 0:
			inpatient_record_doc.add_comment(
				comment_type="Comment",
				text=f"Discount was successfully applied on this Inpatient Record: <b>{inpatient_record_doc.name}</b><br><br>\
					Please refer to Patient Discount Request: <a href='{url}'><b>{self.name}</b></a> for more details."
			)
	
	if self.item_category == "All Items":
		apply_discount_on_appointment(self, url)
		apply_discount_on_encounters(self, url)
		apply_discount_on_inpatient(self, url)
	elif self.item_category == "All OPD Consultations":
		apply_discount_on_appointment(self, url)
	elif self.item_category == "All Lab Prescriptions":
		table_field_to_apply_discount_on = "lab_test_prescription"
		apply_discount_on_encounters(self, url, table_field_to_apply_discount_on)
	elif self.item_category == "All Radiology Procedure Prescription":
		table_field_to_apply_discount_on = "radiology_procedure_prescription"
		apply_discount_on_encounters(self, url, table_field_to_apply_discount_on)
	elif self.item_category == "All Procedure Prescriptions":
		table_field_to_apply_discount_on = "procedure_prescription"
		apply_discount_on_encounters(self, url, table_field_to_apply_discount_on)
	elif self.item_category == "All Therapy Plan Details":
		table_field_to_apply_discount_on = "therapy_plan_detail"
		apply_discount_on_encounters(self, url, table_field_to_apply_discount_on)
	elif self.item_category == "All Drug Prescriptions":
		table_field_to_apply_discount_on = "drug_prescription"
		apply_discount_on_encounters(self, url, table_field_to_apply_discount_on)
	elif self.item_category == "All Other Items":
		apply_discount_on_inpatient(self, url)

@frappe.whitelist()
def get_patient_discount_request(data):
	data = frappe.parse_json(data)
	pdr = frappe.new_doc("Patient Discount Request")
	pdr.patient = data.get("patient")
	pdr.customer = data.get("customer")
	pdr.company = data.get("company")
	pdr.payment_type = data.get("payment_type")
	pdr.apply_discount_on = data.get("apply_discount_on")
	pdr.item_category = data.get("item_category")
	pdr.sales_invoice = data.get("sales_invoice")
	pdr.appointment = data.get("appointment")
	pdr.discount_criteria = data.get("discount_criteria")
	pdr.discount_percent = data.get("discount_percent")
	pdr.discount_amount = data.get("discount_amount")
	pdr.reason_for_discount = data.get("reason_for_discount")

	if data.get("items"):
		for item in data.get("items"):
			pdr.append("items", {
				"item_category": item.get("reference_dt"),
				"item_code": item.get("item_code"),
				"actual_price": item.get("actual_price"),
				"discount_amount": item.get("discount_amount"),
				"amount_after_discount": item.get("amount_after_discount"),
				"sales_invoice": item.get("sales_invoice"),
				"si_detail": item.get("si_detail"),
			})
	
	pdr.save(ignore_permissions=True)
	pdr.reload()
	return pdr.name