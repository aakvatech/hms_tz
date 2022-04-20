# -*- coding: utf-8 -*-
# Copyright (c) 2018, earthians and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import datetime

from hms_tz.hms_tz.utils import validate_customer_created
from frappe.utils import nowdate, nowtime, now_datetime, add_to_date
from datetime import timedelta
import base64
import re


@frappe.whitelist()
def get_healthcare_services_to_invoice(
    patient, company, encounter=None, service_order_category=None, prescribed=None
):
    patient = frappe.get_doc("Patient", patient)
    items_to_invoice = []
    if patient:
        validate_customer_created(patient)
        # Customer validated, build a list of billable services
        if encounter:
            items_to_invoice += get_healthcare_service_order_to_invoice(
                patient, company, encounter, service_order_category, prescribed
            )
        return items_to_invoice


def get_childs_map():
    childs_map = {
        "Lab Prescription": {
            "table": "lab_test_prescription",
            "doctype": "Lab Prescription",
            "template": "Lab Test Template",
            "item": "lab_test_code",
        },
        "Radiology Procedure Prescription": {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Procedure Prescription",
            "template": "Radiology Examination Template",
            "item": "radiology_examination_template",
        },
        "Procedure Prescription": {
            "table": "procedure_prescription",
            "doctype": "Procedure Prescription",
            "template": "Clinical Procedure Template",
            "item": "procedure",
        },
        "Drug Prescription": {
            "table": "drug_prescription",
            "doctype": "Drug Prescription",
            "template": "Medication",
            "item": "drug_code",
        },
        "Therapy Plan Detail": {
            "table": "therapies",
            "doctype": "Therapy Plan Detail",
            "template": "Therapy Type",
            "item": "therapy_type",
        },
    }
    return childs_map


def get_healthcare_service_order_to_invoice(
    patient, company, encounter, service_order_category=None, prescribed=None
):

    reference_encounter = frappe.get_value(
        "Patient Encounter", encounter, "reference_encounter"
    )
    encounter_dict = frappe.get_all(
        "Patient Encounter",
        filters={
            "reference_encounter": reference_encounter,
            "docstatus": 1,
            "is_not_billable": 0,
        },
    )
    encounter_list = []
    for i in encounter_dict:
        encounter_doc = frappe.get_doc("Patient Encounter", i.name)
        encounter_list.append(encounter_doc)
    childs_map = get_childs_map()
    services_to_invoice = []

    for en in encounter_list:
        for key, value in childs_map.items():
            table = en.get(value.get("table"))
            if not table:
                continue
            for row in table:
                if (
                    not row.get("invoiced")
                    and row.get("prescribe")
                    and not row.get("is_not_available_inhouse")
                    and not row.get("is_cancelled")
                ):
                    item_code = frappe.get_value(
                        value.get("template"),
                        row.get(value.get("item")),
                        "item",
                    )
                    services_to_invoice.append(
                        {
                            "reference_type": row.doctype,
                            "reference_name": row.name,
                            "service": item_code,
                            "qty": row.get("quantity") or 1,
                        }
                    )

    return services_to_invoice


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
def get_item_rate(item_code, company, insurance_subscription, insurance_company=None):
    price_list = None
    price_list_rate = None
    if insurance_subscription:
        hic_plan = frappe.get_value(
            "Healthcare Insurance Subscription",
            insurance_subscription,
            "healthcare_insurance_coverage_plan",
        )
        price_list, secondary_price_list, insurance_company = frappe.get_value(
            "Healthcare Insurance Coverage Plan",
            hic_plan,
            ["price_list", "secondary_price_list", "insurance_company"],
        )
        if price_list:
            price_list_rate = get_item_price(item_code, price_list, company)
            if price_list_rate and price_list_rate != 0:
                return price_list_rate
            else:
                price_list_rate = None
        if not price_list_rate:
            price_list_rate = get_item_price(item_code, secondary_price_list, company)
            if price_list_rate and price_list_rate != 0:
                return price_list_rate
            else:
                price_list_rate = None

    if not price_list_rate and insurance_company:
        price_list = frappe.get_value(
            "Healthcare Insurance Company", insurance_company, "default_price_list"
        )
    if not price_list:
        frappe.throw(
            _(
                "Could not get price for item {0} for price list in {1}. Please set Price List in Healthcare Insurance Coverage Plan {1} or Insurance Company {2}"
            ).format(item_code, hic_plan, insurance_company)
        )
    else:
        price_list_rate = get_item_price(item_code, price_list, company)
    if price_list_rate and price_list_rate != 0:
        return price_list_rate
    else:
        frappe.throw(
            _("Please set Price List for item: {0} in price list {1}").format(
                item_code, price_list
            )
        )


