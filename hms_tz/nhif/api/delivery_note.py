from __future__ import unicode_literals
import frappe
from frappe import _
from hms_tz.nhif.api.healthcare_utils import update_dimensions
from frappe.model.naming import set_new_name
import json


def validate(doc, method):
    if doc.docstatus != 0:
        return
    set_prescribed(doc)
    set_missing_values(doc)
    check_item_for_out_of_stock(doc)
    update_dimensions(doc)


def after_insert(doc, method):
    set_original_item(doc)


def set_original_item(doc):
    for item in doc.items:
        if item.item_code:
            item.original_item = item.item_code
            item.original_stock_uom_qty = item.stock_qty
        
        new_row = item.as_dict()
        new_row.update({
            'name': None,
            'owner': None,
            'creation': None,
            'modified': None,
            'modified_by': None,
            'docstatus': None,
            'dn_detail': item.name,
            'parent': doc.name,
            'parentfield': 'hms_tz_original_items',
            'parenttype': 'Delivery Note',
            'doctype': 'Original Delivery Note Item'
        })
        doc.append('hms_tz_original_items', new_row)
    doc.save(ignore_permissions=True)


def onload(doc, method):
    for item in doc.items:
        if item.last_qty_prescribed:
            frappe.msgprint(
                _("The item {0} was last prescribed on {1} for {2} {3}").format(
                    item.item_code,
                    item.last_date_prescribed,
                    item.last_qty_prescribed,
                    item.stock_uom,
                ),
            )


def set_prescribed(doc):
    for item in doc.items:
        items_list = frappe.db.sql(
            """
        select dn.posting_date, dni.item_code, dni.stock_qty, dni.uom from `tabDelivery Note` dn
        inner join `tabDelivery Note Item` dni on dni.parent = dn.name
                        where dni.item_code = %s
                        and dn.patient = %s
                        and dn.docstatus = 1
                        order by posting_date desc
                        limit 1"""
            % ("%s", "%s"),
            (item.item_code, doc.patient),
            as_dict=1,
        )
        if len(items_list):
            item.last_qty_prescribed = items_list[0].get("stock_qty")
            item.last_date_prescribed = items_list[0].get("posting_date")


def set_missing_values(doc):
    if doc.reference_doctype and doc.reference_name:
        if doc.reference_doctype == "Patient Encounter":
            doc.patient = frappe.get_value(
                "Patient Encounter", doc.reference_name, "patient"
            )
            
    if not doc.hms_tz_phone_no:
        doc.hms_tz_phone_no = frappe.get_value('Patient', doc.patient, 'mobile')
    
    if doc.form_sales_invoice:
        if not doc.hms_tz_appointment_no or not doc.hms_tz_practitioner:
            si_reference_dn = frappe.get_value('Sales Invoice Item', doc.items[0].si_detail, 'reference_dn')

            if si_reference_dn:
                parent_encounter = frappe.get_value('Drug Prescription', si_reference_dn, 'parent')
                doc.hms_tz_appointment_no, doc.hms_tz_practitioner = frappe.get_value('Patient Encounter', parent_encounter, ['appointment', 'practitioner'])


def before_submit(doc, method):
    if doc.hms_tz_is_all_items_out_of_stock == 1:
        frappe.throw("<h4 class='font-weight-bold bg-warning text-center'>\
            This Delivery Note can't be submitted because all Items\
                are not available in stock</h4>")

    for item in doc.items:
        if item.is_restricted and not item.approval_number:
            frappe.throw(
                _(
                    "Approval number required for {0}. Please open line {1} and set the Approval Number."
                ).format(item.item_name, item.idx)
            )

def on_submit(doc, method):
    update_drug_prescription(doc)

