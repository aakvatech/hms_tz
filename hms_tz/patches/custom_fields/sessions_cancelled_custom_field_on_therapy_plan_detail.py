import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Therapy Plan Detail": [
            {
                "fieldname": "sessions_cancelled",
                "fieldtype": "Int",
                "label": "Sessions Cancelled",
                "insert_after": "no_of_sessions",
                "read_only": 1,
            },
            {
                "fieldname": "therapy_plan_created",
                "fieldtype": "Check",
                "label": "Therapy Plan Created",
                "insert_after": "section_break_20",
                "read_only": 1,
            },
        ],
        "Therapy Plan": [
            {
                "fieldname": "total_sessions_cancelled",
                "fieldtype": "Int",
                "label": "Total Sessions Cancelled",
                "insert_after": "total_sessions",
                "read_only": 1,
            }
        ],
    }

    create_custom_fields(fields, update=True)
