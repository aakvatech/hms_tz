import frappe

def execute():
    properties = [
        {"fieldname": "card_no","property": "in_global_search"},
        {"fieldname": "patient_name","property": "in_global_search"},
        {"fieldname": "dob", "property": "reqd"},
    ]
    for d in properties:
        d.update({
            "doctype": "Patient",
            "doctype_or_field": "DocField",
            "row_name": None,"value": 1, 
            "property_type": "Check"
        })
        frappe.make_property_setter(d)