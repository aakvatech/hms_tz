import frappe

def execute():
    frappe.get_doc({
        "doctype":"Custom Field",
        "name":"Delivery Note-hms_tz_is_all_items_out_of_stock",
        "dt":"Delivery Note",
        "label":"Is All Items Out of Stock",
        "fieldname":"hms_tz_is_all_items_out_of_stock",
        "insert_after":"authorization_number",
        "fieldtype":"Check",
        "read_only":1,
        "hidden":1
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype":"Custom Field",
        "name":"Delivery Note Item-hms_tz_is_out_of_stock",
        "dt":"Delivery Note Item",
        "label":"Is Out of Stock",
        "fieldname":"hms_tz_is_out_of_stock",
        "insert_after":"customer_item_code",
        "fieldtype":"Check",
        "bold":1
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype":"Custom Field",
        "name":"Delivery Note-original_prescription",
        "dt":"Delivery Note",
        "label":"Original Prescription",
        "fieldname":"original_prescription",
        "insert_after":"items",
        "fieldtype":"Section Break",
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype":"Custom Field",
        "name":"Delivery Note-hms_tz_original_items",
        "dt":"Delivery Note",
        "label":"Original Items",
        "fieldname":"hms_tz_original_items",
        "insert_after":"original_prescription",
        "fieldtype":"Table",
        "options":"Original Delivery Note Item",
        "read_only":1
    }).insert(ignore_permissions=True)

    is_not_available_inhouse = frappe.get_doc('Custom FIeld', 'Drug Prescription-is_not_available_inhouse')
    is_not_available_inhouse.allow_on_submit = 1
    is_not_available_inhouse.bold = 1
    is_not_available_inhouse.save(ignore_permissions=True)

    frappe.get_doc({
        "doctype":"Custom Field",
        "name":"Drug Prescription-hms_tz_is_out_of_stock",
        "dt":"Drug Prescription",
        "label":"Is Out of Stock",
        "fieldname":"hms_tz_is_out_of_stock",
        "insert_after":"is_not_available_inhouse",
        "fieldtype":"Check",
        "read_only":1,
        "allow_on_submit":1,
        "bold":1
    }).insert(ignore_permissions=True)