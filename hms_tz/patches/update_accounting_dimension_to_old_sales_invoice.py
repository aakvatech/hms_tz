import frappe

def execute():
    refdocs = [
        "Lab Prescription",
        "Radiology Procedure Prescription",
        "Procedure Prescription",
        "Therapy Plan Detail"
    ]
    sii_items = frappe.get_all("Sales Invoice Item", 
        filters={"reference_dt": ["in", refdocs], "reference_dn": ["!=", ""],
        "healthcare_service_unit": "", "healthcare_practitioner": "" },
        fields=["name"], pluck="name"
    )

    frappe.db.sql("""
        UPDATE `tabSales Invoice Item` sii
        INNER JOIN `tabLab Prescription` lrpt ON sii.reference_dn = lrpt.name
            AND sii.reference_dt = "Lab Prescription"
        INNER JOIN  `tabPatient Encounter` pe ON lrpt.parent = pe.name
        SET sii.healthcare_service_unit = lrpt.department_hsu,
            sii.healthcare_practitioner = pe.practitioner
        WHERE sii.name IN (%s)
    """%(", ".join(["%s"] * len(sii_items))), tuple([d for d in sii_items])
    )

    frappe.db.sql("""
        UPDATE `tabSales Invoice Item` sii
        INNER JOIN `tabRadiology Procedure Prescription` lrpt ON sii.reference_dn = lrpt.name
            AND sii.reference_dt = "Radiology Procedure Prescription"
        INNER JOIN  `tabPatient Encounter` pe ON lrpt.parent = pe.name
        SET sii.healthcare_service_unit = lrpt.department_hsu,
            sii.healthcare_practitioner = pe.practitioner
        WHERE sii.name IN (%s)
    """%(", ".join(["%s"] * len(sii_items))), tuple([d for d in sii_items])
    )

    frappe.db.sql("""
        UPDATE `tabSales Invoice Item` sii
        INNER JOIN `tabProcedure Prescription` lrpt ON sii.reference_dn = lrpt.name
            AND sii.reference_dt = "Procedure Prescription"
        INNER JOIN  `tabPatient Encounter` pe ON lrpt.parent = pe.name
        SET sii.healthcare_service_unit = lrpt.department_hsu,
            sii.healthcare_practitioner = pe.practitioner
        WHERE sii.name IN (%s)
    """%(", ".join(["%s"] * len(sii_items))), tuple([d for d in sii_items])
    )

    frappe.db.sql("""
        UPDATE `tabSales Invoice Item` sii
        INNER JOIN `tabTherapy Plan Detail` lrpt ON sii.reference_dn = lrpt.name
            AND sii.reference_dt = "Therapy Plan Detail"
        INNER JOIN  `tabPatient Encounter` pe ON lrpt.parent = pe.name
        SET sii.healthcare_service_unit = lrpt.department_hsu,
            sii.healthcare_practitioner = pe.practitioner
        WHERE sii.name IN (%s)
    """%(", ".join(["%s"] * len(sii_items))), tuple([d for d in sii_items])
    )

    frappe.db.commit()