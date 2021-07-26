# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.background_jobs import enqueue


def after_save(doc, method):
    if doc.docstatus == 0 and doc.order_reference_name:
        enqueue(method=auto_submit, queue='short',
                timeout=10000, is_async=True, kwargs=doc.name)
        return


def set_missing_values(doc, method):
    if doc.order_reference_doctype and doc.order_reference_name:
        prescribe = frappe.get_value(
            doc.order_reference_doctype, doc.order_reference_name, "prescribe"
        )
        if not prescribe:
            if doc.insurance_subscription:
                doc.invoiced = 1
            return
        doc.prescribed = prescribe


@frappe.whitelist()
def clear_insurance_details(service_order):
    service_order_doc = frappe.get_doc("Healthcare Service Order", service_order)
    if service_order_doc.docstatus != 0:
        return
    insurance_claim = service_order_doc.insurance_claim
    service_order_doc.insurance_claim = ""
    service_order_doc.insurance_subscription = ""
    service_order_doc.insurance_company = ""
    service_order_doc.claim_status = ""
    service_order_doc.db_update()

    insurance_claim_doc = frappe.get_doc("Healthcare Insurance Claim", insurance_claim)
    insurance_claim_doc.cancel()
    insurance_claim_doc.db_update()
    insurance_claim_doc.reload()
    insurance_claim_doc.delete()

    child_tables = {
        "drug_prescription": "drug_prescription_created",
        "lab_test_prescription": "lab_test_created",
        "procedure_prescription": "procedure_created",
        "radiology_procedure_prescription": "radiology_examination_created",
        # "therapies": "",
    }
    if (
        service_order_doc.order_reference_doctype
        and service_order_doc.order_reference_name
    ):
        child_row_doc = frappe.get_doc(
            service_order_doc.order_reference_doctype,
            service_order_doc.order_reference_name,
        )
        parentfield = child_row_doc.get("parentfield")
        created_field = child_tables.get(parentfield)
        if not created_field:
            return
        setattr(child_row_doc, created_field, 0)
        child_row_doc.prescribe = 1
        child_row_doc.db_update()
    frappe.db.commit()

    frappe.msgprint(
        _("Healthcare Insurance Claim {0} deleted successfully.").format(
            frappe.bold(insurance_claim)
        ),
        alert=True,
    )
    return True


def auto_submit(kwargs):
    import time

    time.sleep(5)
    doc = frappe.get_doc("Healthcare Service Order", kwargs)
    if doc.docstatus == 0 and doc.order_reference_name:
        doc.flags.ignore_permissions = True
        doc.submit()


def real_auto_submit():
    hso_list = frappe.get_all("Healthcare Service Order", filters={"docstatus": 0})
    for hso in hso_list:
        try:
            doc = frappe.get_doc("Healthcare Service Order", hso.name)
            if doc.docstatus == 0 and doc.order_reference_name:
                doc.flags.ignore_permissions = True
                doc.submit()
        except Exception as e:
            frappe.log_error(e)