def to_base64(value):
    data = base64.b64encode(value)
    return str(data)[2:-1]


def remove_special_characters(text):
    return re.sub("[^A-Za-z0-9]+", "", text)


def get_app_branch(app):
    """Returns branch of an app"""
    import subprocess

    try:
        branch = subprocess.check_output(
            "cd ../apps/{0} && git rev-parse --abbrev-ref HEAD".format(app), shell=True
        )
        branch = branch.decode("utf-8")
        branch = branch.strip()
        return branch
    except Exception:
        return ""


def create_delivery_note_from_LRPT(LRPT_doc, patient_encounter_doc):
    if not patient_encounter_doc.appointment:
        return
    # purposely put this below to skip the delivery note process 2021-04-07 14:36:07
    if patient_encounter_doc.appointment:
        return
    # purposely put this above to skip the delivery note process 2021-04-07 14:36:04
    insurance_subscription, insurance_company = frappe.get_value(
        "Patient Appointment",
        patient_encounter_doc.appointment,
        ["insurance_subscription", "insurance_company"],
    )
    if not insurance_subscription:
        return
    warehouse = get_warehouse_from_service_unit(
        patient_encounter_doc.healthcare_service_unit
    )
    items = []
    item = get_item_form_LRPT(LRPT_doc)
    item_code = item.get("item_code")
    if not item_code:
        return
    is_stock, item_name = frappe.get_value(
        "Item", item_code, ["is_stock_item", "item_name"]
    )
    if is_stock:
        return
    item_row = frappe.new_doc("Delivery Note Item")
    item_row.item_code = item_code
    item_row.item_name = item_name
    item_row.warehouse = warehouse
    item_row.healthcare_service_unit = item.healthcare_service_unit
    item_row.practitioner = patient_encounter_doc.practitioner
    item_row.qty = item.qty
    item_row.rate = get_item_rate(
        item_code,
        patient_encounter_doc.company,
        insurance_subscription,
        insurance_company,
    )
    item_row.reference_doctype = LRPT_doc.doctype
    item_row.reference_name = LRPT_doc.name
    item_row.description = frappe.get_value("Item", item_code, "description")
    items.append(item_row)

    if len(items) == 0:
        return
    doc = frappe.get_doc(
        dict(
            doctype="Delivery Note",
            posting_date=nowdate(),
            posting_time=nowtime(),
            set_warehouse=warehouse,
            company=patient_encounter_doc.company,
            customer=frappe.get_value(
                "Healthcare Insurance Company", insurance_company, "customer"
            ),
            currency=frappe.get_value(
                "Company", patient_encounter_doc.company, "default_currency"
            ),
            items=items,
            reference_doctype=LRPT_doc.doctype,
            reference_name=LRPT_doc.name,
            patient=patient_encounter_doc.patient,
            patient_name=patient_encounter_doc.patient_name,
        )
    )
    doc.flags.ignore_permissions = True
    # doc.set_missing_values()
    doc.insert(ignore_permissions=True)
    doc.submit()
    if doc.get("name"):
        frappe.msgprint(
            _("Delivery Note {0} created successfully.").format(frappe.bold(doc.name)),
            alert=True,
        )


def get_warehouse_from_service_unit(healthcare_service_unit):
    warehouse = frappe.get_value(
        "Healthcare Service Unit", healthcare_service_unit, "warehouse"
    )
    if not warehouse:
        frappe.throw(
            _("Warehouse is missing in Healthcare Service Unit {0}").format(
                healthcare_service_unit
            )
        )
    return warehouse


def get_item_form_LRPT(LRPT_doc):
    item = frappe._dict()
    comapny_option = get_template_company_option(LRPT_doc.template, LRPT_doc.company)
    item.healthcare_service_unit = comapny_option.service_unit
    if LRPT_doc.doctype == "Lab Test":
        item.item_code = frappe.get_value(
            "Lab Test Template", LRPT_doc.template, "item"
        )
        item.qty = 1
    elif LRPT_doc.doctype == "Radiology Examination":
        item.item_code = frappe.get_value(
            "Radiology Examination Template",
            LRPT_doc.radiology_examination_template,
            "item",
        )
        item.qty = 1
    elif LRPT_doc.doctype == "Clinical Procedure":
        item.item_code = frappe.get_value(
            "Clinical Procedure Template",
            LRPT_doc.procedure_template,
            "item",
        )
        item.qty = 1
    elif LRPT_doc.doctype == "Therapy Plan":
        item.item_code = None
        item.qty = 0
    return item


