# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import msgprint, _
import pandas as pd
import numpy as np


def execute(filters=None):
    columns = get_columns(filters)
    data = []

    lab_details = get_lab_results(filters)
    if not lab_details:
        msgprint(frappe.bold(
            "No Record Found for Filters You Specified, Please Choose Different Filters and Try Again..!! "))
    else:
        lab_colnames = [key for key in lab_details[0].keys()]
        df = pd.DataFrame.from_records(lab_details, columns = lab_colnames)

        pvt = pd.pivot_table(
            df,
            values="result_value",
            index="lab_test_name",
            columns="result_date",
            fill_value=" ",
            aggfunc="first"
        )

        columns += pvt.columns.values.tolist()
        data += pvt.reset_index().values.tolist()
    return columns, data

def get_columns(filters):
    columns = [
        {
            "fieldname": "lab_test_name",
            "fieldtype": "Data",
            "label": _("Lab Test Name")
        }
    ]
    return columns


def get_lab_results(filters):

    conditions = ""

    if filters.get("patient"):
        conditions += "and lb.patient = %(patient)s"

    if filters.get("from_date"):
        conditions += "and lb.result_date >= %(from_date)s"

    if filters.get("to_date"):
        conditions += "and lb.result_date <= %(to_date)s"

    if filters.get("department"):
        conditions += "and lb.department = %(department)s"

    return frappe.db.sql("""
		select lb.lab_test_name as lab_test_name,  date_format(lb.result_date, '%%Y-%%m-%%d') as result_date, n.result_value as result_value
		from `tabLab Test` lb inner join `tabNormal Test Result` n on lb.name = n.parent
		where lb.docstatus = 1
        and lb.lab_test_name not in (select lbt.lab_test_name from `tabLab Test Template` lbt where lbt.lab_test_template_type="Grouped")
		and lb.status = "Completed" {conditions}
		union
		select lb.lab_test_name as lab_test_name,  date_format(lb.result_date, '%%Y-%%m-%%d') as result_date, d.result_value as result_value
		from `tabLab Test` lb inner join `tabDescriptive Test Result` d on lb.name = d.parent
		where lb.docstatus = 1
        and lb.lab_test_name not in (select lbt.lab_test_name from `tabLab Test Template` lbt where lbt.lab_test_template_type="Grouped")
		and lb.status = "Completed" {conditions}
		union
		select lb.lab_test_name as lab_test_name,  date_format(lb.result_date, '%%Y-%%m-%%d') as result_date, org.colony_population as result_value
		from `tabLab Test` lb inner join `tabOrganism Test Result` org on lb.name = org.parent
		where lb.docstatus = 1
        and lb.lab_test_name not in (select lbt.lab_test_name from `tabLab Test Template` lbt where lbt.lab_test_template_type="Grouped")
		and lb.status = "Completed" {conditions}
		union
		select lb.lab_test_name as lab_test_name,  date_format(lb.result_date, '%%Y-%%m-%%d') as result_date, ss.antibiotic_sensitivity as result_value
		from `tabLab Test` lb inner join `tabSensitivity Test Result` ss on lb.name = ss.parent
		where lb.docstatus = 1
        and lb.lab_test_name not in (select lbt.lab_test_name from `tabLab Test Template` lbt where lbt.lab_test_template_type="Grouped")
		and lb.status = "Completed" {conditions}
		""".format(conditions=conditions), filters, as_dict=1
    )