import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Delivery Note": [
            dict(
                fieldname="hms_tz_lrpmt_returns",
                fieldtype="Button",
                label="LRPMT Returns",
                insert_after="set_target_warehouse"
            ),
            dict(
                fieldname="hms_tz_medicatiion_change_request",
                fieldtype="Button",
                label="Medicatiion Change Request",
                insert_after="hms_tz_lrpmt_returns",
                depends_on="eval: doc.docstatus == 0"
            ),
        ]
    }

    create_custom_fields(fields, update=True)