def update_dimensions(doc):
    for item in doc.items:
        refd, refn = get_references(item)
        if doc.healthcare_practitioner:
            item.healthcare_practitioner = doc.healthcare_practitioner
        elif refd and refn:
            item.healthcare_practitioner = get_healthcare_practitioner(item)

        if (
            doc.healthcare_service_unit
            and not item.healthcare_service_unit
            and not refn
        ):
            item.healthcare_service_unit = doc.healthcare_service_unit

        if refd and refn:
            item.healthcare_service_unit = get_healthcare_service_unit(item)


def get_references(item):
    refd = ""
    refn = ""
    if item.get("reference_doctype"):
        refd = item.get("reference_doctype")
        refn = item.get("reference_name")
    elif item.get("reference_dt"):
        refd = item.get("reference_dt")
        refn = item.get("reference_dn")
    return refd, refn


def get_healthcare_practitioner(item):
    refd, refn = get_references(item)
    if not refd or not refn:
        return

    ref_docs = [
        {"reference_doc": "Lab Prescription"},
        {"reference_doc": "Radiology Procedure Prescription"},
        {"reference_doc": "Procedure Prescription"},
        {"reference_doc": "Therapy Plan Detail"},
    ]

    for ref_doc in ref_docs:
        if refd == ref_doc.get("reference_doc"):
            parent, parenttype = frappe.get_value(
                ref_doc.get("reference_doc"), refn, ["parent", "parenttype"]
            )
            if (
                parent and 
                parenttype == "Patient Encounter"
            ):
                return frappe.get_value("Patient Encounter", parent, "practitioner")
        
    if refd == "Patient Encounter":
        return frappe.get_value("Patient Encounter", refn, "practitioner")
    elif refd == "Patient Appointment":
        return frappe.get_value("Patient Appointment", refn, "practitioner")
    elif refd == "Drug Prescription":
        parent, parenttype = frappe.get_value(
            "Drug Prescription", refn, ["parent", "parenttype"]
        )
        if parenttype == "Patient Encounter":
            return frappe.get_value("Patient Encounter", parent, "practitioner")
    elif refd == "Healthcare Service Order":
        encounter = frappe.get_value("Healthcare Service Order", refn, "order_group")
        if encounter:
            return frappe.get_value("Patient Encounter", encounter, "practitioner")


def get_healthcare_service_unit(item):
    refd, refn = get_references(item)
    if not refd or not refn:
        return

    ref_docs = [
        {"reference_doc": "Lab Prescription"},
        {"reference_doc": "Radiology Procedure Prescription"},
        {"reference_doc": "Procedure Prescription"},
        {"reference_doc": "Therapy Plan Detail"},
    ]

    for ref_doc in ref_docs:
        if refd == ref_doc.get("reference_doc"):
            return frappe.get_value(ref_doc.get("reference_doc"), refn, "department_hsu")

    if refd == "Patient Encounter":
        return frappe.get_value("Patient Encounter", refn, "healthcare_service_unit")
    elif refd == "Patient Appointment":
        return frappe.get_value("Patient Appointment", refn, "service_unit")
    elif refd == "Drug Prescription":
        return frappe.get_value("Drug Prescription", refn, "healthcare_service_unit")
    elif refd == "Healthcare Service Order":
        order_doctype, order, order_group, billing_item, company = frappe.get_value(
            refd,
            refn,
            ["order_doctype", "order", "order_group", "billing_item", "company"],
        )
        if order_doctype in [
            "Lab Test Template",
            "Radiology Examination Template",
            "Clinical Procedure Template",
            "Therapy Plan Template",
        ]:
            comapny_option = get_template_company_option(order, company)
            return comapny_option.service_unit

        elif order_doctype == "Medication":
            if not order_group:
                return
            prescriptions = frappe.get_all(
                "Drug Prescription",
                filters={
                    "parent": order_group,
                    "parentfield": "drug_prescription",
                    "drug_code": billing_item,
                },
                fields=["name", "healthcare_service_unit"],
            )
            if len(prescriptions) > 0:
                return prescriptions[0].healthcare_service_unit


