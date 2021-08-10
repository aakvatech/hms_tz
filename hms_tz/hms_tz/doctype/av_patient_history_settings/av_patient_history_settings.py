# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import msgprint, _
from frappe.utils import cstr, cint
from frappe.model.document import Document

class AVPatientHistorySettings(Document):
	def validate(self):
		self.validated_submitable_doctypes()
		self.validate_date_fieldnames()
	
	def validate_submitable_doctypes(self):
		for entry in self.custom_doctypes:
			if not cint(frappe.db.get_value("DocType", entry.document_type, "is_submittable")):
				msg = _("Row #{0}: Document Type {1} is not submittable. ").format(entry.idx, frappe.bold(entry.document_type))
				
				msg += _("Patient Medical Record can only b created for submittable document types.")
				
				frappe.throw(msg)
	
	def validate_date_fielnames(self):
		for entry in self.custom_doctypes:
			field = frappe.get_meta(entry.document_type).get_field(entry.date_fieldname)
			if not field:
				msgprint(_("Row #{0}: No such Field named {1} found in the Document Type {2}.").format(entry.idx,
				frappe.bold(entry.date_fieldname), frappe.bold(entry.document_type)))

			if field.fieldtype not in ["Date", "Datetime"]:
				msgprint(_("Row #{0}: Field {1} in Document Type {2} is not a Date / Datetime field.").format(entry.idx,
				frappe.bold(entry.date_fieldname), frappe.bold(entry.document_type)))
	