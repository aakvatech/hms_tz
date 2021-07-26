# Copyright (c) 2013, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from numpy.core.fromnumeric import size
import pandas as pd
import numpy as np
from frappe import msgprint, _

def execute(filters=None):
	columns = get_columns() 
	data = []

	occupancy_details = get_service_unit_details(filters)
	if not occupancy_details:
		msgprint(frappe.bold("No Service Unit Record For the Filters You Set, Please Set Different Filters..!!"))
	else:
		occupancy_colnames = [key for key in occupancy_details[0].keys()]
		df = pd.DataFrame.from_records(occupancy_details, columns = occupancy_colnames)

		pv_table = pd.pivot_table(
			df,
			index = ["bed"],
			columns = ["date"],
			values = "count",
			fill_value = " ",
			aggfunc = np.size,
			margins = True
		)

		columns += pv_table.columns.values.tolist()

		data += pv_table.reset_index().values.tolist()

	return columns, data


def get_columns():
	columns = [
		{
        	"fieldname": "bed",
        	"fieldtype": "Link",
        	"label": _("Beds"),
        	"options": "Healthcare Service Unit"
        }
	]
	return columns


def get_service_unit_details(filters):
	conditions = ""
	
	if filters.get("from_date"):
		conditions += "DATE(check_in) >= %(from_date)s"
	
	if filters.get("to_date"):
		conditions += "and DATE(check_in) <= %(to_date)s"

	return frappe.db.sql("""
		SELECT service_unit as bed, date_format(DATE(check_in), '%%Y-%%m-%%d') as date, COUNT(*) as count
		FROM `tabInpatient Occupancy` io
		WHERE {conditions}
		GROUP BY service_unit, DATE(check_in)
		""".format(conditions= conditions), filters, as_dict = 1
	)
