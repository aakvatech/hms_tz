# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from hms_tz.hms_tz.doctype.patient_appointment.patient_appointment import (
    get_appointment_item,
)
from erpnext.healthcare.doctype.healthcare_settings.healthcare_settings import (
    get_receivable_account,
)
from frappe.utils import getdate
from frappe.model.mapper import get_mapped_doc
from hms_tz.nhif.api.token import get_nhifservice_token
import json
import requests
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import get_item_rate
from frappe.utils import date_diff, getdate
from csf_tz import console


@frappe.whitelist()
def get_insurance_amount(
    insurance_subscription, billing_item, company, insurance_company
):
    return get_item_rate(
        billing_item, company, insurance_subscription, insurance_company
    )


@frappe.whitelist()
def get_mop_amount(billing_item, mop=None, company=None, patient=None):
    price_list = None
    if mop:
        price_list = frappe.get_value("Mode of Payment", mop, "price_list")
    if not price_list and patient:
        price_list = get_default_price_list(patient)
    if not price_list:
        frappe.throw(_("Please set Price List in Mode of Payment"))
    return get_item_price(billing_item, price_list, company)


def get_default_price_list(patient):
    price_list = None
    price_list = frappe.get_value("Patient", patient, "default_price_list")
    if not price_list:
        customer = frappe.get_value("Patient", patient, "customer")
        if customer:
            price_list = frappe.get_value("Customer", customer, "default_price_list")
    if not price_list:
        customer_group = frappe.get_value("Customer", customer, "customer_group")
        frappe.get_cached_value("Customer Group", customer_group, "default_price_list")
    if not price_list:
        if frappe.db.exists("Price List", "Standard Selling"):
            price_list = "Standard Selling"
    return price_list


def get_item_price(item_code, price_list, company):
    price = 0
    company_currency = frappe.get_value("Company", company, "default_currency")
    item_prices_data = frappe.get_all(
        "Item Price",
        fields=["item_code", "price_list_rate", "currency"],
        filters={
            "price_list": price_list,
            "item_code": item_code,
            "currency": company_currency,
        },
        order_by="valid_from desc",
    )
    if len(item_prices_data):
        price = item_prices_data[0].price_list_rate
    return price


@frappe.whitelist()
def invoice_appointment(name):
    appointment_doc = frappe.get_doc("Patient Appointment", name)
    if appointment_doc.billing_item:
        if appointment_doc.mode_of_payment:
            appointment_doc.paid_amount = get_mop_amount(
                appointment_doc.billing_item,
                appointment_doc.mode_of_payment,
                appointment_doc.company,
                appointment_doc.patient,
            )
        else:
            appointment_doc.paid_amount = get_insurance_amount(
                appointment_doc.insurance_subscription,
                appointment_doc.billing_item,
                appointment_doc.company,
                appointment_doc.insurance_company,
            )
        appointment_doc.save()
        appointment_doc.reload()
    set_follow_up(appointment_doc, "invoice_appointment")
    automate_invoicing = frappe.db.get_single_value(
        "Healthcare Settings", "automate_appointment_invoicing"
    )

    if (
        not automate_invoicing
        and not appointment_doc.insurance_subscription
        and appointment_doc.mode_of_payment
        and not appointment_doc.invoiced
        and not appointment_doc.ref_sales_invoice
        and not appointment_doc.follow_up
    ):
        sales_invoice = frappe.new_doc("Sales Invoice")
        sales_invoice.patient = appointment_doc.patient
        sales_invoice.customer = frappe.get_value(
            "Patient", appointment_doc.patient, "customer"
        )
        sales_invoice.appointment = appointment_doc.name
        sales_invoice.due_date = getdate()
        sales_invoice.company = appointment_doc.company
        sales_invoice.debit_to = get_receivable_account(appointment_doc.company)
        sales_invoice.healthcare_service_unit = appointment_doc.service_unit
        sales_invoice.healthcare_practitioner = appointment_doc.practitioner

        item = sales_invoice.append("items", {})
        item = get_appointment_item(appointment_doc, item)
        item.rate = appointment_doc.paid_amount
        item.amount = appointment_doc.paid_amount

        # Add payments if payment details are supplied else proceed to create invoice as Unpaid
        if appointment_doc.mode_of_payment and appointment_doc.paid_amount:
            sales_invoice.is_pos = 1
            payment = sales_invoice.append("payments", {})
            payment.mode_of_payment = appointment_doc.mode_of_payment
            payment.amount = appointment_doc.paid_amount

        sales_invoice.set_taxes()
        sales_invoice.set_missing_values(for_validate=True)
        sales_invoice.flags.ignore_mandatory = True
        sales_invoice.save(ignore_permissions=True)
        sales_invoice.calculate_taxes_and_totals()
        sales_invoice.submit()
        frappe.msgprint(_("Sales Invoice {0} created".format(sales_invoice.name)))
        appointment_doc = frappe.get_doc("Patient Appointment", appointment_doc.name)
        appointment_doc.ref_sales_invoice = sales_invoice.name
        appointment_doc.invoiced = 1
        appointment_doc.db_update()
        make_next_doc(appointment_doc, "validate")
        return "true"


