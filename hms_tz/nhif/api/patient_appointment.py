# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from hms_tz.hms_tz.doctype.patient_appointment.patient_appointment import (
    get_appointment_item,
)
from healthcare.healthcare.doctype.healthcare_settings.healthcare_settings import (
    get_receivable_account,
)
from frappe.model.mapper import get_mapped_doc
from hms_tz.nhif.api.token import get_nhifservice_token
import json
import requests
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import get_item_rate
from frappe.utils import date_diff, getdate, nowdate
from hms_tz.hms_tz.doctype.patient.patient import create_customer
from csf_tz import console


def before_insert(doc, method):
    if doc.inpatient_record:
        frappe.throw(
            _(
                "You cannot create an appointment for a patient already admitted.<br>First <b>discharge the patient</b> and then create the appointment."
            )
        )

    patient_doc = frappe.get_cached_doc("Patient", doc.patient)
    if not patient_doc.customer:
        create_customer(patient_doc)


@frappe.whitelist()
def get_insurance_amount(
    insurance_subscription,
    billing_item,
    company,
    insurance_company,
    has_no_consultation_charges=False,
):
    # SHM Rock: 202
    if has_no_consultation_charges:
        return 0, 0

    item_price = get_item_rate(
        billing_item, company, insurance_subscription, insurance_company
    )

    discount_percent = 0
    if insurance_company and "NHIF" not in insurance_company:
        discount_percent = get_discount_percent(insurance_company)

        amount = item_price - (item_price * (discount_percent / 100))

        return amount, discount_percent

    return item_price, discount_percent


@frappe.whitelist()
def get_mop_amount(billing_item, mop=None, company=None, patient=None):
    price_list = None
    if mop:
        price_list = frappe.get_cached_value("Mode of Payment", mop, "price_list")
    if not price_list and patient:
        price_list = get_default_price_list(patient)
    if not price_list:
        frappe.throw(_("Please set Price List in Mode of Payment"))
    return get_item_price(billing_item, price_list, company)


def get_default_price_list(patient):
    price_list = None
    price_list = frappe.get_cached_value("Patient", patient, "default_price_list")
    if not price_list:
        customer = frappe.get_cached_value("Patient", patient, "customer")
        if customer:
            price_list = frappe.get_cached_value(
                "Customer", customer, "default_price_list"
            )
    if not price_list:
        customer_group = frappe.get_cached_value("Customer", customer, "customer_group")
        frappe.get_cached_value("Customer Group", customer_group, "default_price_list")
    if not price_list:
        if frappe.db.exists("Price List", "Standard Selling"):
            price_list = "Standard Selling"
    return price_list


