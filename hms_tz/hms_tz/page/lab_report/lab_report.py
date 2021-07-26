from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def get_data():
    data = frappe.db.get_all(
        "Lab Test",
        filters={"creation": [">", "ADDDATE(now(), -1"]},
        fields=[
            "patient",
            "practitioner",
            "(count(patient) - sum(docstatus)) as remark",
        ],
        group_by="patient, practitioner",
        order_by="max(modified) DESC",
    )

    return data