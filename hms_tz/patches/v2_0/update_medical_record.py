import frappe
from frappe import msgprint, _
from frappe.utils import cstr


def update_patient_medical_record():

	lab_list = frappe.db.sql("""
		select * from `tabLab Test` where status = "Completed" and custom_result != ''
	""", as_dict=1)

	for entry in lab_list:
		table_row = False
		subject = cstr(entry.lab_test_name)
		if entry.practitioner:
			subject += frappe.bold(_('Healthcare Practitioner: ')) + entry.practitioner + '<br>'
		if entry.normal_test_items:
			item = entry.normal_test_items[0]
			comment = ''
			if item.lab_test_comment:
				comment = str(item.lab_test_comment)
			table_row = frappe.bold(_('Lab Test Conducted: ')) + item.lab_test_name

			if item.lab_test_event:
				table_row += frappe.bold(_('Lab Test Event: ')) + item.lab_test_event

			if item.result_value:
				table_row += ' ' + frappe.bold(_('Lab Test Result: ')) + item.result_value

			if item.normal_range:
				table_row += ' ' + _('Normal Range: ') + item.normal_range
			table_row += ' ' + comment

		elif entry.descriptive_test_items:
			item = entry.descriptive_test_items[0]

			if item.lab_test_particulars and item.result_value:
				table_row = item.lab_test_particulars + ' ' + item.result_value

		elif entry.sensitivity_test_items:
			item = entry.sensitivity_test_items[0]

			if item.antibiotic and item.antibiotic_sensitivity:
				table_row = item.antibiotic + ' ' + item.antibiotic_sensitivity

		if table_row:
			subject += '<br>' + table_row

		if entry.lab_test_comment:
			subject += '<br>' + cstr(entry.lab_test_comment)

		if entry.custom_result:
			subject += '<br>' + cstr(entry.custom_result)

		medical_record = frappe.db.exists('Patient Medical Record', {
		                                  "reference_entrytype": "Lab Test", 'reference_name': entry.name})

		if medical_record:
			frappe.db.set_value('Patient Medical Record',
			                    medical_record[0][0], 'subject', subject)


update_patient_medical_record()