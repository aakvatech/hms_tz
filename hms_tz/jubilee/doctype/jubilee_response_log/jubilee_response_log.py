# Copyright (c) 2024, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class JubileeResponseLog(Document):
    pass


def add_jubilee_log(
    request_type,
    request_url,
    request_header=None,
    request_body=None,
    response_data=None,
    status_code=None,
    ref_doctype=None,
    ref_docname=None,
):
    doc = frappe.new_doc("Jubilee Response Log")
    doc.request_type = str(request_type)
    doc.request_url = str(request_url)
    doc.request_header = str(request_header) or ""
    doc.request_body = str(request_body) or ""
    doc.response_data = str(response_data) or ""
    doc.user_id = frappe.session.user
    doc.status_code = status_code or ""
    doc.ref_doctype = ref_doctype or ""
    doc.ref_docname = ref_docname or ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return doc.name
