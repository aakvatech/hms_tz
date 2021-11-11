# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import uuid
from hms_tz.nhif.api.token import get_claimsservice_token
import json
import requests
from frappe.utils.background_jobs import enqueue
from frappe.utils import now, now_datetime, get_fullname, nowdate
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import (
    get_item_rate,
    to_base64,
    get_approval_number_from_LRPMT,
)
import os
from frappe.utils.pdf import get_pdf, cleanup
from PyPDF2 import PdfFileWriter


class NHIFPatientClaim(Document):
    def validate(self):
        self.patient_encounters = self.get_patient_encounters()
        if not self.patient_encounters:
            frappe.throw(_("There are no submitted encounters for this application"))
        if not self.allow_changes:
            from hms_tz.nhif.api.patient_encounter import finalized_encounter

            finalized_encounter(self.patient_encounters[-1])
            self.set_claim_values()
        self.calculate_totals()
        self.set_clinical_notes()
        if not self.is_new():
            frappe.db.sql(
                "UPDATE `tabPatient Appointment` SET nhif_patient_claim = '{0}' WHERE name = '{1}'".format(
                    self.name, self.patient_appointment
                )
            )

    def on_trash(self):
        frappe.set_value(
            "Patient Appointment", self.patient_appointment, "nhif_patient_claim", ""
        )

    def before_submit(self):
        authorization_no = self.authorization_no

        claim_details = frappe.get_all(
            "NHIF Patient Claim",
            filters={"authorization_no": authorization_no, "docstatus": 0},
            fields=["name", "patient", "patient_name"],
        )

        if len(claim_details) > 1:
            claim_name_list = ""
            for claim in claim_details:
                claim_name_list += claim_details[0]["name"] + ", "

                frappe.throw(
                    "This Authorization Number {0} has used multiple times in NHIF Patient Claim: {1}. \
                    Please merge the authorization number to Proceed".format(
                        frappe.bold(authorization_no), frappe.bold(claim_name_list)
                    )
                )
            
        self.patient_encounters = self.get_patient_encounters()
        if not self.patient_signature:
            frappe.throw(_("Patient signature is required"))
        self.patient_file = generate_pdf(self)
        self.claim_file = get_claim_pdf_file(self)
        self.send_nhif_claim()

    def set_claim_values(self):
        if not self.folio_id:
            self.folio_id = str(uuid.uuid1())
        self.facility_code = frappe.get_value(
            "Company NHIF Settings", self.company, "facility_code"
        )
        self.posting_date = nowdate()
        self.folio_no = int(self.name[-9:])
        self.serial_no = self.folio_no
        self.item_crt_by = get_fullname(frappe.session.user)
        final_patient_encounter = self.get_final_patient_encounter()
        self.practitioner_no = frappe.get_value(
            "Healthcare Practitioner",
            final_patient_encounter.practitioner,
            "tz_mct_code",
        )
        if not self.practitioner_no:
            frappe.throw(
                _("There no TZ MCT Code for Practitioner {0}").format(
                    final_patient_encounter.practitioner
                )
            )
        inpatient_record = final_patient_encounter.inpatient_record
        self.inpatient_record = inpatient_record
        self.patient_type_code = "OUT"
        if inpatient_record:
            discharge_date, date_admitted = frappe.get_value(
                "Inpatient Record",
                inpatient_record,
                ["discharge_date", "scheduled_date"],
            )
            self.patient_type_code = "IN"
            self.date_discharge = discharge_date
            self.date_admitted = date_admitted
        self.attendance_date = frappe.get_value(
            "Patient Appointment", self.patient_appointment, "appointment_date"
        )
        if self.date_discharge:
            self.claim_year = int(self.date_discharge.strftime("%Y"))
            self.claim_month = int(self.date_discharge.strftime("%m"))
        else:
            self.claim_year = int(self.attendance_date.strftime("%Y"))
            self.claim_month = int(self.attendance_date.strftime("%m"))
        self.patient_file_no = self.get_patient_file_no()
        if not self.allow_changes:
            self.set_patient_claim_disease()
            self.set_patient_claim_item()

    def get_patient_encounters(self):
        patient_encounters = frappe.get_all(
            "Patient Encounter",
            filters={
                "appointment": self.patient_appointment,
                "docstatus": 1,
            },
            order_by="`creation` ASC",
        )
        return patient_encounters

    def set_patient_claim_disease(self):
        self.nhif_patient_claim_disease = []
        preliminary_diagnosis_list = []
        for encounter in self.patient_encounters:
            encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)
            for row in encounter_doc.patient_encounter_preliminary_diagnosis:
                if row.medical_code in preliminary_diagnosis_list:
                    continue
                preliminary_diagnosis_list.append(row.medical_code)
                new_row = self.append("nhif_patient_claim_disease", {})
                new_row.diagnosis_type = "Provisional Diagnosis"
                new_row.status = "Provisional"
                new_row.patient_encounter = encounter.name
                new_row.codification_table = row.name
                new_row.medical_code = row.medical_code
                if row.code and len(row.code) > 3:
                    new_row.disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
                else:
                    new_row.disease_code = row.code[:3]
                new_row.description = row.description
                new_row.item_crt_by = get_fullname(row.modified_by)
                new_row.date_created = row.modified.strftime("%Y-%m-%d")
        final_diagnosis_list = []
        for encounter in self.patient_encounters:
            encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)
            for row in encounter_doc.patient_encounter_final_diagnosis:
                if row.medical_code in final_diagnosis_list:
                    continue
                final_diagnosis_list.append(row.medical_code)
                new_row = self.append("nhif_patient_claim_disease", {})
                new_row.diagnosis_type = "Final Diagnosis"
                new_row.status = "Final"
                new_row.patient_encounter = encounter.name
                new_row.codification_table = row.name
                new_row.medical_code = row.medical_code
                if row.code and len(row.code) > 3:
                    new_row.disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
                else:
                    new_row.disease_code = row.code[:3]
                new_row.description = row.description
                new_row.item_crt_by = get_fullname(row.modified_by)
                new_row.date_created = row.modified.strftime("%Y-%m-%d")

    def set_patient_claim_item(self):
        childs_map = [
            {
                "table": "lab_test_prescription",
                "doctype": "Lab Test Template",
                "item": "lab_test_code",
                "item_name": "lab_test_name",
                "comment": "lab_test_comment",
                "ref_doctype": "Lab Test",
                "ref_docname": "lab_test",
            },
            {
                "table": "radiology_procedure_prescription",
                "doctype": "Radiology Examination Template",
                "item": "radiology_examination_template",
                "item_name": "radiology_procedure_name",
                "comment": "radiology_test_comment",
                "ref_doctype": "Radiology Examination",
                "ref_docname": "radiology_examination",
            },
            {
                "table": "procedure_prescription",
                "doctype": "Clinical Procedure Template",
                "item": "procedure",
                "item_name": "procedure_name",
                "comment": "comments",
                "ref_doctype": "Clinical Procedure",
                "ref_docname": "clinical_procedure",
            },
            {
                "table": "drug_prescription",
                "doctype": "Medication",
                "item": "drug_code",
                "item_name": "drug_name",
                "comment": "comment",
                "ref_doctype": "Drug Prescription",
                "ref_docname": "name",
            },
            {
                "table": "therapies",
                "doctype": "Therapy Type",
                "item": "therapy_type",
                "item_name": "therapy_type",
                "comment": "comment",
                "ref_doctype": "",
                "ref_docname": "",
            },
        ]
        self.nhif_patient_claim_item = []
        final_patient_encounter = self.get_final_patient_encounter()
        inpatient_record = final_patient_encounter.inpatient_record
        is_inpatient = True if inpatient_record else False
        if not is_inpatient:
            for encounter in self.patient_encounters:
                encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)
                for child in childs_map:
                    for row in encounter_doc.get(child.get("table")):
                        if row.prescribe:
                            continue
                        item_code = frappe.get_value(
                            child.get("doctype"), row.get(child.get("item")), "item"
                        )
                        item_rate = get_item_rate(
                            item_code,
                            self.company,
                            encounter_doc.insurance_subscription,
                        )
                        new_row = self.append("nhif_patient_claim_item", {})
                        new_row.item_name = row.get(child.get("item_name"))
                        new_row.item_code = get_item_refcode(item_code)
                        new_row.item_quantity = row.get("quantity") or 1
                        new_row.unit_price = item_rate
                        new_row.amount_claimed = (
                            new_row.unit_price * new_row.item_quantity
                        )
                        new_row.approval_ref_no = get_approval_number_from_LRPMT(
                            child["ref_doctype"], row.get(child["ref_docname"])
                        )
                        new_row.patient_encounter = encounter.name
                        new_row.ref_doctype = row.doctype
                        new_row.ref_docname = row.name
                        new_row.folio_item_id = str(uuid.uuid1())
                        new_row.folio_id = self.folio_id
                        new_row.date_created = row.modified.strftime("%Y-%m-%d")
                        new_row.item_crt_by = get_fullname(row.modified_by)
        else:
            dates = []
            occupancy_list = []
            record_doc = frappe.get_doc("Inpatient Record", inpatient_record)
            for occupancy in record_doc.inpatient_occupancies:
                if not occupancy.is_confirmed:
                    continue
                checkin_date = occupancy.check_in.strftime("%Y-%m-%d")
                # Add only in occupancy once a day.
                if checkin_date not in dates:
                    dates.append(checkin_date)
                    occupancy_list.append(occupancy)
                service_unit_type = frappe.get_value(
                    "Healthcare Service Unit",
                    occupancy.service_unit,
                    "service_unit_type",
                )
                item_code = frappe.get_value(
                    "Healthcare Service Unit Type", service_unit_type, "item"
                )
                encounter_doc = frappe.get_doc(
                    "Patient Encounter", record_doc.admission_encounter
                )
                item_rate = get_item_rate(
                    item_code,
                    self.company,
                    encounter_doc.insurance_subscription,
                    encounter_doc.insurance_company,
                )
                new_row = self.append("nhif_patient_claim_item", {})
                new_row.item_name = occupancy.service_unit
                new_row.item_code = get_item_refcode(item_code)
                new_row.item_quantity = 1
                new_row.unit_price = item_rate
                new_row.amount_claimed = new_row.unit_price * new_row.item_quantity
                new_row.approval_ref_no = ""
                new_row.patient_encounter = encounter_doc.name
                new_row.ref_doctype = occupancy.doctype
                new_row.ref_docname = occupancy.name
                new_row.folio_item_id = str(uuid.uuid1())
                new_row.folio_id = self.folio_id
                new_row.date_created = occupancy.modified.strftime("%Y-%m-%d")
                new_row.item_crt_by = get_fullname(occupancy.modified_by)

            for occupancy in occupancy_list:
                if not occupancy.is_confirmed:
                    continue
                checkin_date = occupancy.check_in.strftime("%Y-%m-%d")
                service_unit_type = frappe.get_value(
                    "Healthcare Service Unit",
                    occupancy.service_unit,
                    "service_unit_type",
                )
                (is_service_chargeable, is_consultancy_chargeable) = frappe.get_value(
                    "Healthcare Service Unit Type",
                    service_unit_type,
                    ["is_service_chargeable", "is_consultancy_chargeable"],
                )
                encounter_doc = frappe.get_doc(
                    "Patient Encounter", record_doc.admission_encounter
                )
                item_code = frappe.get_value(
                    "Healthcare Service Unit Type", service_unit_type, "item"
                )
                if is_consultancy_chargeable:
                    for row_item in record_doc.inpatient_consultancy:
                        if (
                            row_item.is_confirmed
                            and str(row_item.date) == checkin_date
                            and row_item.rate
                        ):
                            item_code = row_item.consultation_item
                            new_row = self.append("nhif_patient_claim_item", {})
                            new_row.item_name = row_item.consultation_item
                            new_row.item_code = get_item_refcode(item_code)
                            new_row.item_quantity = 1
                            new_row.unit_price = row_item.rate
                            new_row.amount_claimed = row_item.rate
                            new_row.approval_ref_no = ""
                            new_row.patient_encounter = (
                                row_item.encounter or record_doc.admission_encounter
                            )
                            new_row.ref_doctype = row_item.doctype
                            new_row.ref_docname = row_item.name
                            new_row.folio_item_id = str(uuid.uuid1())
                            new_row.folio_id = self.folio_id
                            new_row.date_created = row_item.modified.strftime(
                                "%Y-%m-%d"
                            )
                            new_row.item_crt_by = get_fullname(row_item.modified_by)
                if is_service_chargeable:
                    for encounter in self.patient_encounters:
                        encounter_doc = frappe.get_doc(
                            "Patient Encounter", encounter.name
                        )
                        if str(encounter_doc.encounter_date) != checkin_date:
                            continue
                        for child in childs_map:
                            for row in encounter_doc.get(child.get("table")):
                                if row.prescribe:
                                    continue
                                item_code = frappe.get_value(
                                    child.get("doctype"),
                                    row.get(child.get("item")),
                                    "item",
                                )
                                item_rate = get_item_rate(
                                    item_code,
                                    self.company,
                                    encounter_doc.insurance_subscription,
                                    encounter_doc.insurance_company,
                                )
                                new_row = self.append("nhif_patient_claim_item", {})
                                new_row.item_name = row.get(child.get("item"))
                                new_row.item_code = get_item_refcode(item_code)
                                new_row.item_quantity = row.get("quantity") or 1
                                new_row.unit_price = item_rate
                                new_row.amount_claimed = (
                                    new_row.unit_price * new_row.item_quantity
                                )
                                new_row.approval_ref_no = (
                                    get_approval_number_from_LRPMT(
                                        child["ref_doctype"],
                                        row.get(child["ref_docname"]),
                                    )
                                )
                                new_row.patient_encounter = encounter.name
                                new_row.ref_doctype = row.doctype
                                new_row.ref_docname = row.name
                                new_row.folio_item_id = str(uuid.uuid1())
                                new_row.folio_id = self.folio_id
                                new_row.date_created = row.modified.strftime("%Y-%m-%d")
                                new_row.item_crt_by = get_fullname(row.modified_by)

        sorted_patient_claim_item = sorted(
            self.nhif_patient_claim_item, key=lambda k: k.get("ref_doctype")
        )
        idx = 2
        for row in sorted_patient_claim_item:
            row.idx = idx
            idx += 1
        self.nhif_patient_claim_item = sorted_patient_claim_item

        patient_appointment_doc = frappe.get_doc(
            "Patient Appointment", self.patient_appointment
        )
        if not is_inpatient and not patient_appointment_doc.follow_up:
            item_code = patient_appointment_doc.billing_item
            item_rate = get_item_rate(
                item_code,
                self.company,
                patient_appointment_doc.insurance_subscription,
                patient_appointment_doc.insurance_company,
            )
            new_row = self.append("nhif_patient_claim_item", {})
            new_row.item_name = patient_appointment_doc.billing_item
            new_row.item_code = get_item_refcode(item_code)
            new_row.item_quantity = 1
            new_row.unit_price = item_rate
            new_row.amount_claimed = item_rate
            new_row.approval_ref_no = ""
            new_row.ref_doctype = patient_appointment_doc.doctype
            new_row.ref_docname = patient_appointment_doc.name
            new_row.folio_item_id = str(uuid.uuid1())
            new_row.folio_id = self.folio_id
            new_row.date_created = patient_appointment_doc.modified.strftime("%Y-%m-%d")
            new_row.item_crt_by = get_fullname(patient_appointment_doc.modified_by)
            new_row.idx = 1

    def get_final_patient_encounter(self):
        patient_encounter_list = frappe.get_all(
            "Patient Encounter",
            filters={
                "appointment": self.patient_appointment,
                "docstatus": 1,
                "encounter_type": "Final",
            },
            fields={"*"},
        )
        if len(patient_encounter_list) == 0:
            frappe.throw(_("There no Final Patient Encounter for this Appointment"))
        return patient_encounter_list[0]

    def get_patient_file_no(self):
        patient_file_no = self.patient
        return patient_file_no

    def get_folio_json_data(self):
        folio_data = frappe._dict()
        folio_data.entities = []
        entities = frappe._dict()
        entities.ClaimYear = self.claim_year
        entities.ClaimMonth = self.claim_month
        entities.FolioNo = self.folio_no
        entities.SerialNo = self.serial_no
        entities.FacilityCode = self.facility_code
        entities.CardNo = self.cardno.strip()
        entities.FirstName = self.first_name
        entities.LastName = self.last_name
        entities.Gender = self.gender
        entities.DateOfBirth = str(self.date_of_birth)
        entities.PatientFileNo = self.patient_file_no
        entities.PatientFile = self.patient_file
        entities.ClaimFile = self.claim_file
        entities.ClinicalNotes = self.clinical_notes
        entities.AuthorizationNo = self.authorization_no
        entities.AttendanceDate = str(self.attendance_date)
        entities.PatientTypeCode = self.patient_type_code
        if self.patient_type_code == "IN":
            entities.DateAdmitted = str(self.date_admitted)
            entities.DateDischarged = str(self.date_discharge)
        entities.PractitionerNo = self.practitioner_no
        entities.CreatedBy = self.item_crt_by
        entities.DateCreated = str(self.posting_date)

        entities.FolioDiseases = []
        for disease in self.nhif_patient_claim_disease:
            FolioDisease = frappe._dict()
            FolioDisease.Status = disease.status
            FolioDisease.DiseaseCode = disease.disease_code
            FolioDisease.Remarks = None
            FolioDisease.CreatedBy = disease.item_crt_by
            FolioDisease.DateCreated = str(disease.date_created)
            entities.FolioDiseases.append(FolioDisease)

        entities.FolioItems = []
        for item in self.nhif_patient_claim_item:
            FolioItem = frappe._dict()
            FolioItem.ItemCode = item.item_code
            FolioItem.ItemQuantity = item.item_quantity
            FolioItem.UnitPrice = item.unit_price
            FolioItem.AmountClaimed = item.amount_claimed
            FolioItem.ApprovalRefNo = item.approval_ref_no or None
            FolioItem.CreatedBy = item.item_crt_by
            FolioItem.DateCreated = str(item.date_created)
            entities.FolioItems.append(FolioItem)

        folio_data.entities.append(entities)
        jsonStr = json.dumps(folio_data)
        return jsonStr

    def send_nhif_claim(self):
        json_data = self.get_folio_json_data()
        token = get_claimsservice_token(self.company)
        claimsserver_url = frappe.get_value(
            "Company NHIF Settings", self.company, "claimsserver_url"
        )
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        url = str(claimsserver_url) + "/claimsserver/api/v1/Claims/SubmitFolios"
        r = requests.post(url, headers=headers, data=json_data, timeout=300)
        if r.status_code != 200:
            add_log(
                request_type="SubmitFolios",
                request_url=url,
                request_header=headers,
                request_body=json_data,
                response_data=str(r.text) if r.text else str(r),
                status_code=r.status_code,
            )
            if "has already been submitted." in str(r.text):
                frappe.msgprint(str(r.text) if r.text else str(r))
            else:
                frappe.throw(str(r.text) if r.text else str(r))
        else:
            frappe.msgprint(str(r.text))
            if r.text:
                add_log(
                    request_type="SubmitFolios",
                    request_url=url,
                    request_header=headers,
                    request_body=json_data,
                    response_data=r.text,
                    status_code=r.status_code,
                )
            frappe.msgprint(_("The claim has been sent successfully"), alert=True)

    def calculate_totals(self):
        self.total_amount = 0
        for item in self.nhif_patient_claim_item:
            item.amount_claimed = item.unit_price * item.item_quantity
            item.folio_item_id = item.folio_item_id or str(uuid.uuid1())
            item.date_created = item.date_created or nowdate()
            item.folio_id = item.folio_id or self.folio_id
            self.total_amount += item.amount_claimed
        for item in self.nhif_patient_claim_disease:
            item.folio_id = item.folio_id or self.folio_id
            item.folio_disease_id = item.folio_disease_id or str(uuid.uuid1())
            item.date_created = item.date_created or nowdate()

    def set_clinical_notes(self):
        self.clinical_notes = ""
        for patient_encounter in self.patient_encounters:
            examination_detail = (
                frappe.get_value(
                    "Patient Encounter", patient_encounter.name, "examination_detail"
                )
                or ""
            )
            if not examination_detail:
                frappe.msgprint(
                    _(
                        "Encounter {0} does not have Examination Details defined. Check the encounter.".format(
                            patient_encounter
                        )
                    ),
                    alert=True,
                )
                # return
            self.clinical_notes += examination_detail or ""
            self.clinical_notes += "\n"