def get_restricted_LRPT(doc):
    if doc.doctype == "Lab Test":
        template = doc.template
    elif doc.doctype == "Radiology Examination":
        template = doc.radiology_examination_template
    elif doc.doctype == "Clinical Procedure":
        template = doc.procedure_template
    elif doc.doctype == "Therapy Plan":
        template = doc.therapy_plan_template
    else:
        frappe.msgprint(
            _(
                "Unknown Doctype "
                + doc.doctype
                + " found in get_restricted_LRPT. Setup may be missing."
            )
        )
    is_restricted = 0
    if not template:
        return is_restricted
    if doc.ref_doctype and doc.ref_docname and doc.ref_doctype == "Patient Encounter":
        insurance_subscription = frappe.get_value(
            "Patient Encounter", doc.ref_docname, "insurance_subscription"
        )
        if insurance_subscription:
            healthcare_insurance_coverage_plan = frappe.get_value(
                "Healthcare Insurance Subscription",
                insurance_subscription,
                "healthcare_insurance_coverage_plan",
            )
            if healthcare_insurance_coverage_plan:
                insurance_coverages = frappe.get_all(
                    "Healthcare Service Insurance Coverage",
                    filters={
                        "healthcare_service_template": template,
                        "healthcare_insurance_coverage_plan": healthcare_insurance_coverage_plan,
                    },
                    fields=["name", "approval_mandatory_for_claim"],
                )
                if len(insurance_coverages) > 0:
                    is_restricted = insurance_coverages[0].approval_mandatory_for_claim
    return is_restricted


# Sales Invoice Dialog Box for Healthcare Services
@frappe.whitelist()
def set_healthcare_services(doc, checked_values):
    import json

    doc = frappe.get_doc(json.loads(doc))
    checked_values = json.loads(checked_values)
    doc.items = []
    from erpnext.stock.get_item_details import get_item_details

    for checked_item in checked_values:
        item_line = doc.append("items", {})
        price_list = doc.selling_price_list
        item_line.item_code = checked_item["item"]
        item_line.qty = 1
        item_line.allow_over_sell = 1
        if checked_item["qty"]:
            item_line.qty = checked_item["qty"]
        if checked_item["rate"]:
            item_line.rate = checked_item["rate"]
        else:
            item_line.rate = get_item_price(
                checked_item["item"], price_list, doc.company
            )
        item_line.amount = float(item_line.rate) * float(item_line.qty)
        if checked_item["income_account"]:
            item_line.income_account = checked_item["income_account"]
        if checked_item["dt"]:
            item_line.reference_dt = checked_item["dt"]
        if checked_item["dn"]:
            item_line.reference_dn = checked_item["dn"]
        if checked_item["description"]:
            item_line.description = checked_item["description"]

        childs_map = get_childs_map()
        parent_encounter = frappe.get_value(
            checked_item["dt"],
            checked_item["dn"],
            "parent",
        )
        item_line.healthcare_practitioner, company = frappe.get_value(
            "Patient Encounter",
            parent_encounter,
            ["practitioner", "company"],
        )

        if checked_item["dt"] == "Drug Prescription":
            item_line.healthcare_service_unit = frappe.get_value(
                checked_item["dt"],
                checked_item["dn"],
                "healthcare_service_unit",
            )

        else:
            map_obj = childs_map.get(checked_item["dt"])
            service_item = frappe.get_value(
                checked_item["dt"],
                checked_item["dn"],
                map_obj.get("item"),
            )
            comapny_option = get_template_company_option(service_item, company)
            item_line.healthcare_service_unit = comapny_option.service_unit

        item_line.warehouse = get_warehouse_from_service_unit(
            item_line.healthcare_service_unit
        )
    doc.set_missing_values(for_validate=True)
    doc.save()
    return doc.name


