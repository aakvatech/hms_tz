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
from frappe.utils import now, add_to_date, now_datetime, cstr
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def make_token_request(doc, url, headers, payload, fields):
    for i in range(3):
        try:
            r = requests.request("POST", url, headers=headers, data=payload, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})
            if json.loads(r.text):
                add_log(
                    request_type="Token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    response_data=json.loads(r.text),
                    status_code=r.status_code,
                )

            if json.loads(r.text)["token_type"] == "bearer":
                token = json.loads(r.text)["access_token"]
                expired = json.loads(r.text)["expires_in"]
                expiry_date = add_to_date(now(), seconds=(expired - 1000))
                doc.update({fields["token"]: token, fields["expiry"]: expiry_date})

                doc.db_update()
                frappe.db.commit()
                return token
            else:
                add_log(
                    request_type="Token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    status_code=r.status_code,
                )
                frappe.throw(json.loads(r.text))

        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


def get_nhifservice_token(company):
    setting_doc = frappe.get_cached_doc("Company NHIF Settings", company)
    if (
        setting_doc.service_token_expiry
        and setting_doc.service_token_expiry > now_datetime()
    ):
        return setting_doc.service_token

    username = setting_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = str(setting_doc.service_url) + "/nhifservice/Token"

    nhifservice_fields = {
        "token": "service_token",
        "expiry": "service_token_expiry",
    }

    return make_token_request(setting_doc, url, headers, payload, nhifservice_fields)


def get_claimsservice_token(company):
    setting_doc = frappe.get_cached_doc("Company NHIF Settings", company)
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

    claimserver_fields = {
        "token": "claimsserver_token",
        "expiry": "claimsserver_expiry",
    }

    return make_token_request(setting_doc, url, headers, payload, claimserver_fields)


def get_formservice_token(company):
    company_nhif_doc = frappe.get_cached_doc("Company NHIF Settings", company)
    if not company_nhif_doc.enable:
        frappe.throw(_("Company {0} not enabled for NHIF Integration".format(company)))

    if (
        company_nhif_doc.form_token_expiry
        and company_nhif_doc.form_token_expiry > now_datetime()
    ):
        return company_nhif_doc.form_token

    username = company_nhif_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = cstr(company_nhif_doc.form_url) + "/formposting/Token"

    nhifform_fields = {
        "token": "form_token",
        "expiry": "form_token_expiry",
    }

    return make_token_request(company_nhif_doc, url, headers, payload, nhifform_fields)