@frappe.whitelist()
def merge_nhif_claims(authorization_no):    
    claim_details = frappe.get_all(
        "NHIF Patient Claim",
        filters={"authorization_no": authorization_no, "docstatus": 0},
        fields=["name"],
    )

    if len(claim_details) == 1:
        frappe.throw("This Authorization No.: {0} was used only once on NHIF Patient Claim: {1}".format(
            frappe.bold(authorization_no),
            frappe.bold(claim_details[0]["name"])
        ))
    
    first_doc = frappe.get_doc("NHIF Patient Claim", claim_details[0]["name"])
    second_doc = frappe.get_doc("NHIF Patient Claim", claim_details[1]["name"])

    diseases_no = len(first_doc.nhif_patient_claim_disease)
    items_no = len(first_doc.nhif_patient_claim_item)

    if second_doc.nhif_patient_claim_disease:
        for row in second_doc.nhif_patient_claim_disease:
            first_doc.append("nhif_patient_claim_disease", {
            "diagnosis_type": row.diagnosis_type,
            "status": row.status,
            "patient_encounter": row.patient_encounter,
            "codification_table": row.codification_table,
            "medical_code": row.medical_code,
            "disease_code": row.disease_code,
            "description": row.description,
            "item_crt_by": row.item_crt_by,
            "date_created": row.date_created,
            "parent": first_doc.name,
            "parenttype": row.parenttype
            })
        first_doc.save(ignore_permissions=True)

    if len(first_doc.nhif_patient_claim_disease) > diseases_no:
        frappe.msgprint("NHIF Patient Claim Diseases merged successfully \
            from Claim: {0} to Claim: {1}".format(
                frappe.bold(second_doc.name),
                frappe.bold(first_doc.name)
            ))

    if second_doc.nhif_patient_claim_item:
        for row in second_doc.nhif_patient_claim_item:
            first_doc.append("nhif_patient_claim_item", {
                "item_name": row.item_name,
                "item_code": row.item_code,
                "item_quantity": row.item_quantity,
                "unit_price": row.unit_price,
                "amount_claimed": row.amount_claimed,
                "approval_ref_no": row.approval_ref_no,
                "patient_encounter": row.patient_encounter,
                "ref_doctype": row.ref_doctype,
                "ref_docname": row.ref_docname,
                "folio_item_id": row.folio_item_id,
                "folio_id": row.folio_id,
                "date_created": row.date_created,
                "item_crt_by": row.item_crt_by,
                "parent": first_doc.name,
                "parenttype": row.parenttype
            })
        first_doc.save(ignore_permissions=True)

    if len(first_doc.nhif_patient_claim_item) > items_no:
        frappe.msgprint("NHIF Patient Claim Items merged successfully \
            from Claim: {0} to Claim: {1}".format(
                frappe.bold(second_doc.name),
                frappe.bold(first_doc.name)
            ))
    
    frappe.delete_doc(second_doc.doctype, second_doc.name)
    
    claim = frappe.get_doc("NHIF Patient Claim", second_doc.name)
    if not claim:
        frappe.msgprint("NHIF Patient Claim: {0} was deleted successfully.".format(
            frappe.bold(second_doc.name)
        ))
    else:
        frappe.msgprint("NHIF Patient Claim: {0} was not deleted, please try again or Seek \
            assistance from IT Office.".format(
                frappe.bold(second_doc.name)
            ))