def create_individual_lab_test(source_doc, child):
    if child.lab_test_created == 1 or child.is_not_available_inhouse:
        return
    ltt_doc = frappe.get_doc("Lab Test Template", child.lab_test_code)
    patient_sex = frappe.get_value("Patient", source_doc.patient, "sex")

    doc = frappe.new_doc("Lab Test")
    doc.patient = source_doc.patient
    doc.patient_sex = patient_sex
    doc.company = source_doc.company
    doc.template = ltt_doc.name
    if source_doc.doctype == "Healthcare Service Order":
        doc.practitioner = source_doc.ordered_by
    else:
        doc.practitioner = source_doc.practitioner
    doc.source = source_doc.source
    if child.prescribe:
        doc.prescribe = 1
    else:
        doc.insurance_subscription = source_doc.insurance_subscription
    doc.ref_doctype = source_doc.doctype
    doc.ref_docname = source_doc.name
    doc.invoiced = 1
    doc.service_comment = (
        (child.medical_code or "No ICD Code")
        + " : "
        + (child.lab_test_comment or "No Comment")
    )

    doc.save(ignore_permissions=True)
    if doc.get("name"):
        frappe.msgprint(
            _("Lab Test {0} created successfully.").format(frappe.bold(doc.name))
        )

        child.lab_test_created = 1
        # lab prescription will be updated only is lab test is submitted
        # child.lab_test = doc.name
        child.db_update()

    # Will not submit sales invoice or patient encounter if lab test is not created
    else:
        frappe.throw(frappe.bold("Lab Test was not created, please try submitting again"))


def create_individual_radiology_examination(source_doc, child):
    if child.radiology_examination_created == 1 or child.is_not_available_inhouse:
        return
    doc = frappe.new_doc("Radiology Examination")
    doc.patient = source_doc.patient
    doc.company = source_doc.company
    doc.radiology_examination_template = child.radiology_examination_template
    if source_doc.doctype == "Healthcare Service Order":
        doc.practitioner = source_doc.ordered_by
    else:
        doc.practitioner = source_doc.practitioner
    doc.source = source_doc.source
    if child.prescribe:
        doc.prescribe = 1
    else:
        doc.insurance_subscription = source_doc.insurance_subscription
    doc.medical_department = frappe.get_value(
        "Radiology Examination Template",
        child.radiology_examination_template,
        "medical_department",
    )
    doc.ref_doctype = source_doc.doctype
    doc.ref_docname = source_doc.name
    doc.invoiced = 1
    doc.service_comment = (
        (child.medical_code or "No ICD Code")
        + " : "
        + (child.radiology_test_comment or "No Comment")
    )

    doc.save(ignore_permissions=True)
    if doc.get("name"):
        frappe.msgprint(
            _("Radiology Examination {0} created successfully.").format(
                frappe.bold(doc.name)
            )
        )

        child.radiology_examination_created = 1
        # radiology procedure prescription will be updated only if radiology examination is submitted
        # child.radiology_examination = doc.name
        child.db_update()

    # 08-02-2022
    # Will not submit sales invoice or patient encounter if radiology examination is not created
    else:
        frappe.throw(frappe.bold("Radiology Examination was not created, please try submitting again"))


def create_individual_procedure_prescription(source_doc, child):
    if child.procedure_created == 1 or child.is_not_available_inhouse:
        return
    doc = frappe.new_doc("Clinical Procedure")
    doc.patient = source_doc.patient
    doc.company = source_doc.company
    doc.procedure_template = child.procedure
    if source_doc.doctype == "Healthcare Service Order":
        doc.practitioner = source_doc.ordered_by
    else:
        doc.practitioner = source_doc.practitioner
    doc.source = source_doc.source
    if child.prescribe:
        doc.prescribe = 1
    else:
        doc.insurance_subscription = source_doc.insurance_subscription
    doc.patient_sex = frappe.get_value("Patient", source_doc.patient, "sex")
    doc.medical_department = frappe.get_value(
        "Clinical Procedure Template", child.procedure, "medical_department"
    )
    doc.ref_doctype = source_doc.doctype
    doc.ref_docname = source_doc.name
    doc.invoiced = 1
    doc.service_comment = (
        (child.medical_code or "No ICD Code") + " : " + (child.comments or "No Comment")
    )

    doc.save(ignore_permissions=True)
    if doc.get("name"):
        frappe.msgprint(
            _("Clinical Procedure {0} created successfully.").format(
                frappe.bold(doc.name)
            )
        )

        child.procedure_created = 1
        # procedure prescription will be updated only clinical procedure is submitted
        # child.clinical_procedure = doc.name
        child.db_update()

    # 08-02-2022
    # Will not submit sales invoice or patient encounter if clinical procedure is not created
    else:
        frappe.throw(frappe.bold("Clinical Procedure was not created, please try submitting again"))


