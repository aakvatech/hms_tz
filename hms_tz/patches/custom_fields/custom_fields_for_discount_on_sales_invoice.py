import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Sales Invoice": [
            {
                "fieldname": "hms_tz_request_discount",
                "label": "Request Discount",
                "fieldtype": "Button",
                "insert_after": "column_break_51",
                "depends_on": "eval:doc.hms_tz_discount_requested == 0"
            },
            {
                "fieldname": "hms_tz_discount_requested",
                "label": "Discount Requested",
                "fieldtype": "Check",
                "insert_after": "hms_tz_request_discount",
                "read_only": 1
            },
            {
                "fieldname": "hms_tz_discount_status",
                "label": "Discount Status",
                "fieldtype": "Select",
                "insert_after": "hms_tz_discount_requested",
                "options": "\nPending\nApproved\nRejected",
                "read_only": 1
            },
        ],
    }

    create_custom_fields(fields, update=True)