def get_item_refcode(item_code):
    code_list = frappe.get_all(
        "Item Customer Detail",
        filters={"parent": item_code, "customer_name": "NHIF"},
        fields=["ref_code"],
    )
    if len(code_list) == 0:
        frappe.throw(_("Item {0} has not NHIF Code Reference").format(item_code))
    ref_code = code_list[0].ref_code
    if not ref_code:
        frappe.throw(_("Item {0} has not NHIF Code Reference").format(item_code))
    return ref_code


def generate_pdf(doc):
    doc_name = doc.name
    file_list = frappe.get_all("File", filters={"attached_to_name": doc_name})
    for file in file_list:
        frappe.delete_doc("File", file.name)
    data_list = []
    data = doc.patient_encounters
    for i in data:
        data_list.append(i.name)
    doctype = dict({"Patient Encounter": data_list})
    print_format = ""
    default_print_format = frappe.db.get_value(
        "Property Setter",
        dict(property="default_print_format", doc_type="Patient Encounter"),
        "value",
    )
    if default_print_format:
        print_format = default_print_format
    else:
        print_format = "Patient File"

    pdf = download_multi_pdf(doctype, doc_name, format=print_format, no_letterhead=1)
    if pdf:
        ret = frappe.get_doc(
            {
                "doctype": "File",
                "attached_to_doctype": "NHIF Patient Claim",
                "attached_to_name": doc_name,
                "folder": "Home/Attachments",
                "file_name": doc_name + ".pdf",
                "file_url": "/private/files/" + doc_name + ".pdf",
                "content": pdf,
                "is_private": 1,
            }
        )
        ret.save(ignore_permissions=1)
        ret.db_update()
        base64_data = to_base64(pdf)
        return base64_data


