import json
import frappe
import requests
from time import sleep, localtime
from frappe.utils import now_datetime, add_to_date, now
from frappe.utils.password import get_decrypted_password
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import (
    add_jubilee_log,
)


def make_jubilee_token_request(doc, url, headers, payload, fields):
    for i in range(3):
        try:
            r = requests.request("POST", url, headers=headers, data=payload, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})
            data = json.loads(r.text)
            if data:
                add_jubilee_log(
                    request_type="Token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    response_data=data,
                    status_code=r.status_code,
                    company=doc.company,
                )

            if (
                data["Description"]
                and data["Description"].get("token_type") == "Bearer"
            ):
                token = data["Description"].get("access_token")
                expired = data["Description"].get("expires_in")
                expiry_date = localtime(expired)
                doc.update({fields["token"]: token, fields["expiry"]: expiry_date})

                doc.db_update()
                frappe.db.commit()
                return token
            else:
                add_jubilee_log(
                    request_type="Token",
                    request_url=url,
                    request_header=headers,
                    request_body=payload,
                    response_data=data,
                    status_code=r.status_code,
                    company=doc.company,
                )
                frappe.throw(data)

        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


@frappe.whitelist()
def get_jubilee_service_token(company, api_provider):
    setting_name = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "api_provider": api_provider},
        "name",
    )
    if not setting_name:
        frappe.throw(
            f"Company Insurance Setting not found for company: {company} and API Provider: {api_provider}, please create one."
        )

    setting_doc = frappe.get_cached_doc("Company Insurance Setting", setting_name)
    if (
        setting_doc.service_token_expiry
        and setting_doc.service_token_expiry > now_datetime()
    ):
        return setting_doc.service_token

    payload = {
        "username": setting_doc.username,
        "password": get_decrypted_password(
            setting_doc.doctype, setting_doc.name, "password"
        ),
        "providerid": setting_doc.providerid,
    }
    headers = {}
    url = str(setting_doc.service_url) + "/jubileeapi/Token"

    jubileeservice_fields = {
        "token": "service_token",
        "expiry": "service_token_expiry",
    }

    return make_jubilee_token_request(
        setting_doc, url, headers, payload, jubileeservice_fields
    )


@frappe.whitelist()
def get_jubilee_claimsservice_token(company, api_provider):
    setting_name = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "api_provider": api_provider},
        "name",
    )
    if not setting_name:
        frappe.throw(
            f"Company Insurance Setting not found for company: {company} and API Provider: {api_provider}, please create one."
        )

    setting_doc = frappe.get_cached_doc("Company Insurance Setting", setting_name)

    if (
        setting_doc.claimsserver_expiry
        and setting_doc.claimsserver_expiry > now_datetime()
    ):
        return setting_doc.claimsserver_token

    payload = {
        "username": setting_doc.username,
        "password": get_decrypted_password(
            setting_doc.doctype, setting_doc.name, "password"
        ),
        "providerid": setting_doc.providerid,
    }
    headers = {}
    url = str(setting_doc.claimsserver_url) + "/jubileeapi/Token"

    claimserver_fields = {
        "token": "claimsserver_token",
        "expiry": "claimsserver_expiry",
    }

    return make_jubilee_token_request(
        setting_doc, url, headers, payload, claimserver_fields
    )
