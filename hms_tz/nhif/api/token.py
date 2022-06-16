# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_url_to_form, get_url
from frappe import _
from frappe.utils.password import get_decrypted_password
import json
import requests
from time import sleep
from frappe.utils import now, add_to_date, now_datetime
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def get_nhifservice_token(company):
    setting_doc = frappe.get_doc("Company NHIF Settings", company)
    if (
        setting_doc.nhifservice_expiry
        and setting_doc.nhifservice_expiry > now_datetime()
    ):
        return setting_doc.nhifservice_token

    username = setting_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = str(setting_doc.nhifservice_url) + "/nhifservice/Token"

    for i in range(3):
        try:
            r = requests.request("POST", url, headers=headers, data=payload, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})
            if json.loads(r.text):
                add_log(
                    request_type="token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    response_data=json.loads(r.text),
                )
            if json.loads(r.text)["token_type"] == "bearer":
                token = json.loads(r.text)["access_token"]
                expired = json.loads(r.text)["expires_in"]
                expiry_date = add_to_date(now(), seconds=(expired - 1000))
                setting_doc.nhifservice_token = token
                setting_doc.nhifservice_expiry = expiry_date
                setting_doc.db_update()
                frappe.db.commit()
                return token
            else:
                add_log(
                    request_type="token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                )
                frappe.throw(json.loads(r.text))
        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


def get_claimsservice_token(company):
    setting_doc = frappe.get_doc("Company NHIF Settings", company)
    if (
        setting_doc.claimsserver_expiry
        and setting_doc.claimsserver_expiry > now_datetime()
    ):
        return setting_doc.claimsserver_token

    username = setting_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = str(setting_doc.claimsserver_url) + "/claimsserver/Token"

    for i in range(3):
        try:
            r = requests.request("POST", url, headers=headers, data=payload, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})
            if json.loads(r.text):
                add_log(
                    request_type="token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    response_data=json.loads(r.text),
                )
            if json.loads(r.text)["token_type"] == "bearer":
                token = json.loads(r.text)["access_token"]
                expired = json.loads(r.text)["expires_in"]
                expiry_date = add_to_date(now(), seconds=(expired - 1000))
                setting_doc.claimsserver_token = token
                setting_doc.claimsserver_expiry = expiry_date
                setting_doc.db_update()
                frappe.db.commit()
                return token
            else:
                add_log(
                    request_type="token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                )
                frappe.throw(json.loads(r.text))
        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e
