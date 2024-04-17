# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import json
import frappe
import requests
from frappe.utils import now_datetime
from frappe.model.document import Document
from hms_tz.nhif.api.token import get_nhifservice_token
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


class HealthcareReferral(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = now_datetime()


@frappe.whitelist()
def get_referral_no(name):
    doc = frappe.get_doc("Healthcare Referral", name)
    validate_required_fields(doc)

    service_url = frappe.get_cached_value(
        "Company NHIF Settings", doc.source_facility, "service_url"
    )

    token = get_nhifservice_token(doc.source_facility)

    url = str(service_url) + "/nhifservice/breeze/verification/AddReferral"

    qualificationid = frappe.get_cached_value(
        "NHIF Physician Qualification",
        doc.nhif_physician_qualification,
        "physicianqualificationid",
    )

    payload = json.dumps(
        {
            "CardNo": doc.card_no,
            "AuthorizationNo": doc.authorization_number,
            "PatientFullName": doc.patient_name,
            "PhysicianMobileNo": "",
            "Gender": doc.gender,
            "PhysicianName": doc.practitioner,
            "PhysicianQualificationID": qualificationid,
            "ServiceIssuingFacilityCode": doc.referrer_facility_code,
            "ReferringDiagnosis": doc.referring_diagnosis,
            "ReasonsForReferral": doc.reason_for_referral,
        }
    )

    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}

    return make_referral_request(doc, url, headers, payload)


def validate_required_fields(doc):
    fields_to_check = [
        "card_no",
        "authorization_number",
        "patient_name",
        "gender",
        "practitioner",
        "referrer_facility_code",
        "referring_diagnosis",
        "reason_for_referral",
    ]

    for fieldname in fields_to_check:
        if not doc.get(fieldname):
            frappe.throw(
                "Missing Value for field: {0}".format(
                    frappe.bold(frappe.unscrub(fieldname))
                )
            )


def make_referral_request(doc, url, headers, payload):
    r = requests.request("POST", url, headers=headers, data=payload, timeout=30)
    data = json.loads(r.text)

    if r.status_code != 200:
        add_log(
            request_type="GetReferralNo",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
        )
        frappe.msgprint(frappe.bold("NHIF Status Code: " + str(r.status_code)))
        frappe.throw(data["Message"])
    else:
        add_log(
            request_type="GetReferralNo",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
        )
        doc.referral_no = data["ReferralNo"]
        doc.referralid = data["ReferralID"]
        doc.referringdate = data["ReferringDate"]
        doc.referral_status = "Success"
        doc.save(ignore_permissions=True)
        doc.reload()

        if doc.get("referral_no"):
            doc.submit()
            return {"referralno": data["ReferralNo"]}
