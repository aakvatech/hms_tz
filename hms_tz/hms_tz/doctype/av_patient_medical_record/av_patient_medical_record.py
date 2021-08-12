# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AVPatientMedicalRecord(Document):
	def after_insert(self):
		if self.reference_doctype == "AV Patient Medical Record":
			frappe.db.set_value("AV Patient Medical Record", self.name, "reference_name", self.name)
