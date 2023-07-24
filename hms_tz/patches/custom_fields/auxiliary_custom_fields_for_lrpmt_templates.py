import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Lab Test Template": [
            {
                "fieldname": "hms_tz_supp_section",
                "label": "Auxiliary/Supplimentary/Additional LRPMT",
                "fieldtype": "Section Break",
                "insert_after": "hms_tz_cash_min_no_of_days_for_prescription",
            },
            {
                "fieldname": "hms_tz_allow_supplimentary_items",
                "label": "Allow Supplimentary Items",
                "fieldtype": "Check",
                "insert_after": "hms_tz_supp_section",
                "description": "if ticked, All Items defined on the table will be added into the bill, when this item is prescribed by practitioner",
            },
            {
                "fieldname": "hms_tz_supplimentary_items",
                "label": "Supplimentary Items",
                "fieldtype": "Table",
                "options": "Healthcare Supplimentary Item",
                "insert_after": "hms_tz_allow_supplimentary_items",
                "depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
                "mandatory_depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
            }
        ],
        "Radiology Examination Template": [
            {
                "fieldname": "hms_tz_supp_section",
                "label": "Auxiliary/Supplimentary/Additional LRPMT",
                "fieldtype": "Section Break",
                "insert_after": "hms_tz_cash_min_no_of_days_for_prescription",
            },
            {
                "fieldname": "hms_tz_allow_supplimentary_items",
                "label": "Allow Supplimentary Items",
                "fieldtype": "Check",
                "insert_after": "hms_tz_supp_section",
                "description": "if ticked, All Items defined on the table will be added into the bill, when this item is prescribed by practitioner",
            },
            {
                "fieldname": "hms_tz_supplimentary_items",
                "label": "Supplimentary Items",
                "fieldtype": "Table",
                "options": "Healthcare Supplimentary Item",
                "insert_after": "hms_tz_allow_supplimentary_items",
                "depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
                "mandatory_depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
            }
        ],
        "Clinical Procedure Template": [
            {
                "fieldname": "hms_tz_supp_section",
                "label": "Auxiliary/Supplimentary/Additional LRPMT",
                "fieldtype": "Section Break",
                "insert_after": "hms_tz_cash_min_no_of_days_for_prescription",
            },
            {
                "fieldname": "hms_tz_allow_supplimentary_items",
                "label": "Allow Supplimentary Items",
                "fieldtype": "Check",
                "insert_after": "hms_tz_supp_section",
                "description": "if ticked, All Items defined on the table will be added into the bill, when this item is prescribed by practitioner",
            },
            {
                "fieldname": "hms_tz_supplimentary_items",
                "label": "Supplimentary Items",
                "fieldtype": "Table",
                "options": "Healthcare Supplimentary Item",
                "insert_after": "hms_tz_allow_supplimentary_items",
                "depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
                "mandatory_depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
            }
        ],
        "Medication": [
            {
                "fieldname": "hms_tz_supp_section",
                "label": "Auxiliary/Supplimentary/Additional LRPMT",
                "fieldtype": "Section Break",
                "insert_after": "hms_tz_cash_min_no_of_days_for_prescription",
            },
            {
                "fieldname": "hms_tz_allow_supplimentary_items",
                "label": "Allow Supplimentary Items",
                "fieldtype": "Check",
                "insert_after": "hms_tz_supp_section",
                "description": "if ticked, All Items defined on the table will be added into the bill, when this item is prescribed by practitioner",
            },
            {
                "fieldname": "hms_tz_supplimentary_items",
                "label": "Supplimentary Items",
                "fieldtype": "Table",
                "options": "Healthcare Supplimentary Item",
                "insert_after": "hms_tz_allow_supplimentary_items",
                "depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
                "mandatory_depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
            }
            
        ],
        "Therapy Type": [
            {
                "fieldname": "hms_tz_supp_section",
                "label": "Auxiliary/Supplimentary/Additional LRPMT",
                "fieldtype": "Section Break",
                "insert_after": "hms_tz_cash_min_no_of_days_for_prescription",
            },
            {
                "fieldname": "hms_tz_allow_supplimentary_items",
                "label": "Allow Supplimentary Items",
                "fieldtype": "Check",
                "insert_after": "hms_tz_supp_section",
                "description": "if ticked, All Items defined on the table will be added into the bill, when this item is prescribed by practitioner",
            },
            {
                "fieldname": "hms_tz_supplimentary_items",
                "label": "Supplimentary Items",
                "fieldtype": "Table",
                "options": "Healthcare Supplimentary Item",
                "insert_after": "hms_tz_allow_supplimentary_items",
                "depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
                "mandatory_depends_on": "eval:doc.hms_tz_allow_supplimentary_items == 1",
            }
        ],
    }

    create_custom_fields(fields, update=True)