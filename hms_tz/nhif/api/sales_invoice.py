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
    inpatient_record = frappe.get_value("Patient", doc.patient, "inpatient_record")
    if inpatient_record:
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


def on_submit(doc, method):
    create_healthcare_docs(doc, method)


def create_healthcare_docs(doc, method):
    if doc.docstatus != 1 or method not in ["on_submit", "From Front End"]:
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

    if method == "From Front End":
        frappe.db.commit()
