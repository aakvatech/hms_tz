import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        'Patient Encounter': [dict(fieldname='hms_tz_convert_to_inpatient', label='Convert to Inpatient',
                    fieldtype='Button', insert_after='medical_department', bold=1, permlevel=3 )],
        'Healthcare Insurance Company': [dict(fieldname='disabled', label='Disabled', fieldtype='Check',
                    insert_after='default_price_list', bold=1)]
    }
    create_custom_fields(fields, update=True)

    examination_field = frappe.get_doc('Custom Field', 'Patient Encounter-examination_detail')
    examination_field.mandatory_depends_on = "eval:!doc.practitioner.includes ('Direct')"
    examination_field.save(ignore_permissions=True)

    cash_limit_field = frappe.get_doc('Custom Field', 'Inpatient Record-cash_limit')
    cash_limit_field.fetch_if_empty = 1
    cash_limit_field.save(ignore_permissions=True)
    