import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    for doctype in ["Lab Test", "Clinical Procedure"]:
        make_property_setter(
            doctype=doctype,
            fieldname="insurance_section",
            property="hidden",
            value=0,
            property_type="Check",
            for_doctype=False,
            validate_fields_for_doctype=False
        )

