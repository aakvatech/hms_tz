import frappe
from frappe.utils import nowdate


def execute():
    today = nowdate()
    encounters = frappe.get_all("Patient Encounter", {"encounter_date": ["<=", today]}, ["name"], pluck="name")
 
    frappe.db.sql("""
        UPDATE `tabLab Prescription` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabLab Test Template` template ON lrpt.lab_test_code = template.name AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%frappe.db.escape(tuple(encounters)))


    frappe.db.sql("""
        UPDATE `tabRadiology Procedure Prescription` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabRadiology Examination Template` template ON lrpt.radiology_examination_template = template.name
                AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%frappe.db.escape(tuple(encounters)))


    frappe.db.sql("""
        UPDATE `tabProcedure Prescription` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabClinical Procedure Template` template ON lrpt.procedure = template.name AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%frappe.db.escape(tuple(encounters)))


    frappe.db.sql("""
        UPDATE `tabTherapy Plan Detail` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabTherapy Type` template ON lrpt.therapy_type = template.name AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%frappe.db.escape(tuple(encounters)))

    # child_fields = [
    #     {
    #         "doctype": "Lab Test Template",
    #         "field": "lab_test_prescription",
    #         "item": "lab_test_code"
    #     },
    #     {
    #         "doctype": "Radiology Examination Template",
    #         "field": "radiology_procedure_prescription",
    #         "item": "radiology_examination_template"
    #     },
    #     {
    #         "doctype": "Clinical Procedure Template",
    #         "field": "procedure_prescription",
    #         "item": "procedure"
    #     },
    #     {
    #         "doctype": "Therapy Type",
    #         "field": "therapies",
    #         "item": "therapy_type"
    #     },
    # ]

    # patient_encounters = frappe.get_all("Patient Encounter", {"encounter_date": ["<=", today]}, ["name"])
    # for encounter in patient_encounters:
    #     encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)
        
    #     for child in child_fields:
    #         if encounter_doc.get(child.get("field")):
    #             for row in encounter_doc.get(child.get("field")):
    #                 if row.get(child.get("item")) and not row.department_hsu:
    #                     try:
    #                         template = frappe.get_doc(child.get("doctype"), row.get(child.get("item")))
    #                         if not template.disabled:
    #                             for option in template.company_options:
    #                                 if encounter_doc.company == option.company:
    #                                     row.department_hsu = option.service_unit
    #                                     row.db_update()
                        
    #                     except Exception:
    #                         pass