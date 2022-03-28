# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from hashlib import new
from types import new_class
import frappe
from frappe import _
from hms_tz.nhif.api.token import get_nhifservice_token
from erpnext import get_default_company
import json
import requests
from time import sleep
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from frappe.utils import getdate
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import remove_special_characters
from datetime import date


def validate(doc, method):
    # validate date of birth
    if date.today() < getdate(doc.dob):
        frappe.throw(_("The date of birth cannot be later than today's date"))
    # replace initial 0 with 255 and remove all the unnecessray characters
    doc.mobile = remove_special_characters(doc.mobile)
    if doc.mobile[0] == "0":
        doc.mobile = "255" + doc.mobile[1:]
    if doc.next_to_kin_mobile_no:
        doc.next_to_kin_mobile_no = remove_special_characters(doc.next_to_kin_mobile_no)
        if doc.next_to_kin_mobile_no[0] == "0":
            doc.next_to_kin_mobile_no = "255" + doc.next_to_kin_mobile_no[1:]
    validate_mobile_number(doc.name, doc.mobile)
    if not doc.is_new():
        update_patient_history(doc)
    else:
        doc.insurance_card_detail = (doc.card_no or "") + ", "


@frappe.whitelist()
def validate_mobile_number(doc_name, mobile=None):
    if mobile:
        mobile_patients_list = frappe.get_all(
            "Patient", filters={"mobile": mobile, "name": ["!=", doc_name]}
        )
        if len(mobile_patients_list) > 0:
            frappe.msgprint(_("This mobile number is used by another patient"))


@frappe.whitelist()
def get_patient_info(card_no=None):
    if not card_no:
        frappe.msgprint(_("Please set Card No"))
        return
    # TODO: need to be fixed to support multiple company
    company = get_default_company()
    if not company:
        company = frappe.defaults.get_user_default("Company")
    if not company:
        company = frappe.get_list(
            "Company NHIF Settings", fields=["company"], filters={"enable": 1}
        )[0].company
    if not company:
        frappe.throw(_("No companies found to connect to NHIF"))
    token = get_nhifservice_token(company)

    nhifservice_url = frappe.get_value(
        "Company NHIF Settings", company, "nhifservice_url"
    )
    headers = {"Authorization": "Bearer " + token}
    url = (
        str(nhifservice_url)
        + "/nhifservice/breeze/verification/GetCardDetails?CardNo="
        + str(card_no)
    )
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})
            if json.loads(r.text):
                add_log(
                    request_type="GetCardDetails",
                    request_url=url,
                    request_header=headers,
                    response_data=json.loads(r.text),
                )
                card = json.loads(r.text)
                frappe.msgprint(_(card["Remarks"]), alert=True)
                add_scheme(card.get("SchemeID"), card.get("SchemeName"))
                add_product(card.get("ProductCode"), card.get("ProductName"))
                return card
            else:
                add_log(
                    request_type="GetCardDetails",
                    request_url=url,
                    request_header=headers,
                )
                frappe.msgprint(json.loads(r.text))
                frappe.msgprint(
                    _(
                        "Getting information from NHIF failed. Try again after sometime, or continue manually."
                    )
                )
        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


def update_patient_history(doc):
    # Remarked till multi company setting is required and feasible from Patient doctype 2021-03-20 19:57:14
    # company = get_default_company()
    # update_history = frappe.get_value(
    #     "Company NHIF Settings", company, "update_patient_history")
    # if not update_history:
    #     return

    medical_history = ""
    for row in doc.codification_table:
        if row.description:
            medical_history += row.description + "\n"
    doc.medical_history = medical_history

    medication = ""
    for row in doc.chronic_medications:
        if row.drug_name:
            medication += row.drug_name + "\n"
    doc.medication = medication
    if doc.medical_history or doc.medication:
        frappe.msgprint(
            _("Update patient history for medical history and chronic medications"),
            alert=True,
        )


@frappe.whitelist()
def check_card_number(card_no, is_new=None, patient=None):
    filters = {"insurance_card_detail": ["like", "%" + card_no + "%"]}
    if not is_new and patient:
        filters["name"] = ["!=", patient]
    patients = frappe.get_all("Patient", filters=filters)
    if len(patients):
        return patients[0].name
    else:
        return "false"


def create_subscription(doc):
    if not frappe.db.exists("NHIF Product", {"nhif_product_code": doc.product_code}):
        return
    subscription_list = frappe.get_list(
        "Healthcare Insurance Subscription",
        filters={"patient": doc.name, "is_active": 1},
    )
    if len(subscription_list) > 0 or not doc.product_code:
        frappe.msgprint(
            _(
                "Existing Patient HIS was found. Create the Healthcare Insurance Subscription manually!"
            )
        )
        return
    plan = frappe.get_list(
        "Healthcare Insurance Coverage Plan",
        {"nhif_employername": doc.nhif_employername},
        "name",
    )

    if len(plan) == 0:
        plan = frappe.db.get_list(
            "NHIF Product",
            {"nhif_product_code": doc.product_code},
            "healthcare_insurance_coverage_plan",
        )
        if len(plan) != 0:
            plan_name = plan[0].healthcare_insurance_coverage_plan
    else:
        plan_name = plan[0].name

    if len(plan) == 0:
        frappe.msgprint(
            _(
                "Failed to find matching plan for product code {0} and employer name {1}".format(
                    doc.product_code, doc.nhif_employername
                )
            ),
            alert=True,
        )
        return
    plan_doc = frappe.get_doc("Healthcare Insurance Coverage Plan", plan_name)
    sub_doc = frappe.new_doc("Healthcare Insurance Subscription")
    sub_doc.patient = doc.name
    sub_doc.insurance_company = plan_doc.insurance_company
    sub_doc.healthcare_insurance_coverage_plan = plan_doc.name
    sub_doc.coverage_plan_card_number = doc.card_no
    sub_doc.save(ignore_permissions=True)
    sub_doc.submit()
    frappe.msgprint(
        _(
            "<h3>AUTO</h3> Healthcare Insurance Subscription {0} is created for {1}"
        ).format(sub_doc.name, plan_name)
    )


def after_insert(doc, method):
    if not doc.card_no:
        return
    doc.insurance_card_detail = (doc.card_no or "") + ", "
    create_subscription(doc)


@frappe.whitelist()
def enqueue_update_cash_limit(old_cash_limit, new_cash_limit):
    from frappe.utils.background_jobs import enqueue

    data = {'old_value': old_cash_limit, 'new_value': new_cash_limit}

    enqueue(
        method=update_cash_limit,
        queue='default',
        timeout=60000,
        job_name='update_new_cash_limit',
        is_async=True,
        kwargs=data
    )

    if frappe.get_all('Patient', ['cash_limit'], page_length=1)[0]['cash_limit'] != old_cash_limit:
        frappe.msgprint(frappe.bold('Cash Limit Updated Successfully'))


def update_cash_limit(kwargs):
    data = kwargs
    patient_list = frappe.get_all('Patient', {'status': 'Active'}, pluck='name')
    pa_names = tuple(patient_list)

    new_cash_limit = data.get('new_value')

    frappe.db.sql("""
        UPDATE `tabPatient` p  SET p.cash_limit = {new_cash_limit}
        WHERE p.name IN {pa_names}
    """.format(new_cash_limit=new_cash_limit, pa_names=pa_names)
    )
    frappe.db.commit()