def get_item_price(item_code, price_list, company):
    price = 0
    company_currency = frappe.get_cached_value("Company", company, "default_currency")
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
            # TODO to be removed since on creating sales invoice we don't need insurance amount
            appointment_doc.paid_amount, discount_percent = get_insurance_amount(
                appointment_doc.insurance_subscription,
                appointment_doc.billing_item,
                appointment_doc.company,
                appointment_doc.insurance_company,
                appointment_doc.has_no_consultation_charges,
            )
            if discount_percent > 0:
                appointment_doc.hms_tz_is_discount_applied = 1

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
        sales_invoice.customer = frappe.get_cached_value(
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
        make_next_doc(appointment_doc, "validate", from_hook=False)
        return "true"


@frappe.whitelist()
def get_consulting_charge_item(appointment_type, practitioner):
    charge_item = ""
    is_inpatient = frappe.get_cached_value("Appointment Type", appointment_type, "ip")
    field_name = (
        "inpatient_visit_charge_item" if is_inpatient else "op_consulting_charge_item"
    )
    charge_item = frappe.get_cached_value(
        "Healthcare Practitioner", practitioner, field_name
    )
    return charge_item


@frappe.whitelist()
def create_vital(appointment):
    appointment_doc = frappe.get_doc("Patient Appointment", appointment)
    make_vital(appointment_doc, "patient_appointment")
    appointment_doc.save()
    appointment_doc.reload()


def make_vital(appointment_doc, method):
    if (
        appointment_doc.insurance_subscription
        and not appointment_doc.authorization_number
    ):
        frappe.msgprint(
            _(
                "Authorization number not set to proceed to create vitals for this appointment. Please get the authorization number first and then try again."
            ),
            alert=True,
        )
        return
    if appointment_doc.insurance_subscription and appointment_doc.billing_item:
        appointment_doc.paid_amount, discount_percent = get_insurance_amount(
            appointment_doc.insurance_subscription,
            appointment_doc.billing_item,
            appointment_doc.company,
            appointment_doc.insurance_company,
            appointment_doc.has_no_consultation_charges,
        )
        if discount_percent > 0:
            appointment_doc.hms_tz_is_discount_applied = 1
            frappe.msgprint(
                "Discount of {0} is applied to this Patient: {1}".format(
                    frappe.bold(discount_percent), frappe.bold(appointment_doc.patient)
                ),
                alert=True,
            )

    set_follow_up(appointment_doc, "invoice_appointment")
    # SHM Rock: 202
    if "NHIF" in appointment_doc.insurance_company and appointment_doc.appointment_type:
        appointment_doc.has_no_consultation_charges = frappe.get_cached_value(
            "Appointment Type",
            appointment_doc.appointment_type,
            "has_no_consultation_charges",
        )
        if appointment_doc.has_no_consultation_charges:
            if appointment_doc.paid_amount > 0:
                appointment_doc.paid_amount = 0

            frappe.msgprint(
                _(
                    f"This appointment type: <b>{appointment_doc.appointment_type}</b> has no consultation charges."
                ),
                alert=True,
            )

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
        appointment_doc.db_update()
        frappe.msgprint(_("Vital Signs {0} created".format(vital_doc.name)))


def make_encounter(doc, method):
    if doc.is_new():
        return
    if doc.doctype == "Vital Signs":
        if not doc.appointment or doc.inpatient_record:
            return
        if (
            frappe.get_value("Patient Appointment", doc.appointment, "status")
            == "Cancelled"
        ):
            frappe.throw("<b>Appointment is already cancelled</b>")
        source_name = doc.appointment
    elif doc.doctype == "Patient Appointment":
        if (
            (not doc.authorization_number and not doc.mode_of_payment)
            or doc.ref_patient_encounter
            or doc.status == "Cancelled"
        ):
            return

        if doc.insurance_subscription and doc.billing_item and doc.paid_amount <= 0:
            doc.paid_amount, discount_percent = get_insurance_amount(
                doc.insurance_subscription,
                doc.billing_item,
                doc.company,
                doc.insurance_company,
                doc.has_no_consultation_charges,
            )
            if discount_percent > 0:
                doc.hms_tz_is_discount_applied = 1

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
    frappe.msgprint(_("Patient Encounter {0} created".format(encounter_doc.name)))

    if doc.doctype == "Patient Appointment":
        doc.ref_patient_encounter = encounter_doc.name
        doc.db_update()

        if doc.healthcare_package_order:
            return encounter_doc.name


@frappe.whitelist()
def get_authorization_num(
    insurance_subscription,
    company,
    appointment_type,
    card_no,
    referral_no="",
    remarks="",
):
    enable_nhif_api, service_url = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "insurance_provider": "NHIF"},
        ["enable", "service_url"],
    )
    if not enable_nhif_api:
        frappe.msgprint(
            _(f"Company {company} not enabled for NHIF Integration")
        )
        return

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
        + frappe.get_cached_value(
            "Appointment Type", appointment_type, "visit_type_id"
        )[:1]
    )
    referral_no = "&ReferralNo=" + str(referral_no)
    remarks = "&Remarks=" + str(remarks)

    token = get_nhifservice_token(company, "NHIF")

    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    url = (
        str(service_url)
        + "/nhifservice/breeze/verification/AuthorizeCard?"
        + card_no
        + visit_type_id
        + referral_no
        + remarks
    )

    r = requests.get(url, headers=headers, timeout=5)
    r.raise_for_status()
    frappe.logger().debug({"webhook_success": r.text})
    if json.loads(r.text):
        add_log(
            request_type="AuthorizeCard",
            request_url=url,
            request_header=headers,
            response_data=json.loads(r.text),
            status_code=r.status_code,
        )
        card = json.loads(r.text)
        # console(card)
        if card.get("AuthorizationStatus") != "ACCEPTED":
            frappe.throw(title=card.get("AuthorizationStatus"), msg=card["Remarks"])
        frappe.msgprint(_(card["Remarks"]), alert=True)
        add_scheme(card.get("SchemeID"), card.get("SchemeName"))
        add_product(company, card.get("ProductCode"), card.get("ProductName"))
        update_insurance_subscription(insurance_subscription, card, company)
        return card
    else:
        add_log(
            request_type="AuthorizeCard",
            request_url=url,
            request_header=headers,
            status_code=r.status_code,
        )
        frappe.throw(json.loads(r.text))