@frappe.whitelist()
def get_consulting_charge_item(appointment_type, practitioner):
    charge_item = ""
    is_inpatient = frappe.get_value("Appointment Type", appointment_type, "ip")
    field_name = (
        "inpatient_visit_charge_item" if is_inpatient else "op_consulting_charge_item"
    )
    charge_item = frappe.get_value("Healthcare Practitioner", practitioner, field_name)
    return charge_item


@frappe.whitelist()
def create_vital(appointment):
    appointment_doc = frappe.get_doc("Patient Appointment", appointment)
    make_vital(appointment_doc, "patient_appointment")
    appointment_doc.save()
    appointment_doc.reload()


def make_vital(appointment_doc, method):
    if appointment_doc.insurance_subscription and appointment_doc.billing_item:
        appointment_doc.paid_amount = get_insurance_amount(
            appointment_doc.insurance_subscription,
            appointment_doc.billing_item,
            appointment_doc.company,
            appointment_doc.insurance_company,
        )
    set_follow_up(appointment_doc, "invoice_appointment")
    if (not appointment_doc.ref_vital_signs) and (
        appointment_doc.invoiced
        or (
            appointment_doc.insurance_subscription
            and appointment_doc.authorization_number
        )
        or method == "patient_appointment"
    ):
        vital_doc = frappe.get_doc(
            dict(
                doctype="Vital Signs",
                patient=appointment_doc.patient,
                appointment=appointment_doc.name,
                company=appointment_doc.company,
            )
        )
        vital_doc.save(ignore_permissions=True)
        appointment_doc.ref_vital_signs = vital_doc.name
        frappe.msgprint(_("Vital Signs {0} created".format(vital_doc.name)))


def make_encounter(doc, method):
    if doc.is_new():
        return
    if doc.doctype == "Vital Signs":
        if not doc.appointment or doc.inpatient_record:
            return
        source_name = doc.appointment
    elif doc.doctype == "Patient Appointment":
        if (
            not doc.authorization_number and not doc.mode_of_payment
        ) or doc.ref_patient_encounter:
            return
        source_name = doc.name
    target_doc = None
    encounter_doc = get_mapped_doc(
        "Patient Appointment",
        source_name,
        {
            "Patient Appointment": {
                "doctype": "Patient Encounter",
                "field_map": [
                    ["appointment", "name"],
                    ["patient", "patient"],
                    ["practitioner", "practitioner"],
                    ["medical_department", "department"],
                    ["patient_sex", "patient_sex"],
                    ["invoiced", "invoiced"],
                    ["company", "company"],
                    ["appointment_type", "appointment_type"],
                ],
            }
        },
        target_doc,
        ignore_permissions=True,
    )
    encounter_doc.encounter_category = "Appointment"

    encounter_doc.save(ignore_permissions=True)
    if doc.doctype == "Patient Appointment":
        doc.ref_patient_encounter = encounter_doc.name

    frappe.msgprint(_("Patient Encounter {0} created".format(encounter_doc.name)))


