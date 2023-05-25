import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Healthcare Settings": [
            {
                "fieldname": "enable_auto_quantity_calculation",
                "label": "Enable Auto Quantity Calculation in Patient Encounter",
                "fieldtype": "Check",
                "insert_after": "default_medical_code_standard",
                "bold": 1,
                "description": "If checked, system will auto calculate quantity of drugs based on the dosage, period, interval and interval uom of drugs prescribed in patient encounter."
            }
        ]
    }

    create_custom_fields(fields, update=True)