def update_drug_prescription(doc):
    if doc.patient and not doc.is_return:
        if doc.form_sales_invoice:
            sales_invoice_doc = frappe.get_doc("Sales Invoice", doc.form_sales_invoice)

            for item in sales_invoice_doc.items:
                if item.reference_dt == "Drug Prescription":
                    for dni in doc.items:
                        if (
                            item.name == dni.si_detail and 
                            item.item_code == dni.item_code and 
                            item.parent == dni.against_sales_invoice
                        ):
                            if item.qty != dni.stock_qty:
                                quantity = dni.stock_qty
                            else:
                                quantity = item.qty

                            frappe.db.set_value("Drug Prescription", item.reference_dn, {
                                "dn_detail": dni.name,
                                "quantity": quantity,
                                "delivered_quantity": quantity
                            })
                    
                    for og_item in doc.hms_tz_original_items:
                        if (
                            og_item.hms_tz_is_out_of_stock == 1 and
                            item.name == og_item.si_detail and 
                            item.item_code == og_item.item_code and 
                            item.parent == og_item.against_sales_invoice
                        ):
                            frappe.db.set_value("Drug Prescription", item.reference_dn, {
                                "dn_detail": og_item.dn_detail,
                                "is_not_available_inhouse": 1,
                                "hms_tz_is_out_of_stcok": 1
                            })
        
        else:
            if doc.reference_doctype == "Patient Encounter":
                patient_encounter_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)

                for dni in doc.items:
                    if dni.reference_doctype == "Drug Prescription":
                        for item in patient_encounter_doc.drug_prescription:
                            if (
                                dni.item_code == item.drug_code and 
                                dni.reference_name == item.name and 
                                dni.reference_doctype == item.doctype
                            ):
                                item.dn_detail = dni.name
                                if item.quantity != dni.stock_qty:
                                    item.quantity = dni.stock_qty
                                item.delivered_quantity = item.quantity - item.quantity_returned
                                item.db_update()
                
                for og_item in doc.hms_tz_original_items:
                    if (
                        og_item.hms_tz_is_out_of_stock == 1 and 
                        og_item.reference_doctype == "Drug Prescription"
                    ):
                        for item in patient_encounter_doc.drug_prescription:
                            if (
                                og_item.item_code == item.drug_code and 
                                og_item.reference_name == item.name and 
                                og_item.reference_doctype == item.doctype
                            ):
                                item.dn_detail = og_item.dn_detail
                                item.is_not_available_inhouse = 1
                                item.hms_tz_is_out_of_stcok = 1
                                item.db_update()

def check_item_for_out_of_stock(doc):
    """Mark an Item as out of stock if it is not available in stock"""
    if len(doc.items) > 0 and len(doc.hms_tz_original_items) > 0:
        items = []

        for row in doc.items:
            for item in doc.hms_tz_original_items:
                if (
                    row.hms_tz_is_out_of_stock == 1 
                    and row.reference_name == item.reference_name
                    and item.hms_tz_is_out_of_stock == 0
                ):
                    item.hms_tz_is_out_of_stock = 1
                
                if (
                    row.hms_tz_is_out_of_stock == 0
                    and row.reference_name == item.reference_name
                    and item.hms_tz_is_out_of_stock == 1
                ):
                    item.hms_tz_is_out_of_stock = 0
            
            if not row.hms_tz_is_out_of_stock:
                items.append(row)

        doc.items = items
        if len(doc.items) > 0:
            doc.hms_tz_is_all_items_out_of_stock = 0
        else:
            mark_all_items_as_out_of_stock(doc)
            

def mark_all_items_as_out_of_stock(doc):
    """Copy items back to delivery note item table 
    if all items marked as out of stock"""

    for row in doc.hms_tz_original_items:
        new_row = row.as_dict()
        new_row.update({
            'name': None,
            'owner': None,
            'creation': None,
            'modified': None,
            'modified_by': None,
            'docstatus': None,
            'dn_detail': '',
            'parent': doc.name,
            'parentfield': 'items',
            'parenttype': 'Delivery Note',
            'doctype': 'Delivery Note Item'
        })
        doc.append('items', frappe.get_doc(new_row).as_dict())

        if len(doc.items) > 0:
            for item in doc.items:
                if (
                    row.item_code == item.item_code and
                    row.reference_name == item.reference_name
                ):
                    item.hms_tz_is_out_of_stock = 1
                    row.hms_tz_is_out_of_stock = 1
                    row.dn_detail = item.name
    
    doc.hms_tz_is_all_items_out_of_stock = 1
    frappe.msgprint("<h4 class='font-weight-bold bg-warning text-center'>All Items are marked as Out of Stock</h4>")

@frappe.whitelist() 
def convert_to_instock_item(name, row):
    """Convert an item to be considered as it is available in stock

    :param name: Name of the current document.
    :param row: Child table row to be converted.
    """
    new_row = json.loads(row)
    og_item_name = new_row['name']

    new_row.update({
        'name': None,
        'owner': None,
        'creation': None,
        'modified': None,
        'modified_by': None,
        'docstatus': None,
        'dn_detail': None,
        'hms_tz_is_out_of_stock': 0,
        'parent': name,
        'parentfield': 'items',
        'parenttype': 'Delivery Note',
        'doctype': 'Delivery Note Item'
    })
    doc = frappe.get_doc("Delivery Note", name)
    prev_len = len(doc.items)
    doc.append('items', new_row)

    if len(doc.items) > prev_len:
        for entry in doc.items:
            for item in doc.hms_tz_original_items:
                if (
                    og_item_name == item.name and
                    entry.item_code == item.item_code
                ):
                    item.dn_detail = entry.name
                    item.hms_tz_is_out_of_stock = 0
                    break
        doc.save(ignore_permissions=True)
        doc.reload()
        return True