def update_insurance_subscription(insurance_subscription, card, company):
    subscription_doc = frappe.get_cached_doc(
        "Healthcare Insurance Subscription", insurance_subscription
    )

    if (
        subscription_doc.hms_tz_product_code != card["ProductCode"]
        or subscription_doc.hms_tz_scheme_id != card["SchemeID"]
    ):
        from hms_tz.nhif.api.patient import get_coverage_plan

        coverage_plan = get_coverage_plan(card, company)

        if coverage_plan:
            card["CoveragePlanName"] = coverage_plan
            plan_doc = frappe.get_cached_doc(
                "Healthcare Insurance Coverage Plan", coverage_plan
            )

            if plan_doc:
                subscription_doc.insurance_company = plan_doc.insurance_company
                subscription_doc.healthcare_insurance_coverage_plan = plan_doc.name
                subscription_doc.coverage_plan_name = plan_doc.coverage_plan_name

        subscription_doc.hms_tz_product_code = card["ProductCode"]
        subscription_doc.hms_tz_product_name = card["ProductName"]

        subscription_doc.hms_tz_scheme_id = card["SchemeID"]
        subscription_doc.hms_tz_scheme_name = card["SchemeName"]

        subscription_doc.save(ignore_permissions=True)

    return card


@frappe.whitelist()
def send_vfd(invoice_name):
    if "vfd_tz" not in frappe.get_installed_apps():
        frappe.msgprint(_("VFD App Not installed"), alert=True)
        msg = {"enqueue": False}
        return msg
    else:
        from vfd_tz.vfd_tz.api.sales_invoice import enqueue_posting_vfd_invoice

        enqueue_posting_vfd_invoice(invoice_name)
        pos_profile_name = frappe.get_value(
            "Sales Invoice", invoice_name, "pos_profile"
        )
        pos_profile = frappe.get_cached_doc("POS Profile", pos_profile_name)
        msg = {"enqueue": True, "pos_rofile": pos_profile}
        return msg


@frappe.whitelist()
def get_previous_appointment(patient, filters=None):
    the_filters = {"patient": patient, "follow_up": 0}
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
        "department": appointment_doc.department,
        "status": ["in", ["Open", "Closed"]],
    }
    if appointment_doc.insurance_subscription:
        filters["insurance_subscription"] = appointment_doc.insurance_subscription
    else:
        filters["mode_of_payment"] = ["!=", ""]

    appointment = get_previous_appointment(appointment_doc.patient, filters)
    if appointment and appointment_doc.appointment_date:
        diff = date_diff(appointment_doc.appointment_date, appointment.appointment_date)
        if appointment_doc.mode_of_payment:
            valid_days = int(
                frappe.get_cached_value(
                    "Healthcare Settings", "Healthcare Settings", "valid_days"
                )
            )
        else:
            valid_days = int(
                frappe.get_cached_value(
                    "Healthcare Insurance Coverage Plan",
                    {"coverage_plan_name": appointment_doc.coverage_plan_name},
                    "no_of_days_for_follow_up",
                )
            )
            if valid_days == 0:
                valid_days = int(
                    frappe.get_cached_value(
                        "Healthcare Insurance Company",
                        appointment_doc.insurance_company,
                        "no_of_days_for_follow_up",
                    )
                )
        if diff <= valid_days:
            appointment_doc.follow_up = 1
            if (
                appointment_doc.follow_up
                and appointment_doc.insurance_subscription
                and not appointment_doc.authorization_number
            ):
                return
            appointment_doc.invoiced = 1
            appointment_doc.paid_amount = 0
            frappe.msgprint(
                _(
                    "Previous appointment found valid for free follow-up.<br>Skipping invoice for this appointment!"
                ),
                alert=True,
            )
        else:
            appointment_doc.follow_up = 0
            # frappe.msgprint(_("This appointment requires to be paid for!"), alert=True)


