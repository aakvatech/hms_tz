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
    """%(", ".join(["%s"] * len(encounters))),  tuple([d for d in encounters]))


    frappe.db.sql("""
        UPDATE `tabRadiology Procedure Prescription` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabRadiology Examination Template` template ON lrpt.radiology_examination_template = template.name
                AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%(", ".join(["%s"] * len(encounters))),  tuple([d for d in encounters]))


    frappe.db.sql("""
        UPDATE `tabProcedure Prescription` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabClinical Procedure Template` template ON lrpt.procedure = template.name AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%(", ".join(["%s"] * len(encounters))),  tuple([d for d in encounters]))


    frappe.db.sql("""
        UPDATE `tabTherapy Plan Detail` lrpt
        INNER JOIN `tabPatient Encounter` pe ON lrpt.parent = pe.name
        INNER JOIN `tabTherapy Type` template ON lrpt.therapy_type = template.name AND template.disabled = 0
        INNER JOIN `tabHealthcare Company Option` hco ON template.name = hco.parent AND hco.company = pe.company
        SET lrpt.department_hsu = hco.service_unit
        WHERE pe.name IN (%s)
    """%(", ".join(["%s"] * len(encounters))),  tuple([d for d in encounters]))

    frappe.db.commit()
