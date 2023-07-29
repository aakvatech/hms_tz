import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    properties = [
        {
            "doctype": "Sales Invoice",
            "fieldname": "apply_discount_on",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice",
            "fieldname": "is_cash_or_non_trade_discount",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice",
            "fieldname": "base_discount_amount",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice",
            "fieldname": "additional_discount_account",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice",
            "fieldname": "additional_discount_percentage",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice",
            "fieldname": "discount_amount",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "margin_type",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "margin_rate_or_amount",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "rate_with_margin",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "discount_percentage",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "discount_amount",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
        {
            "doctype": "Sales Invoice Item",
            "fieldname": "base_rate_with_margin",
            "property": "read_only",
            "value": 1,
            "property_type": "Check"
        },
    ]

    for property in properties:
        make_property_setter(
            property.get("doctype"),
            property.get("fieldname"),
            property.get("property"),
            property.get("value"),
            property.get("property_type"),
            for_doctype=False,
            validate_fields_for_doctype=False
        )