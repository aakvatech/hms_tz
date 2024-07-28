# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe.utils import nowdate, flt
from frappe.model.document import Document
from hms_tz.nhif.api.token import get_claimsservice_token
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


class NHIFClaimReconciliation(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = nowdate()

    def validate_reqd_fields(self):
        for fieldname in ["company", "claim_year", "claim_month"]:
            if not self.get(fieldname):
                frappe.throw(frappe.bold("{0} is required".format(fieldname)))

    def before_submit(self):
        if self.status == "Pending":
            frappe.throw("Cannot submit a pending reconciliation")


@frappe.whitelist()
def get_submitted_claims(self):
    doc = frappe.get_doc(frappe.parse_json(self))
    doc.validate_reqd_fields()

    token = get_claimsservice_token(doc.get("company", "NHIF"))
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}

    facility_code, base_url = frappe.get_cached_value(
        "Company Insurance Setting", {"company": doc.company, "insurance_provider": "NHIF"}, ["facility_code", "claimsserver_url"]
    )
    params = "FacilityCode={0}&ClaimYear={1}&ClaimMonth={2}".format(
        facility_code, doc.claim_year, doc.claim_month
    )

    url = "{0}/claimsserver/api/v1/claims/getSubmittedClaims?{1}".format(
        base_url, params
    )

    data = make_request(url, headers, params)

    if len(data) > 0:
        return update_reconciliation_detail(doc, data)

    else:
        frappe.msgprint(
            "No record found for facility: {0}, claim year: {1} and claim month: {2}".format(
                frappe.bold(doc.company),
                frappe.bold(doc.claim_year),
                frappe.bold(doc.claim_month),
            )
        )
        return False


def make_request(url, headers, payload):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = json.loads(response.text)
            add_log(
                request_type="GetSubmittedClaims",
                request_url=url,
                request_header=headers,
                request_body=payload,
                response_data="total_records: {0}".format(len(data)),
                status_code=response.status_code,
            )
            return data

        else:
            add_log(
                request_type="GetSubmittedClaims",
                request_url=url,
                request_header=headers,
                request_body=payload,
                response_data=response.text,
                status_code=response.status_code,
            )
            data = json.loads(response.text)
            frappe.throw("Message: {0}".format(frappe.bold(data["Message"])))

    except Exception as e:
        raise e
        frappe.throw(str(e))


def update_reconciliation_detail(self, records):
    total_amount = 0
    self.status = "Successful"
    self.number_of_submitted_claims = len(records)

    self.claim_details = []
    for record in records:
        total_amount += flt(record["AmountClaimed"])
        self.append(
            "claim_details",
            {
                "foliono": record["FolioNo"],
                "billno": record["BillNo"],
                "datesubmitted": record["DateSubmitted"],
                "cardno": record["CardNo"],
                "authorizationno": record["AuthorizationNo"],
                "amountclaimed": flt(record["AmountClaimed"]),
                "submissionid": record["SubmissionID"],
                "submissionno": record["SubmissionNo"],
                "remarks": record["Remarks"],
            },
        )

    self.total_amount_claimed = total_amount

    self.save(ignore_permissions=True)
    frappe.db.commit()

    self.reload()

    if len(self.claim_details) > 0:
        self.submit()

    return True
