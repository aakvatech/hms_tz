import json
import frappe
import requests
from frappe import _
from time import sleep
from erpnext import get_default_company
from hms_tz.jubilee.api.token import get_jubilee_service_token
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import add_jubilee_log


@frappe.whitelist()
def get_member_card_detials(card_no, insurance_provider):
    if not card_no or insurance_provider != "Jubilee":
        return

    company = get_default_company()
    if not company:
        company = frappe.defaults.get_user_default("Company")

    if not company:
        company = frappe.get_list(
            "Company Insurance Setting", fields=["company"], filters={"enable": 1, "api_provider": insurance_provider}
        )[0].company
    if not company:
        frappe.throw(_("No companies found to connect to Jubilee"))

    token = get_jubilee_service_token(company, insurance_provider)

    service_url = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "api_provider": insurance_provider},
        "service_url",
    )
    headers = {"Authorization": "Bearer " + token}
    url = (
        str(service_url) + f"/jubileeapi/Getcarddetails?MemberNo={str(card_no)}"
    )
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})

            if json.loads(r.text):
                add_jubilee_log(
                    request_type="GetCardDetails",
                    request_url=url,
                    request_header=headers,
                    response_data=json.loads(r.text),
                    status_code=r.status_code,
                    ref_doctype="Patient",
                )
                card = json.loads(r.text)
                frappe.msgprint(_(card["Status"]), alert=True)
                # add_scheme(card.get("SchemeID"), card.get("SchemeName"))
                # add_product(card.get("ProductCode"), card.get("ProductName"))
                return card
            else:
                add_jubilee_log(
                    request_type="GetCardDetails",
                    request_url=url,
                    request_header=headers,
                    response_data=str(r),
                    status_code=r.status_code,
                    ref_doctype="Patient",
                )
                frappe.msgprint(json.loads(r.text))
                frappe.msgprint(
                    _(
                        "Getting information from NHIF failed. Try again after sometime, or continue manually."
                    )
                )
        except Exception as e:
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e