def make_next_doc(doc, method, from_hook=True):
    validate_insurance_subscription(doc)
    check_multiple_appointments(doc)
    if doc.is_new():
        return
    if doc.insurance_subscription:
        is_active, his_patient, coverage_plan = frappe.get_cached_value(
            "Healthcare Insurance Subscription",
            doc.insurance_subscription,
            ["is_active", "patient", "healthcare_insurance_coverage_plan"],
        )
        if not is_active:
            frappe.throw(
                _(
                    "The Insurance Subscription is NOT ACTIVE. Please select the correct Insurance Subscription."
                )
            )

        if doc.patient != his_patient:
            frappe.throw(
                _(
                    "Insurance Subscription belongs to another patient. Please select the correct Insurance Subscription."
                )
            )
        if "NHIF" not in doc.insurance_company and not doc.daily_limit:
            doc.daily_limit = frappe.get_cached_value(
                "Healthcare Insurance Coverage Plan", coverage_plan, "daily_limit"
            )

    if not doc.billing_item and doc.authorization_number:
        doc.billing_item = get_consulting_charge_item(
            doc.appointment_type, doc.practitioner
        )
        if not doc.billing_item:
            frappe.throw(
                _(
                    "Billing item was not set from {0} for appointment type {1}.".format(
                        doc.practitioner, doc.appointment_type
                    )
                )
            )
        else:
            frappe.msgprint(
                _(
                    "Billing item was set from {0} for appointment type {1}.".format(
                        doc.practitioner, doc.appointment_type
                    )
                )
            )
    if from_hook:
        set_follow_up(doc, method)
        # SHM Rock: 202
        if "NHIF" in doc.insurance_company and doc.appointment_type:
            doc.has_no_consultation_charges = frappe.get_cached_value(
                "Appointment Type", doc.appointment_type, "has_no_consultation_charges"
            )
            if doc.has_no_consultation_charges:
                if doc.paid_amount > 0:
                    doc.paid_amount = 0

                frappe.msgprint(
                    _(
                        f"This appointment type: <b>{doc.appointment_type}</b> has no consultation charges."
                    ),
                    alert=True,
                )

    if not doc.patient_age:
        doc.patient_age = calculate_patient_age(doc.patient)
    # fix: followup appointments still require authorization number
    if doc.follow_up and doc.insurance_subscription and not doc.authorization_number:
        return
    # do not create vital sign or encounter if appointment is already cancelled
    if doc.status == "Cancelled":
        return

    # do not create vital sign or encounter if appointment is already invoiced
    if doc.mode_of_payment and not doc.invoiced:
        return

    if frappe.get_cached_value(
        "Healthcare Practitioner", doc.practitioner, "bypass_vitals"
    ):
        make_encounter(doc, method)
    else:
        make_vital(doc, method)


@frappe.whitelist()
def validate_insurance_company(insurance_company: str) -> str:
    if frappe.get_value("Healthcare Insurance Company", insurance_company, "disabled"):
        frappe.msgprint(
            _(
                "<b>Insurance Company: <strong>{0}</strong> is disabled, Please choose different insurance subscription</b>".format(
                    insurance_company
                )
            )
        )
        return True
    return False


@frappe.whitelist()
def validate_insurance_subscription(doc):
    if not doc.insurance_subscription:
        return

    if (
        frappe.db.get_value(
            "Healthcare Insurance Subscription", doc.insurance_subscription, "docstatus"
        )
        == 0
    ):
        url = frappe.utils.get_link_to_form(
            "Healthcare Insurance Subscription", doc.insurance_subscription
        )
        frappe.throw(
            _(
                f"Insurance Subscription: <strong>{doc.insurance_subscription}</strong> is on Draft<br>\
                Click here: <strong>{url}</strong> to submit Insurance Subscription"
            )
        )


def calculate_patient_age(patient):
    dob = frappe.get_value("Patient", patient, "dob")
    if not dob:
        frappe.msgprint(
            "<h4 style='background-color: LightCoral'>Please update date of birth for this patient</h4>"
        )
        return None
    diff = date_diff(nowdate(), dob)
    years = diff // 365
    months = (diff - (years * 365)) // 30
    return f"{years} Year(s) {months} Month(s)"


def get_discount_percent(insurance_company):
    """Get discount percent (%) from Non NHIF Insurance Company"""

    discount_percent = 0
    has_price_discount, discount = frappe.get_cached_value(
        "Healthcare Insurance Company",
        insurance_company,
        ["hms_tz_has_price_discount", "hms_tz_price_discount"],
    )
    if has_price_discount and discount == 0:
        frappe.throw(
            _(
                "Please set discount(%) for this insurance company: {0}".format(
                    frappe.bold(insurance_company)
                )
            )
        )

    if has_price_discount and discount > 0:
        discount_percent = discount

    return discount_percent


def check_multiple_appointments(doc):
    if doc.healthcare_package_order:
        return

    if (
        doc.coverage_plan_card_number
        and "NHIF" in doc.insurance_company
        and doc.appointment_type in ["Outpatient Visit", "Normal Visit"]
        and doc.department not in ["Eye", "Optometrist", "Physiotherapy"]
    ):
        appointments = frappe.get_list(
            "Patient Appointment",
            filters={
                "patient": doc.patient,
                "coverage_plan_card_number": doc.coverage_plan_card_number,
                "appointment_date": frappe.utils.nowdate(),
                "status": ["!=", "Cancelled"],
                "name": ["!=", doc.name],
            },
            fields=["name", "department", "practitioner"],
        )

        if len(appointments) > 0:
            msg = f"Patient already has an appointment: <b>{appointments[0].name}</b> for Practitioner: <b>{appointments[0].practitioner}</b>. \
                <br>It is adviced to have only one appointment per day."
            frappe.msgprint(msg)
            frappe.msgprint(
                f"Patient already has an appointment for <b>{appointments[0].practitioner}</b>",
                alert=True,
            )
