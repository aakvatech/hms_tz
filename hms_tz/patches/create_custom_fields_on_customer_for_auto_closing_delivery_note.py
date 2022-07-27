from turtle import update
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Customer": [
            dict(
                fieldname="hms_tz_closing_dn_section_break",
                fieldtype="Section Break",
                label="Auto Closing Delivery Note",
                insert_after="companies",
            ),
            dict(
                fieldname="hms_tz_is_dn_outo_closed",
                fieldtype="Check",
                label="Is DN Auto Closed",
                insert_after="hms_tz_closing_dn_section_break",
                bold=1
            ),
            dict(
                fieldname="hms_tz_dn_closed_after",
                fieldtype="Int",
                label="DN Closed after",
                insert_after="hms_tz_is_dn_outo_closed",
                description="Delivery notes for this customer will automatically be closed after days specified at this field",
                mandatory_depends_on="eval: doc.hms_tz_is_dn_outo_closed == 1"
            ),
        ]
    }

    create_custom_fields(fields, update=True)