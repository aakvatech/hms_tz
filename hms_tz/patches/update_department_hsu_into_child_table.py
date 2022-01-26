import frappe
from frappe.utils import nowdate


def execute():
    today = nowdate()
    child_fields = [
        {
            "doctype": "Lab Test Template",
            "field": "lab_test_prescription",
            "item": "lab_test_code"
        },
        {
            "doctype": "Radiology Examination Template",
            "field": "radiology_procedure_prescription",
            "item": "radiology_examination_template"
        },
        {
            "doctype": "Clinical Procedure Template",
            "field": "procedure_prescription",
            "item": "procedure"
        },
        {
            "doctype": "Therapy Type",
            "field": "therapies",
            "item": "therapy_type"
        },
    ]

    patient_encounters = frappe.get_all("Patient Encounter", {"encounter_date": ["<=", today]}, ["name"])
    for encounter in patient_encounters:
        encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)
        
        for child in child_fields:
            if encounter_doc.get(child.get("field")):
                for row in encounter_doc.get(child.get("field")):
                    if row.get(child.get("item")) and not row.department_hsu:
                        template = frappe.get_doc(child.get("doctype"), row.get(child.get("item")))
                        for option in template.company_options:
                            if encounter_doc.company == option.company:
                                row.department_hsu = option.service_unit
                                row.db_update()
