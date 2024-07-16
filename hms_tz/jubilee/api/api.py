import json
import frappe
import requests
from frappe import _
from time import sleep
from erpnext import get_default_company
from frappe.utils.background_jobs import enqueue
from hms_tz.jubilee.api.token import get_jubilee_service_token
from hms_tz.jubilee.api.price_package import sync_jubilee_price_package
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import (
    add_jubilee_log,
)


@frappe.whitelist()
def get_member_card_detials(card_no, insurance_provider):
    if not card_no or insurance_provider != "Jubilee":
        return

    company = get_default_company()
    if not company:
        company = frappe.defaults.get_user_default("Company")

    if not company:
        company = frappe.get_list(
            "Company Insurance Setting",
            fields=["company"],
            filters={"enable": 1, "api_provider": insurance_provider},
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
    url = str(service_url) + f"/jubileeapi/Getcarddetails?MemberNo={str(card_no)}"
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


@frappe.whitelist()
def create_jubilee_subscription(patient_id, card_no, insurance_provider):
    if not insurance_provider or insurance_provider != "Jubilee":
        return

    subscription_list = frappe.get_list(
        "Healthcare Insurance Subscription",
        filters={"patient": patient_id, "is_active": 1},
    )
    if len(subscription_list) > 0:
        frappe.msgprint(
            _(
                "Existing Patient HIS was found. Create the Healthcare Insurance Subscription manually!"
            )
        )
        return

    plan_filters = {
        "is_active": 1,
        "insurance_company": ["like", "Jubilee%"],
    }
    company = get_default_company()
    if company:
        plan_filters["company"] = company

    # Assumed that company is filtered based on user permissions
    plan = frappe.db.get_list(
        "Healthcare Insurance Coverage Plan",
        filters=plan_filters,
        fields=["name", "insurance_company", "company"],
    )

    if not plan or len(plan) == 0:
        frappe.msgprint(
            _("No active Healthcare Insurance Coverage Plan found for Jubilee")
        )
        return

    if len(plan) > 1:
        frappe.msgprint(
            _(
                "Multiple active Healthcare Insurance Coverage Plan found for Jubilee,\
                    <br><br>please create the healthcare Insurance Subscription manually"
            )
        )
        return

    sub_doc = frappe.new_doc("Healthcare Insurance Subscription")
    sub_doc.patient = patient_id
    sub_doc.insurance_company = plan[0].insurance_company
    sub_doc.healthcare_insurance_coverage_plan = plan[0].name
    sub_doc.coverage_plan_card_number = card_no
    sub_doc.save(ignore_permissions=True)
    sub_doc.submit()
    frappe.msgprint(
        _(
            f"<h3>AUTO</h3> Healthcare Insurance Subscription: {sub_doc.name} is created for {plan[0].name}"
        )
    )


@frappe.whitelist()
def enqueue_get_jubilee_price_packages(company):
    enqueue(
        method=get_jubilee_price_packages,
        job_name="get_jubilee_price_packages",
        queue="default",
        timeout=10000000,
        is_async=True,
        company=company,
    )


@frappe.whitelist()
def get_jubilee_price_packages(company, insurance_provider="Jubilee"):
    if not company:
        frappe.throw(_("No companies found to connect to Jubilee"))

    token = get_jubilee_service_token(company, insurance_provider)

    service_url = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "api_provider": insurance_provider},
        "service_url",
    )
    headers = {"Authorization": "Bearer " + token}
    url = str(service_url) + "/jubileeapi/GetPriceList"
    r = requests.get(url, headers=headers, timeout=300)
    if r.status_code != 200:
        add_jubilee_log(
            request_type="GetPricePackage",
            request_url=url,
            request_header=headers,
            response_data=r.text,
            status_code=r.status_code,
            ref_doctype="Jubilee Price Package",
            company=company,
        )
        frappe.throw(json.loads(r.text))
    else:
        if json.loads(r.text):
            log_name = add_jubilee_log(
                request_type="GetPricePackage",
                request_url=url,
                request_header=headers,
                response_data=r.text,
                status_code=r.status_code,
                ref_doctype="Jubilee Price Package",
                company=company,
            )

            packages = json.loads(r.text)["Description"]
            sync_jubilee_price_package(packages, company, log_name)