@frappe.whitelist()
def get_authorization_num(
    insurance_subscription, company, appointment_type, referral_no=""
):
    enable_nhif_api = frappe.get_value("Company NHIF Settings", company, "enable")
    if not enable_nhif_api:
        frappe.msgprint(
            _("Company {0} not enabled for NHIF Integration".format(company))
        )
        return
    card_no = frappe.get_value(
        "Healthcare Insurance Subscription",
        insurance_subscription,
        "coverage_plan_card_number",
    )
    if not card_no:
        frappe.msgprint(
            _(
                "Please set Card No in Healthcare Insurance Subscription {0}".format(
                    insurance_subscription
                )
            )
        )
        return
    card_no = "CardNo=" + str(card_no)
    visit_type_id = (
        "&VisitTypeID="
        + frappe.get_value("Appointment Type", appointment_type, "visit_type_id")[:1]
    )
    referral_no = "&ReferralNo=" + str(referral_no)
    # remarks = "&Remarks=" + ""
    token = get_nhifservice_token(company)

    nhifservice_url = frappe.get_value(
        "Company NHIF Settings", company, "nhifservice_url"
    )
    headers = {"Authorization": "Bearer " + token}
    url = (
        str(nhifservice_url)
        + "/nhifservice/breeze/verification/AuthorizeCard?"
        + card_no
        + visit_type_id
        + referral_no
    )  # + remarks
    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    frappe.logger().debug({"webhook_success": r.text})
    if json.loads(r.text):
        add_log(
            request_type="AuthorizeCard",
            request_url=url,
            request_header=headers,
            response_data=json.loads(r.text),
        )
        card = json.loads(r.text)
        # console(card)
        if card.get("AuthorizationStatus") != "ACCEPTED":
            frappe.throw(card["Remarks"])
        frappe.msgprint(_(card["Remarks"]), alert=True)
        add_scheme(card.get("SchemeID"), card.get("SchemeName"))
        add_product(card.get("ProductCode"), card.get("ProductName"))
        return card
    else:
        add_log(
            request_type="AuthorizeCard",
            request_url=url,
            request_header=headers,
        )
        frappe.throw(json.loads(r.text))


@frappe.whitelist()
def send_vfd(invoice_name):
    if "vfd_tz" not in frappe.get_installed_apps():
        frappe.msgprint(_("VFD App Not installed"), alert=True)
        msg = {"enqueue": False}
        return msg
    else:
        from vfd_tz.api.sales_invoice import enqueue_posting_vfd_invoice

        enqueue_posting_vfd_invoice(invoice_name)
        pos_profile_name = frappe.get_value(
            "Sales Invoice", invoice_name, "pos_profile"
        )
        pos_profile = frappe.get_doc("POS Profile", pos_profile_name)
        msg = {"enqueue": True, "pos_rofile": pos_profile}
        return msg


@frappe.whitelist()
def get_previous_appointment(patient, filters=None):
    the_filters = {
        "patient": patient,
    }
    if filters:
        # when the function is called from frontend
        if type(filters) == str:
            filters = json.loads(filters)
        the_filters.update(filters)
    appointments = frappe.get_all(
        "Patient Appointment",
        filters=the_filters,
        fields=["appointment_date", "practitioner_name", "name"],
        order_by="appointment_date desc",
    )
    if len(appointments):
        return appointments[0]


def set_follow_up(appointment_doc, method):
    filters = {
        "name": ["!=", appointment_doc.name],
        "insurance_subscription": appointment_doc.insurance_subscription,
        "department": appointment_doc.department,
        "status": "Closed",
    }
    appointment = get_previous_appointment(appointment_doc.patient, filters)
    if appointment and appointment_doc.appointment_date:
        diff = date_diff(appointment_doc.appointment_date, appointment.appointment_date)
        valid_days = int(
            frappe.get_value("Healthcare Settings", "Healthcare Settings", "valid_days")
        )
        if diff <= valid_days:
            appointment_doc.follow_up = 1
            appointment_doc.invoiced = 1
            # frappe.msgprint(_("Previous appointment found valid for free follow-up.<br>Skipping invoice for this appointment!"), alert=True)
        else:
            appointment_doc.follow_up = 0
            # frappe.msgprint(_("This appointment requires to be paid for!"), alert=True)


def make_next_doc(doc, method):
    if doc.inpatient_record:
        frappe.throw(
            _(
                "You cannot create an appointment for a patient already admitted.<br>First <b>discharge the patient</b> and then create the appointment."
            )
        )
    if doc.is_new():
        return
    if doc.ref_sales_invoice:
        doc.invoiced = 1
    # fix: followup appointments still require authorization number
    if doc.follow_up and doc.insurance_subscription and not doc.authorization_number:
        return
    if frappe.get_value("Healthcare Practitioner", doc.practitioner, "bypass_vitals"):
        make_encounter(doc, method)
    else:
        make_vital(doc, method)
