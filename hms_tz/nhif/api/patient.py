# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from hms_tz.nhif.api.token import get_nhifservice_token
from erpnext import get_default_company
import json
import requests
from time import sleep
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from frappe.utils import getdate, nowdate, flt
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import remove_special_characters
from datetime import date
from frappe.utils.background_jobs import enqueue
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product


def validate(doc, method):
    # validate date of birth
    if date.today() < getdate(doc.dob):
        frappe.throw(_("The date of birth cannot be later than today's date"))

    check_card_number(doc.card_no, doc.is_new(), doc.name, "validate")

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

    service_url = frappe.get_cached_value(
        "Company NHIF Settings", company, "service_url"
    )
    headers = {"Authorization": "Bearer " + token}
    url = (
        str(service_url)
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
    # update_history = frappe.get_cached_value(
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
def check_card_number(card_no, is_new=None, patient=None, caller=None):
    if not card_no:
        return "false"
    filters = {"insurance_card_detail": ["like", "%" + card_no + "%"]}
    if not is_new and patient:
        filters["name"] = ["!=", patient]
    patients = frappe.get_all("Patient", filters=filters)
    if len(patients):
        if caller:
            frappe.throw(
                f"Cardno: <b>{card_no}</b> used with patient: <b>{patient}</b>, Please change Cardno to Proceed"
            )
        return patients[0].name
    else:
        return "false"


def create_subscription(doc):
    if not frappe.db.exists("NHIF Product", {"nhif_product_code": doc.product_code}):
        company = get_default_company()
        if company:
            add_product(company, doc.get("product_code"), None)

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

    coverage_plan = get_coverage_plan(doc)
    if not coverage_plan:
        return

    plan_doc = frappe.get_cached_doc(
        "Healthcare Insurance Coverage Plan", coverage_plan
    )
    sub_doc = frappe.new_doc("Healthcare Insurance Subscription")
    sub_doc.patient = doc.name
    sub_doc.insurance_company = plan_doc.insurance_company
    sub_doc.healthcare_insurance_coverage_plan = plan_doc.name
    sub_doc.coverage_plan_card_number = doc.card_no
    sub_doc.hms_tz_product_code = doc.product_code
    sub_doc.hms_tz_scheme_id = doc.scheme_id
    sub_doc.save(ignore_permissions=True)
    sub_doc.submit()
    frappe.msgprint(
        _(
            f"<h3>AUTO</h3> Healthcare Insurance Subscription: {sub_doc.name} is created for {plan_doc.name}"
        )
    )


def get_coverage_plan(doc=None, card=None, company=None):
    from frappe.utils import cstr

    data = None
    if not doc and card:
        data = card
    if doc:
        data = doc

    product_code = data.get("product_code") or data["ProductCode"]
    scheme_id = data.get("scheme_id") or data["SchemeID"]
    nhif_employername = data.get("nhif_employername") or data["EmployerName"]

    nhif_product_filters = {
        "nhif_product_code": product_code,
    }
    if company:
        nhif_product_filters["company"] = company

    # Assumed that company is filtered based on user permissions
    plan = frappe.db.get_list(
        "NHIF Product",
        filters=nhif_product_filters,
        fields="healthcare_insurance_coverage_plan as name",
    )
    if len(plan) == 0:
        frappe.msgprint(
            _(
                f"Failed to find matching plan for product code {product_code} and employer name {nhif_employername}"
            ),
            alert=True,
        )
        return

    coverage_plan_scheme_id = frappe.get_cached_value(
        "Healthcare Insurance Coverage Plan",
        plan[0].name,
        "nhif_scheme_id",
    )
    if (
        scheme_id
        and coverage_plan_scheme_id
        and cstr(scheme_id) != cstr(coverage_plan_scheme_id)
    ):
        coverage_filters = {
            "nhif_scheme_id": scheme_id,
            "is_active": 1,
        }
        if company:
            coverage_filters["company"] = company

        # Assumed that company is filtered based on user permissions
        plan = frappe.db.get_list(
            "Healthcare Insurance Coverage Plan",
            filters=coverage_filters,
            fields=["name"],
        )
        if len(plan) == 0:
            frappe.msgprint(
                _(
                    f"""Failed to find matching plan for SchemeId: {scheme_id} and employer name {nhif_employername}"""
                ),
                alert=True,
            )
            return
        elif len(plan) > 1:
            frappe.msgprint(
                _(
                    f"""Multiple plans found for SchemeId: {scheme_id}, please select the plan manually"""
                ),
                alert=True,
            )
            return

    return plan[0].name


def after_insert(doc, method):
    if not doc.card_no:
        return
    doc.insurance_card_detail = (doc.card_no or "") + ", "
    create_subscription(doc)


@frappe.whitelist()
def enqueue_update_cash_limit(old_cash_limit, new_cash_limit):
    if getdate(nowdate()).strftime("%A") != "Saturday":
        frappe.throw(
            "<h4 class='font-weight-bold text-center'>\
            Please run this routine only on Saturday</h4>"
        )

    data = dict(old_value=old_cash_limit, new_value=new_cash_limit)

    enqueue(
        method=update_cash_limit,
        queue="default",
        timeout=600000,
        job_name="update_new_cash_limit",
        is_async=True,
        kwargs=data,
    )


def update_cash_limit(kwargs):
    data = kwargs
    patient_list = frappe.get_all("Patient", {"status": "Active"}, pluck="name")
    for name in patient_list:
        try:
            doc = frappe.get_cached_doc("Patient", name)
            if flt(doc.cash_limit) != flt(data.get("new_value")):
                doc.cash_limit = flt(data.get("new_value"))
                doc.db_update()
        except Exception:
            frappe.log_error(frappe.get_traceback())

    frappe.db.commit()


@frappe.whitelist()
def validate_missing_patient_dob(patient: str):
    patient_name, dob = frappe.get_value("Patient", patient, ["patient_name", "dob"])
    if not dob:
        return False
    return True
