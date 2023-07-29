# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from hms_tz.nhif.api.healthcare_utils import (
    update_dimensions,
    create_individual_lab_test,
    create_individual_radiology_examination,
    create_individual_procedure_prescription,
)


def validate(doc, method):
    for item in doc.items:
        if not item.is_free_item and item.amount == 0:
            frappe.throw(
                _(
                    "Amount of the healthcare service <b>'{0}'</b> cannot be ZERO. Please do not select this item and request Pricing team to resolve this."
                ).format(item.item_name)
            )
    update_dimensions(doc)
    validate_create_delivery_note(doc)


def validate_create_delivery_note(doc):
    if not doc.patient:
        return
    inpatient_record = frappe.get_cached_value  ("Patient", doc.patient, "inpatient_record")
    if inpatient_record:
        insurance_subscription = frappe.get_value(
            "Inpatient Record", inpatient_record, "insurance_subscription"
        )
        if not insurance_subscription:
            doc.enabled_auto_create_delivery_notes = 0


@frappe.whitelist()
def create_pending_healthcare_docs(doc_name):
    doc = frappe.get_doc("Sales Invoice", doc_name)
    create_healthcare_docs(doc, "From Front End")


def before_submit(doc, method):
    if doc.is_pos and doc.outstanding_amount != 0:
        frappe.throw(
            _(
                "Sales invoice not paid in full.<BR><BR>Make sure that full paid amount is entered in <b>Mode of Payments table.</b>"
            )
        )
    
    if doc.hms_tz_discount_requested == 1 and doc.hms_tz_discount_status == "Pending":
        frappe.throw(_("Patient Discount Request is still pending. Please wait for approval before submitting this invoice."))

def on_submit(doc, method):
    create_healthcare_docs(doc, method)
    update_drug_prescription(doc)


def create_healthcare_docs(doc, method):
    if doc.docstatus != 1 or method not in ["on_submit", "From Front End"]:
        frappe.msgprint(
            _(
                "No LRPMTs were created. Alert the IT Team!<b><br>DOCSTATUS = {0}<br>METHOD {1}</b>".format(
                    doc.docstatus, method
                )
            )
        )
        return
    if doc.get("items"):
        for item in doc.items:
            if item.reference_dt and item.reference_dt in [
                "Lab Prescription",
                "Radiology Procedure Prescription",
                "Procedure Prescription",
            ]:
                child = frappe.get_doc(item.reference_dt, item.reference_dn)
                patient_encounter_doc = frappe.get_doc(
                    "Patient Encounter", child.parent
                )
                if child.doctype == "Lab Prescription":
                    create_individual_lab_test(patient_encounter_doc, child)
                elif child.doctype == "Radiology Procedure Prescription":
                    create_individual_radiology_examination(
                        patient_encounter_doc, child
                    )
                elif child.doctype == "Procedure Prescription":
                    create_individual_procedure_prescription(
                        patient_encounter_doc, child
                    )
                child.invoiced = 1
                child.sales_invoice_number = doc.name
                child.save(ignore_permissions=True)

                item.hms_tz_is_lrp_item_created = 1
                item.db_update()

    if method == "From Front End":
        frappe.db.commit()

def update_drug_prescription(doc):
    if doc.patient and doc.enabled_auto_create_delivery_notes:
        for item in doc.items:
            if (
                item.reference_dn and 
                item.reference_dt and 
                item.reference_dt == "Drug Prescription"
            ):
                dn_name = frappe.get_value("Delivery Note", {"form_sales_invoice": doc.name}, "name")
                if not dn_name:
                    return
                frappe.db.set_value("Drug Prescription", item.reference_dn, {
                    "sales_invoice_number": doc.name,
                    "drug_prescription_created": 1,
                    "invoiced": 1
                })

@frappe.whitelist()
def get_discount_items(invoice_no):
    items = frappe.get_all(
        "Sales Invoice Item", filters={"parent": invoice_no},
        fields=["item_code", "item_name", "amount", "reference_dt", "name"], order_by="reference_dt desc"
    )
    return items