def msgThrow(msg, method="throw", alert=True):
    if method == "validate":
        frappe.msgprint(msg, alert=alert)
    else:
        frappe.throw(msg)


def msgPrint(msg, method="throw", alert=False):
    if method == "validate":
        frappe.msgprint(msg, alert=True)
    else:
        frappe.msgprint(msg, alert=alert)


def get_approval_number_from_LRPMT(ref_doctype=None, ref_docname=None):
    if not ref_doctype or not ref_docname:
        return None
    if ref_doctype == "Drug Prescription":
        approval_number_list = frappe.get_all(
            "Delivery Note Item",
            filters={"reference_doctype": ref_doctype, "reference_name": ref_docname},
            fields=["approval_number"],
        )
        if len(approval_number_list) > 0:
            return approval_number_list[0].approval_number
    else:
        return frappe.get_value(ref_doctype, ref_docname, "approval_number")


def set_uninvoiced_so_closed():
    from erpnext.selling.doctype.sales_order.sales_order import update_status

    uninvoiced_so_list = frappe.get_list(
        "Sales Order",
        fields=("name"),
        filters={
            "status": ("in", ["To Bill", "To Deliver and Bill"]),
            "docstatus": 1,
            "creation": ("<", now_datetime() - timedelta(hours=3)),
        },
    )
    for so in uninvoiced_so_list:
        so_doc = frappe.get_doc("Sales Order", so.name)
        so_doc.update_status("Closed")


def validate_hsu_healthcare_template(doc):
    doctypes = [
        "Lab Test Template",
        "Therapy Type",
        "Radiology Examination Template",
        "Clinical Procedure Template",
    ]
    if doc.doctype not in doctypes:
        return
    companys = frappe.get_all("Company", filters={"domain": "Healthcare"})
    companys = [i.name for i in companys]
    for company in companys:
        row = next(
            (d for d in doc.company_options if d.get("company") == company), None
        )
        if not row:
            frappe.msgprint(
                _("Please set Healthcare Service Unit for company {0}").format(company)
            )


@frappe.whitelist()
def get_template_company_option(template=None, company=None):
    def_res = {"company": company, "service_unit": None, "is_not_available": 0}
    if not template or not company:
        return def_res
    exist = frappe.db.exists(
        "Healthcare Company Option", {"company": company, "parent": template}
    )
    if exist:
        doc = frappe.get_doc(
            "Healthcare Company Option", {"company": company, "parent": template}
        )
        return doc
    else:
        return def_res


# Cancel open appointments, delete draft vital signs and delete draft delivery note
def delete_or_cancel_draft_document():
    from frappe.utils import nowdate, add_to_date

    before_7_days_date = add_to_date(nowdate(), days=-7, as_string=False)
    before_45_days_date = add_to_date(nowdate(), days=-45, as_string=False)

    appointments = frappe.db.sql(
        """
        SELECT name FROM `tabPatient Appointment` 
        WHERE status = "Open" AND appointment_date < '{before_7_days_date}'
    """.format(
            before_7_days_date=before_7_days_date
        ),
        as_dict=1,
    )

    for app_doc in appointments:
        frappe.db.set_value(
            "Patient Appointment",
            app_doc.name,
            "status",
            "Cancelled",
            update_modified=False,
        )

    vital_docs = frappe.db.sql(
        """
        SELECT name FROM `tabVital Signs` 
        WHERE docstatus = 0 AND signs_date < '{before_7_days_date}'
    """.format(
            before_7_days_date=before_7_days_date
        ),
        as_dict=1,
    )

    for vs_doc in vital_docs:
        doc = frappe.get_doc("Vital Signs", vs_doc.name)
        doc.delete()
        frappe.db.commit()

    delivery_documents = frappe.db.sql(
        """
        SELECT name FROM `tabDelivery Note` 
        WHERE docstatus = 0 AND posting_date < '{before_45_days_date}'
    """.format(
            before_45_days_date=before_45_days_date
        ),
        as_dict=1,
    )

    for dn_doc in delivery_documents:
        dn_del = frappe.get_doc("Delivery Note", dn_doc.name)
        try:
            if not dn_del.hms_tz_is_all_items_out_of_stock:
                dn_del.delete()
        except Exception:
            frappe.log_error(frappe.get_traceback())
        frappe.db.commit()
