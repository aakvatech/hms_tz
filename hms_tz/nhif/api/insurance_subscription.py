# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from time import sleep

# from frappe import _
from hms_tz.nhif.api.patient import get_patient_info


def on_submit(doc, method):
    set_insurance_card_detail_in_patient(doc)


def on_update_after_submit(doc, method):
    if method != "on_submit" and doc.is_active == 1:
        set_insurance_card_detail_in_patient(doc)


def on_cancel(doc, method):
    set_insurance_card_detail_in_patient(doc)


def set_insurance_card_detail_in_patient(doc):
    his_list = frappe.get_all(
        "Healthcare Insurance Subscription",
        filters={
            "patient": doc.patient,
            "docstatus": 1,
            "is_active": 1,
        },
        fields=["coverage_plan_card_number"],
        group_by="coverage_plan_card_number",
    )
    str_coverage_plan_card_number = ""
    card_count = 0
    for card in his_list:
        if card.coverage_plan_card_number:
            card_count += 1
            str_coverage_plan_card_number += card.coverage_plan_card_number + ", "

    # wait for 30 seconds to avoid an Error of 'Document is already modified'
    sleep(30)
    frappe.db.set_value(
        "Patient",
        doc.patient,
        {
            "insurance_card_detail": str_coverage_plan_card_number[:-2],
            "card_no": doc.coverage_plan_card_number,
        },
    )


@frappe.whitelist()
def check_patient_info(patient, card_no, patient_name):
    if not patient or not card_no:
        return
    patient_info = get_patient_info(card_no)
    if patient_name != patient_info.get("FullName"):
        patient_doc = frappe.get_cached_doc("Patient", patient)
        patient_doc.patient_name = patient_info.get("FullName")
        patient_doc.first_name = patient_info.get("FirstName")
        patient_doc.middle_name = patient_info.get("MiddleName")
        patient_doc.last_name = patient_info.get("LastName")
        patient_doc.sex = patient_info.get("Gender")
        patient_doc.dob = patient_info.get("DateOfBirth")
        patient_doc.product_code = patient_info.get("ProductCode")
        patient_doc.membership_no = patient_info.get("membership_no")
        patient_doc.save(ignore_permissions=True)
    return patient_info.get("FullName")


def before_insert(doc, method):
    validate_card_info(doc)


def validate(doc, method):
    validate_card_info(doc)


def validate_card_info(doc):
    his_list = frappe.get_all(
        "Healthcare Insurance Subscription",
        filters={
            "patient": doc.patient,
            "docstatus": 1,
            "is_active": 1,
            "healthcare_insurance_coverage_plan": doc.healthcare_insurance_coverage_plan,
            "coverage_plan_card_number": doc.coverage_plan_card_number,
        },
        fields=["coverage_plan_card_number", "coverage_plan_name"],
    )
    if len(his_list) > 0:
        frappe.throw(
            _(
                f"The card {doc.coverage_plan_card_number} already exists for plan {doc.coverage_plan_name}"
            )
        )