def download_multi_pdf(doctype, name, format=None, no_letterhead=0):
    output = PdfFileWriter()
    if isinstance(doctype, dict):
        for doctype_name in doctype:
            for doc_name in doctype[doctype_name]:
                try:
                    output = frappe.get_print(
                        doctype_name,
                        doc_name,
                        format,
                        as_pdf=True,
                        output=output,
                        no_letterhead=no_letterhead,
                    )
                except Exception:
                    frappe.log_error(frappe.get_traceback())
        frappe.local.response.filename = "{}.pdf".format(name)

    return read_multi_pdf(output)


def read_multi_pdf(output):
    fname = os.path.join("/tmp", "frappe-pdf-{0}.pdf".format(frappe.generate_hash()))
    output.write(open(fname, "wb"))

    with open(fname, "rb") as fileobj:
        filedata = fileobj.read()

    return filedata


def get_claim_pdf_file(doc):
    try:
        doctype = doc.doctype
        docname = doc.name
        default_print_format = frappe.db.get_value(
            "Property Setter",
            dict(property="default_print_format", doc_type=doctype),
            "value",
        )
        if default_print_format:
            print_format = default_print_format
        else:
            print_format = "NHIF Form 2A & B"

        # print_format = "NHIF Form 2A & B"

        html = frappe.get_print(
            doctype, docname, print_format, doc=None, no_letterhead=1
        )

        filename = "{name}-claim".format(
            name=docname.replace(" ", "-").replace("/", "-")
        )
        pdf = get_pdf(html)
        if pdf:
            ret = frappe.get_doc(
                {
                    "doctype": "File",
                    "attached_to_doctype": doc.doctype,
                    "attached_to_name": docname,
                    "folder": "Home/Attachments",
                    "file_name": filename + ".pdf",
                    "file_url": "/private/files/" + filename + ".pdf",
                    "content": pdf,
                    "is_private": 1,
                }
            )
            ret.save(ignore_permissions=1)
            ret.db_update()
            base64_data = to_base64(pdf)
            return base64_data

    except Exception:
        frappe.log_error(frappe.get_traceback())
