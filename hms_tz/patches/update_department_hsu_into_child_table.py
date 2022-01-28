import frappe
from frappe.utils import nowdate


def execute():
    today = nowdate()
    encounters = frappe.get_all("Patient Encounter", {"encounter_date": ["<=", today]}, ["name"], pluck="name")

    frappe.db.sql("""
        UPDATE `tabLab Prescription` l
        INNER JOIN `tabLab Test Template` lab ON l.lab_test_code = lab.name AND lab.disabled = 0
        INNER JOIN `Healthcare Company Option` lab_hco ON lab.name = lab_hco.parent AND lab_hco.company = pe.company
        SET l.department_hsu = lab_hco.service_unit
        WHERE l.parent IN ({0})
    """.format(tuple(encounters)))


    # frappe.db.sql("""
    #     UPDATE `tabLab Prescription` l, `tabRadiology Procedure Prescription` r,
    #             `tabProcedure Prescription` p, `tabTherapy Plan Detail` t

    #     INNER JOIN `tabPatient Encounter` lab_pe ON l.parent = lab_pe.name 
    #     INNER JOIN `tabPatient Encounter` rad_pe ON r.parent = rad_pe.name
    #     INNER JOIN `tabPatient Encounter` proc_pe ON p.parent = proc_pe.name
    #     INNER JOIN `tabPatient Encounter` tt_pe ON t.parent = tt_pe.name

    #     LEFT JOIN `tabLab Test Template` lab ON l.lab_test_code = lab.name AND lab.disabled = 0
    #     LEFT JOIN `Healthcare Company Option` lab_hco ON lab.name = lab_hco.parent AND lab_hco.company = pe.company

    #     LEFT JOIN `tabRadiology Examination Template` rad ON r.radiology_examination_template = rad.name
    #             AND rad.disabled = 0
    #     LEFT JOIN `Healthcare Company Option` rad_hco ON rad.name = rad_hco.parent AND rad_hco.company = pe.company

    #     LEFT JOIN `tabProcedure Prescription` proc ON p.procedure = proc.name AND proc.disabled = 0
    #     LEFT JOIN `Healthcare Company Option` proc_hco ON proc.name = proc_hco.parent AND proc_hco.company = pe.company

    #     LEFT JOIN `tabTherapy Type` tt ON t.therapy_type = tt.name AND tt.disabled = 0
    #     LEFT JOIN `Healthcare Company Option` tt_hco ON tt.name = tt_hco.parent AND tt_hco.company = pe.company

    #     SET l.department_hsu = lab_hco.service_unit, r.department_hsu = rad_hco.service_unit, 
    #         p.department_hsu = proc_hco.service_unit, t.department_hsu = tt_hco.service_unit
        
    #     WHERE pe.name IN %s
    # """.format(tuple(encounters)))

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