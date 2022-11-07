# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from hms_tz.nhif.api.healthcare_utils import msgThrow
from frappe.utils import nowdate, get_fullname, get_url_to_form

class PriceChangeRequest(Document):
	def before_insert(self):
		self.posting_date = nowdate()
		self.requested_by = get_fullname(frappe.session.user)
	

	def validate(self):
		for row in self.items:
			validate_item(row.item_code, "validate")
			validate_price_list(row.price_list, "validate")

			row.old_price = set_old_price(row.item_code, row.price_list)		
	
	
	def before_submit(self):
		for row in self.items:
			validate_item(row.item_code, "throw")
			validate_price_list(row.price_list, "throw")
			validate_zero_prices(row)

			set_new_price_item(row, nowdate())
		self.approved_by = get_fullname(frappe.session.user)


@frappe.whitelist()
def validate_item(item, method):	
	disabled = frappe.get_cached_value("Item", item, "disabled")
	if disabled == 1:
		msgThrow(_("Item: {0} is disabled".format(frappe.bold(item))), method)


@frappe.whitelist()
def validate_price_list(price_list, method):
	if not frappe.get_cached_value("Price List", price_list, "enabled"):
		msgThrow(_("Price List: {0} is disabled".format(frappe.bold(price_list))), method)


def set_old_price(item, price_list):
	"""set old price of an item from item price"""

	return frappe.get_value(
		"Item Price", 
		{"item_code": item, "price_list": price_list, "valid_from": ["<=", nowdate()]}, 
		["price_list_rate"], order_by="valid_from desc"
	)


def validate_zero_prices(row):
	"""Check for zero price, and stopping zero price of an item before updating item price"""

	if not row.new_price:
		frappe.throw("Zero price is not allowed for an item: {0}, row: #{1}".format(
			frappe.bold(row.item_code), frappe.bold(row.idx)
		))

def set_new_price_item(row, date):
	"""Set new price to existing item price or create new item price"""

	item_price = frappe.get_all(
		"Item Price", 
		filters={"item_code": row.item_code, "price_list": row.price_list, "valid_from": ["<=", date]}
	)

	if not item_price:
		record = create_new_item_price(row, date)
		if record.get("name"):
			url_to_item_price = get_url_to_form(record.doctype, record.name)
			frappe.msgprint("New Item Price: <a href='{0}'>{1}</a> is created".format(
				url_to_item_price, frappe.bold(record.name)
			))

		return True
	
	frappe.set_value("Item Price", item_price[0].name, "price_list_rate", row.new_price)


def create_new_item_price(row, date):
	"""Create new item price if no any item price found for item code and price list"""

	frappe.msgprint("There is no Item price for this Item: {0} and price list: {1}.<br>New Item price will be created".format(
			frappe.bold(row.item_code), frappe.bold(row.price_list)
		),
		alert=True
	)
	new_item_price = frappe.get_doc({
		"doctype": "Item Price",
		"item_code": row.item_code,
		"price_list": row.price_list,
		"price_list_rate": row.new_price,
		"valid_from": date
	}).insert(ignore_permissions=True)

	return new_item_price