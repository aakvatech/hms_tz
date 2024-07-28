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
from frappe.utils import (
    getdate,
    get_fullname,
    nowdate,
    nowtime,
    get_datetime,
    time_diff_in_seconds,
    now_datetime,
    cint,
    get_url_to_form,
    get_time,
)
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.healthcare_utils import (
    get_item_rate,
    to_base64,
    get_approval_number_from_LRPMT,
)
import os
from frappe.utils.pdf import get_pdf
from PyPDF2 import PdfFileWriter
from hms_tz.nhif.doctype.nhif_tracking_claim_change.nhif_tracking_claim_change import (
    track_changes_of_claim_items,
)


class NHIFPatientClaim(Document):
    def validate(self):
        if self.docstatus != 0:
            return

        self.validate_appointment_info()
        self.patient_encounters = self.get_patient_encounters()
        if not self.patient_encounters:
            frappe.throw(_("There are no submitted encounters for this application"))
        if not self.allow_changes:
            from hms_tz.nhif.api.patient_encounter import finalized_encounter

            finalized_encounter(self.patient_encounters[-1])
            self.final_patient_encounter = self.get_final_patient_encounter()
            self.set_claim_values()
        else:
            self.final_patient_encounter = self.get_final_patient_encounter()
        self.calculate_totals()
        # self.set_clinical_notes()
        if not self.is_new():
            update_original_patient_claim(self)

            frappe.db.sql(
                "UPDATE `tabPatient Appointment` SET nhif_patient_claim = '' WHERE nhif_patient_claim = '{0}'".format(
                    self.name
                )
            )
            frappe.db.sql(
                "UPDATE `tabPatient Appointment` SET nhif_patient_claim = '{0}' WHERE name = '{1}'".format(
                    self.name, self.patient_appointment
                )
            )

    def on_trash(self):
        # check if claim number exist in appointment record
        nhif_patient_claim = frappe.get_value(
            "Patient Appointment", self.patient_appointment, "nhif_patient_claim"
        )
        if nhif_patient_claim == self.name:
            frappe.db.set_value(
                "Patient Appointment",
                self.patient_appointment,
                "nhif_patient_claim",
                "",
            )

    def before_submit(self):
        try:
            if len(self.nhif_patient_claim_disease) == 0:
                frappe.throw(
                    _(
                        "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>Please add at least one disease code, before submitting this claim<h4>"
                    )
                )
            if len(self.nhif_patient_claim_item) == 0:
                frappe.throw(
                    _(
                        "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>Please add at least one item, before submitting this claim<h4>"
                    )
                )

            if self.total_amount != sum(
                [item.amount_claimed for item in self.nhif_patient_claim_item]
            ):
                frappe.throw(
                    _(
                        "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>Total amount does not match with the total of the items<h4>"
                    )
                )
        except Exception as e:
            self.add_comment(
                comment_type="Comment",
                text=str(e),
            )
            frappe.db.commit()
            frappe.throw("")

        start_datetime = get_datetime()
        frappe.msgprint("Submit process started: " + str(get_datetime()))

        self.validate_multiple_appointments_per_authorization_no()

        validate_item_status(self)
        self.patient_encounters = self.get_patient_encounters()
        if not self.patient_signature:
            get_missing_patient_signature(self)

        validate_submit_date(self)

        # self.claim_file_mem = get_claim_pdf_file(self)
        frappe.msgprint("Sending NHIF Claim: " + str(get_datetime()))
        self.send_nhif_claim()
        frappe.msgprint("Got response from NHIF Claim: " + str(get_datetime()))
        end_datetime = get_datetime()
        time_in_seconds = time_diff_in_seconds(str(end_datetime), str(start_datetime))
        frappe.msgprint(
            "Total time to complete the process in seconds = " + str(time_in_seconds)
        )

    def on_submit(self):
        track_changes_of_claim_items(self)

    def validate_multiple_appointments_per_authorization_no(self, caller=None):
        """Validate if patient gets multiple appointments with same authorization number"""

        # Check if there are multiple claims with same authorization number
        claim_details = frappe.get_all(
            "NHIF Patient Claim",
            filters={
                "patient": self.patient,
                "authorization_no": self.authorization_no,
                "cardno": self.cardno,
                "docstatus": 0,
            },
            fields=["name", "patient", "patient_name", "hms_tz_claim_appointment_list"],
        )
        claim_name_list = ""
        merged_appointments = []
        for claim in claim_details:
            url = get_url_to_form("NHIF Patient Claim", claim["name"])
            claim_name_list += f"<a href='{url}'><b>{claim['name']}</b> </a> , "
            if claim["hms_tz_claim_appointment_list"]:
                merged_appointments += json.loads(
                    claim["hms_tz_claim_appointment_list"]
                )

        if len(claim_details) > 1 and not caller:
            frappe.throw(
                f"<p style='text-align: justify; font-size: 14px;'>This Authorization Number: <b>{self.authorization_no}</b> has used multiple times in NHIF Patient Claim: {claim_name_list}. \
                Please merge these <b>{len(claim_details)}</b> claims to Proceed</p>"
            )

        # rock: 139
        # Check if there are multiple appointments with same authorization number
        appointment_documents = frappe.get_all(
            "Patient Appointment",
            filters={
                "patient": self.patient,
                "authorization_number": self.authorization_no,
                "coverage_plan_card_number": self.cardno,
                "status": ["!=", "Cancelled"],
            },
            pluck="name",
        )

        if len(appointment_documents) > 1:
            validate_hold_card_status(
                self, appointment_documents, claim_details, merged_appointments, caller
            )
        else:
            if caller:
                frappe.msgprint("Release Patient Card", 20, alert=True)

    def set_claim_values(self):
        if not self.folio_id:
            self.folio_id = str(uuid.uuid1())
        self.facility_code = frappe.get_cached_value(
            "Company Insurance Setting", {"company": self.company, "insurance_provider": "NHIF"}, "facility_code"
        )
        self.posting_date = nowdate()
        self.serial_no = int(self.name[-9:])
        self.item_crt_by = get_fullname(frappe.session.user)
        # rock: 173
        practitioners = [d.practitioner for d in self.final_patient_encounter]
        practitioner_details = frappe.get_all(
            "Healthcare Practitioner",
            {"name": ["in", practitioners]},
            ["practitioner_name", "tz_mct_code"],
        )
        if not practitioner_details[0].practitioner_name:
            frappe.throw(
                _(
                    f"There is no Practitioner Name for Practitioner: {practitioner_details[0].practitioner_name}"
                )
            )

        if not practitioner_details[0].tz_mct_code:
            frappe.throw(
                _(
                    f"There is no TZ MCT Code for Practitioner {practitioner_details[0].practitioner_name}"
                )
            )

        self.practitioner_name = practitioner_details[0].practitioner_name
        self.practitioner_no = ",".join([d.tz_mct_code for d in practitioner_details])
        inpatient_record = [
            h.inpatient_record
            for h in self.final_patient_encounter
            if h.inpatient_record
        ] or None
        self.inpatient_record = inpatient_record[0] if inpatient_record else None
        # Reset values for every validate
        self.patient_type_code = "OUT"
        self.date_admitted = None
        self.admitted_time = None
        self.date_discharge = None
        self.discharge_time = None
        if self.inpatient_record:
            (
                discharge_date,
                scheduled_date,
                admitted_datetime,
                time_created,
            ) = frappe.get_value(
                "Inpatient Record",
                self.inpatient_record,
                ["discharge_date", "scheduled_date", "admitted_datetime", "creation"],
            )

            if getdate(scheduled_date) < getdate(admitted_datetime):
                self.date_admitted = scheduled_date
                self.admitted_time = get_time(get_datetime(time_created))
            else:
                self.date_admitted = getdate(admitted_datetime)
                self.admitted_time = get_time(get_datetime(admitted_datetime))

            # If the patient is same day discharged then consider it as Outpatient
            if self.date_admitted == getdate(discharge_date):
                self.patient_type_code = "OUT"
                self.date_admitted = None
            else:
                self.patient_type_code = "IN"
                self.date_discharge = discharge_date

                # the time claim is created will treated as discharge time
                # because there is no field of discharge time on Inpatient Record
                self.discharge_time = nowtime()

        self.attendance_date, self.attendance_time = frappe.get_value(
            "Patient Appointment",
            self.patient_appointment,
            ["appointment_date", "appointment_time"],
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
            self.set_patient_claim_item(self.inpatient_record)

    @frappe.whitelist()
    def get_appointments(self):
        appointment_list = frappe.get_all(
            "NHIF Patient Claim",
            filters={
                "patient": self.patient,
                "authorization_no": self.authorization_no,
                "cardno": self.cardno,
            },
            fields=["patient_appointment", "hms_tz_claim_appointment_list"],
        )
        if len(appointment_list) == 1:
            frappe.throw(
                _(
                    "<p style='text-align: center; font-size: 12pt; background-color: #FFD700;'>\
                <strong>This Authorization no: {0} was used only once on <br> NHIF Patient Claim: {1} </strong>\
                </p>".format(
                        frappe.bold(self.authorization_no), frappe.bold(self.name)
                    )
                )
            )
        app_list = []
        for app_name in appointment_list:
            if app_name["hms_tz_claim_appointment_list"]:
                app_numbers = json.loads(app_name["hms_tz_claim_appointment_list"])
                app_list += app_numbers

                for d in app_numbers:
                    frappe.db.set_value(
                        "Patient Appointment",
                        d,
                        "nhif_patient_claim",
                        self.name,
                    )
            else:
                app_list.append(app_name["patient_appointment"])
                frappe.db.set_value(
                    "Patient Appointment",
                    app_name["patient_appointment"],
                    "nhif_patient_claim",
                    self.name,
                )
        app_list = list(set(app_list))
        self.allow_changes = 0
        self.hms_tz_claim_appointment_list = json.dumps(app_list)

        self.save(ignore_permissions=True)

    def get_patient_encounters(self):
        if not self.hms_tz_claim_appointment_list:
            patient_appointment = self.patient_appointment
        else:
            patient_appointment = ["in", json.loads(self.hms_tz_claim_appointment_list)]

        patient_encounters = frappe.get_all(
            "Patient Encounter",
            filters={
                "appointment": patient_appointment,
                "docstatus": 1,
            },
            fields={"name", "encounter_date"},
            order_by="`creation` ASC",
        )
        return patient_encounters

    def set_patient_claim_disease(self):
        self.nhif_patient_claim_disease = []
        preliminary_query_string = """
            SELECT ct.name, ct.parent, ct.code, ct.medical_code, ct.description, ct.modified_by, ct.modified, pe.practitioner
            FROM `tabCodification Table` ct
            INNER JOIN `tabPatient Encounter` pe ON pe.name = ct.parent
            WHERE ct.parentfield = "patient_encounter_preliminary_diagnosis"
            AND ct.parenttype = "Patient Encounter"
            AND ct.parent in ({})
            GROUP BY ct.medical_code
            """.format(
            ", ".join(
                frappe.db.escape(encounters.name)
                for encounters in self.patient_encounters
            )
        )

        preliminary_diagnosis_list = frappe.db.sql(
            preliminary_query_string, as_dict=True
        )
        for row in preliminary_diagnosis_list:
            new_row = self.append("nhif_patient_claim_disease", {})
            new_row.diagnosis_type = "Provisional Diagnosis"
            new_row.status = "Provisional"
            new_row.patient_encounter = row.parent
            new_row.codification_table = row.name
            new_row.medical_code = row.medical_code
            # Convert the ICD code of CDC to NHIF
            if row.code and len(row.code) > 3 and "." not in row.code:
                new_row.disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
            elif row.code and len(row.code) <= 5 and "." in row.code:
                new_row.disease_code = row.code
            else:
                new_row.disease_code = row.code[:3]
            new_row.description = row.description[0:139]
            new_row.item_crt_by = row.practitioner
            new_row.date_created = row.modified.strftime("%Y-%m-%d")

        final_query_string = """
            SELECT ct.name, ct.parent, ct.code, ct.medical_code, ct.description, ct.modified_by, ct.modified, pe.practitioner
            FROM `tabCodification Table` ct
            INNER JOIN `tabPatient Encounter` pe ON pe.name = ct.parent
            WHERE ct.parentfield = "patient_encounter_final_diagnosis"
            AND ct.parenttype = "Patient Encounter"
            AND ct.parent in ({})
            GROUP BY ct.medical_code
            """.format(
            ", ".join(
                frappe.db.escape(encounters.name)
                for encounters in self.patient_encounters
            )
        )

        final_diagnosis_list = frappe.db.sql(final_query_string, as_dict=True)
        for row in final_diagnosis_list:
            new_row = self.append("nhif_patient_claim_disease", {})
            new_row.diagnosis_type = "Final Diagnosis"
            new_row.status = "Final"
            new_row.patient_encounter = row.parent
            new_row.codification_table = row.name
            new_row.medical_code = row.medical_code
            # Convert the ICD code of CDC to NHIF
            if row.code and len(row.code) > 3 and "." not in row.code:
                new_row.disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
            elif row.code and len(row.code) <= 5 and "." in row.code:
                new_row.disease_code = row.code
            else:
                new_row.disease_code = row.code[:3]
            new_row.description = row.description[0:139]
            new_row.item_crt_by = row.practitioner
            new_row.date_created = row.modified.strftime("%Y-%m-%d")

    def set_patient_claim_item(self, inpatient_record=None, called_method=None):
        if called_method == "enqueue":
            self.reload()
            self.final_patient_encounter = self.get_final_patient_encounter()
            self.patient_encounters = self.get_patient_encounters()
        childs_map = get_child_map()
        self.nhif_patient_claim_item = []
        self.clinical_notes = ""
        if not inpatient_record:
            for encounter in self.patient_encounters:
                encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)

                self.set_clinical_notes(encounter_doc)

                for child in childs_map:
                    for row in encounter_doc.get(child.get("table")):
                        if row.prescribe or row.is_cancelled:
                            continue

                        item_code = frappe.get_value(
                            child.get("doctype"), row.get(child.get("item")), "item"
                        )

                        delivered_quantity = 0
                        if row.get("doctype") == "Drug Prescription":
                            delivered_quantity = (row.get("quantity") or 0) - (
                                row.get("quantity_returned") or 0
                            )
                        elif row.get("doctype") == "Therapy Plan Detail":
                            delivered_quantity = (row.get("no_of_sessions") or 0) - (
                                row.get("sessions_cancelled") or 0
                            )
                        else:
                            delivered_quantity = 1

                        new_row = self.append("nhif_patient_claim_item", {})
                        new_row.item_name = row.get(child.get("item_name"))
                        new_row.item_code = get_item_refcode(item_code)
                        new_row.item_quantity = delivered_quantity or 1
                        new_row.unit_price = row.get("amount")
                        new_row.amount_claimed = (
                            new_row.unit_price * new_row.item_quantity
                        )
                        new_row.approval_ref_no = get_approval_number_from_LRPMT(
                            child["ref_doctype"], row.get(child["ref_docname"])
                        )

                        new_row.status = get_LRPMT_status(encounter.name, row, child)
                        new_row.patient_encounter = encounter.name
                        new_row.ref_doctype = row.doctype
                        new_row.ref_docname = row.name
                        new_row.folio_item_id = str(uuid.uuid1())
                        new_row.folio_id = self.folio_id
                        new_row.date_created = row.modified.strftime("%Y-%m-%d")
                        new_row.item_crt_by = encounter_doc.practitioner
        else:
            dates = []
            occupancy_list = []
            record_doc = frappe.get_doc("Inpatient Record", inpatient_record)

            admission_encounter_doc = frappe.get_doc(
                "Patient Encounter", record_doc.admission_encounter
            )
            for occupancy in record_doc.inpatient_occupancies:
                if not occupancy.is_confirmed:
                    continue

                service_unit_type = frappe.get_cached_value(
                    "Healthcare Service Unit",
                    occupancy.service_unit,
                    "service_unit_type",
                )

                (
                    is_service_chargeable,
                    is_consultancy_chargeable,
                    item_code,
                ) = frappe.get_cached_value(
                    "Healthcare Service Unit Type",
                    service_unit_type,
                    ["is_service_chargeable", "is_consultancy_chargeable", "item"],
                )

                # update occupancy object
                occupancy.update(
                    {
                        "service_unit_type": service_unit_type,
                        "is_service_chargeable": is_service_chargeable,
                        "is_consultancy_chargeable": is_consultancy_chargeable,
                    }
                )

                checkin_date = occupancy.check_in.strftime("%Y-%m-%d")
                # Add only in occupancy once a day.
                if checkin_date not in dates:
                    dates.append(checkin_date)
                    occupancy_list.append(occupancy)

                item_rate = get_item_rate(
                    item_code,
                    self.company,
                    admission_encounter_doc.insurance_subscription,
                    admission_encounter_doc.insurance_company,
                )
                new_row = self.append("nhif_patient_claim_item", {})
                new_row.item_name = occupancy.service_unit
                new_row.item_code = get_item_refcode(item_code)
                new_row.item_quantity = 1
                new_row.unit_price = item_rate
                new_row.amount_claimed = new_row.unit_price * new_row.item_quantity
                new_row.approval_ref_no = ""
                new_row.patient_encounter = admission_encounter_doc.name
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

                if occupancy.is_consultancy_chargeable:
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

                for encounter in self.patient_encounters:
                    if str(encounter.encounter_date) != checkin_date:
                        continue
                    encounter_doc = frappe.get_doc("Patient Encounter", encounter.name)

                    # allow clinical notes to be added to the claim even if the service is not chargeable and encounters will be ignored
                    self.set_clinical_notes(encounter_doc)

                    if not occupancy.is_service_chargeable:
                        continue

                    for child in childs_map:
                        for row in encounter_doc.get(child.get("table")):
                            if row.prescribe or row.is_cancelled:
                                continue

                            item_code = frappe.get_value(
                                child.get("doctype"),
                                row.get(child.get("item")),
                                "item",
                            )

                            delivered_quantity = 0
                            if row.get("doctype") == "Drug Prescription":
                                delivered_quantity = (row.get("quantity") or 0) - (
                                    row.get("quantity_returned") or 0
                                )
                            elif row.get("doctype") == "Therapy Plan Detail":
                                delivered_quantity = (
                                    row.get("no_of_sessions") or 0
                                ) - (row.get("sessions_cancelled") or 0)
                            else:
                                delivered_quantity = 1

                            new_row = self.append("nhif_patient_claim_item", {})
                            new_row.item_name = row.get(child.get("item"))
                            new_row.item_code = get_item_refcode(item_code)
                            new_row.item_quantity = delivered_quantity or 1
                            new_row.unit_price = row.get("amount")
                            new_row.amount_claimed = (
                                new_row.unit_price * new_row.item_quantity
                            )
                            new_row.approval_ref_no = get_approval_number_from_LRPMT(
                                child["ref_doctype"],
                                row.get(child["ref_docname"]),
                            )

                            new_row.status = get_LRPMT_status(
                                encounter.name, row, child
                            )

                            new_row.patient_encounter = encounter.name
                            new_row.ref_doctype = row.doctype
                            new_row.ref_docname = row.name
                            new_row.folio_item_id = str(uuid.uuid1())
                            new_row.folio_id = self.folio_id
                            new_row.date_created = row.modified.strftime("%Y-%m-%d")
                            new_row.item_crt_by = encounter_doc.practitioner

        patient_appointment_list = []
        if not self.hms_tz_claim_appointment_list:
            patient_appointment_list.append(self.patient_appointment)
        else:
            patient_appointment_list = json.loads(self.hms_tz_claim_appointment_list)

        sorted_patient_claim_item = sorted(
            self.nhif_patient_claim_item,
            key=lambda k: (
                k.get("ref_doctype"),
                k.get("item_code"),
                k.get("date_created"),
            ),
        )
        idx = len(patient_appointment_list) + 1
        for row in sorted_patient_claim_item:
            row.idx = idx
            idx += 1
        self.nhif_patient_claim_item = sorted_patient_claim_item

        appointment_idx = 1
        for appointment_no in patient_appointment_list:
            patient_appointment_doc = frappe.get_doc(
                "Patient Appointment", appointment_no
            )

            # SHM Rock: 202
            if patient_appointment_doc.has_no_consultation_charges == 1:
                continue

            if not inpatient_record and not patient_appointment_doc.follow_up:
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
                new_row.date_created = patient_appointment_doc.modified.strftime(
                    "%Y-%m-%d"
                )
                new_row.item_crt_by = get_fullname(patient_appointment_doc.modified_by)
                new_row.idx = appointment_idx
                appointment_idx += 1

    def get_final_patient_encounter(self):
        # rock 173
        appointment = None
        if self.hms_tz_claim_appointment_list:
            appointment = ["in", json.loads(self.hms_tz_claim_appointment_list)]
        else:
            appointment = self.patient_appointment

        patient_encounter_list = frappe.get_all(
            "Patient Encounter",
            filters={
                "appointment": appointment,
                "docstatus": 1,
                "duplicated": 0,
                "encounter_type": "Final",
            },
            fields=["name", "practitioner", "inpatient_record"],
            order_by="`modified` desc",
            # limit_page_length=1,
        )
        if len(patient_encounter_list) == 0:
            frappe.throw(_("There no Final Patient Encounter for this Appointment"))
        return patient_encounter_list

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
        # entities.PatientFile = generate_pdf(self)
        entities.ClaimFile = get_claim_pdf_file(self)
        entities.ClinicalNotes = self.clinical_notes
        entities.AuthorizationNo = self.authorization_no
        entities.AttendanceDate = str(self.attendance_date)
        entities.PatientTypeCode = self.patient_type_code
        if self.patient_type_code == "IN":
            entities.DateAdmitted = (
                str(self.date_admitted) + " " + str(self.admitted_time)
            )
            entities.DateDischarged = (
                str(self.date_discharge) + " " + str(self.discharge_time)
            )
        entities.PractitionerName = self.practitioner_name
        entities.PractitionerNo = self.practitioner_no
        entities.CreatedBy = self.item_crt_by
        entities.DateCreated = str(self.posting_date)
        entities.BillNo = self.name
        entities.LateSubmissionReason = self.delayreason

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

        # Strip off the patient file
        folio_data.entities[0].PatientFile = "Stripped off"
        folio_data.entities[0].ClaimFile = "Stripped off"
        jsonStr_wo_files = json.dumps(folio_data)
        return jsonStr, jsonStr_wo_files

    def send_nhif_claim(self):
        json_data, json_data_wo_files = self.get_folio_json_data()
        token = get_claimsservice_token(self.company, "NHIF")
        claimsserver_url = frappe.get_value(
            "Company Insurance Setting", {"company": self.company, "insurance_provider": "NHIF"}, "claimsserver_url"
        )
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        url = str(claimsserver_url) + "/claimsserver/api/v1/Claims/SubmitFolios"
        r = None
        try:
            r = requests.post(url, headers=headers, data=json_data, timeout=300)

            if r.status_code != 200:
                if str(r) and r.status_code == 500 and "A claim with Similar" in r.text:
                    frappe.msgprint(
                        "This folio was NOT sent. However, since the folio is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{0}".format(
                            r.text
                        )
                        + str(get_datetime())
                    )
                elif (
                    str(r)
                    and r.status_code == 406
                    and "Folio Number {0} has already been submited.".format(
                        self.folio_no
                    )
                    in r.text
                ):
                    frappe.msgprint(
                        "This folio was NOT sent. However, since it is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{0}".format(
                            r.text
                        )
                        + str(get_datetime())
                    )
                else:
                    frappe.msgprint(
                        "NHIF Server responded with HTTP status code: {0}".format(
                            str(r.status_code if r.status_code else "NONE")
                        )
                    )
                    frappe.throw(str(r.text) if r.text else str(r))
            else:
                frappe.msgprint(str(r.text))
                if r.text:
                    add_log(
                        request_type="SubmitFolios",
                        request_url=url,
                        request_header=headers,
                        request_body=json_data_wo_files,
                        response_data=r.text,
                        status_code=r.status_code,
                    )
                frappe.msgprint(_("The claim has been sent successfully"), alert=True)

        except Exception as e:
            add_log(
                request_type="SubmitFolios",
                request_url=url,
                request_header=headers,
                request_body=json_data,
                response_data=(r.text if str(r) else "NO RESPONSE r. Timeout???")
                or "NO TEXT",
                status_code=(r.status_code if str(r) else "NO RESPONSE r. Timeout???")
                or "NO STATUS CODE",
            )
            self.add_comment(
                comment_type="Comment",
                text=r.text if str(r) else "NO RESPONSE",
            )
            frappe.db.commit()

            frappe.throw(
                "This folio was NOT submitted due to the error above!. Please retry after resolving the problem. "
                + str(get_datetime())
            )

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

    def set_clinical_notes(self, encounter_doc):
        if not self.clinical_notes:
            patient_name = f"Patient: <b>{self.patient_name}</b>,"
            date_of_birth = f"Date of Birth: <b>{self.date_of_birth}</b>,"
            gender = f"Gender: <b>{self.gender}</b>,"
            years = f"Age: <b>{(frappe.utils.date_diff(nowdate(), self.date_of_birth))//365} years</b>,"
            self.clinical_notes = (
                " ".join([patient_name, gender, date_of_birth, years]) + "<br>"
            )

        if not encounter_doc.examination_detail:
            frappe.msgprint(
                _(
                    f"Encounter {encounter_doc.name} does not have Examination Details defined. Check the encounter."
                ),
                alert=True,
            )
            # return
        department = frappe.get_cached_value(
            "Healthcare Practitioner", encounter_doc.practitioner, "department"
        )
        self.clinical_notes += f"<br>PractitionerName: <i>{encounter_doc.practitioner_name},</i> Speciality: <i>{department},</i> DateofService: <i>{encounter_doc.encounter_date} {encounter_doc.encounter_time}</i> <br>"
        self.clinical_notes += encounter_doc.examination_detail or ""

        if len(encounter_doc.get("drug_prescription")) > 0:
            self.clinical_notes += "<br>Medication(s): <br>"
            for row in encounter_doc.get("drug_prescription"):
                med_info = ""
                if row.dosage:
                    med_info += f", Dosage: {row.dosage}"
                if row.period:
                    med_info += f", Period: {row.period}"
                if row.dosage_form:
                    med_info += f", Dosage Form: {row.dosage_form}"

                self.clinical_notes += f"Drug: {row.drug_code} {med_info}"
                self.clinical_notes += "<br>"
        self.clinical_notes = self.clinical_notes.replace('"', " ")

    def before_insert(self):
        if frappe.db.exists(
            {
                "doctype": "NHIF Patient Claim",
                "patient": self.patient,
                "patient_appointment": self.patient_appointment,
                "cardno": self.cardno,
                "docstatus": 0,
            }
        ):
            frappe.throw(
                f"NHIF Patient Claim is already exist for patient: #<b>{self.patient}</b> with appointment: #<b>{self.patient_appointment}</b>"
            )

        self.validate_appointment_info()
        self.validate_multiple_appointments_per_authorization_no("before_insert")

    def after_insert(self):
        folio_counter = frappe.db.get_all(
            "Insurance Folio Counter",
            filters={
                "company": self.company,
                "claim_year": self.claim_year,
                "claim_month": self.claim_month,
                "insurance_provider": "NHIF",
            },
            fields=["name", "folio_no"],
            page_length=1,
        )

        folio_no = 1
        if not folio_counter:
            new_folio_doc = frappe.get_doc(
                {
                    "doctype": "Insurance Folio Counter",
                    "company": self.company,
                    "claim_year": self.claim_year,
                    "claim_month": self.claim_month,
                    "posting_date": now_datetime(),
                    "insurance_provider": "NHIF",
                    "folio_no": folio_no,
                }
            ).insert(ignore_permissions=True)
            new_folio_doc.reload()
        else:
            folio_no = cint(folio_counter[0].folio_no) + 1
            frappe.set_value("Insurance Folio Counter", folio_counter[0].name, {
                "folio_no": folio_no,
                "posting_date": now_datetime()
            })
        frappe.set_value(self.doctype, self.name, "folio_no", folio_no)

        items = []
        for row in self.nhif_patient_claim_item:
            new_row = row.as_dict()
            for fieldname in [
                "name",
                "owner",
                "creation",
                "modified",
                "modified_by",
                "docstatus",
            ]:
                new_row[fieldname] = None
            items.append(new_row)

        if len(items) > 0:
            frappe.set_value(
                self.doctype, self.name, "original_nhif_patient_claim_item", items
            )

        self.reload()

    def validate_appointment_info(self):
        appointment_doc = frappe.get_doc(
            "Patient Appointment", self.patient_appointment
        )
        if self.authorization_no != appointment_doc.authorization_number:
            url = frappe.utils.get_url_to_form(
                "Patient Appointment", self.patient_appointment
            )
            frappe.throw(
                _(
                    f"Authorization Number: <b>{self.authorization_no}</b> of this Claim is not same to \
                  Authorization Number: <b>{appointment_doc.authorization_number}</b> on Patient Appointment: <a href='{url}'><b>{self.patient_appointment}</b></a><br><br>\
                  <b>Please rectify before creating this Claim</b>"
                )
            )
        if self.cardno != appointment_doc.coverage_plan_card_number:
            url = frappe.utils.get_url_to_form(
                "Patient Appointment", self.patient_appointment
            )
            frappe.throw(
                _(
                    f"Card Number: <b>{self.cardno}</b> of this Claim is not same to \
                  Card Number: <b>{appointment_doc.coverage_plan_card_number}</b> on Patient Appointment: <a href='{url}'><b>{self.patient_appointment}</b></a><br><br>\
                  <b>Please rectify before creating this Claim</b>"
                )
            )


def get_missing_patient_signature(self):
    if self.patient:
        patient_doc = frappe.get_cached_doc("Patient", self.patient)
        signature = patient_doc.patient_signature
        if not signature:
            frappe.throw(_("Patient signature is required"))
        self.patient_signature = signature


def validate_submit_date(self):
    import calendar

    submit_claim_month, submit_claim_year = frappe.get_value(
        "Company Insurance Setting",
        {"company": self.company, "insurance_provider": "NHIF"},
        ["submit_claim_month", "submit_claim_year"],
    )

    if not (submit_claim_month or submit_claim_year):
        frappe.throw(
            frappe.bold(
                "Submit Claim Month or Submit Claim Year not found,\
                please inform IT department to set it on Company Insurance Setting"
            )
        )

    if self.claim_month != submit_claim_month or self.claim_year != submit_claim_year:
        frappe.throw(
            f"Claim Month: {frappe.bold(calendar.month_name[self.claim_month])} or Claim Year: {frappe.bold(self.claim_year)} \
            of this document is not same to Submit Claim Month: {frappe.bold(calendar.month_name[submit_claim_month])} \
            or Submit Claim Year: {frappe.bold(submit_claim_year)} on Company Insurance Setting"
        )


def validate_item_status(self):
    for row in self.nhif_patient_claim_item:
        if row.status == "Draft":
            frappe.throw(
                "Item: {0}, doctype: {1}. RowNo: {2} is in <strong>Draft</strong>,\
                please contact relevant department for clarification".format(
                    frappe.bold(row.item_name),
                    frappe.bold(row.ref_doctype),
                    frappe.bold(row.idx),
                )
            )


def validate_hold_card_status(
    self, appointment_documents, claim_details, merged_appointments, caller=None
):
    msg = f"<p style='text-align: justify; font-size: 14px'>Patient: <b>{self.patient}</b>-<b>{self.patient_name}</b> has multiple appointments: <br>"
    # check if there is any merging done before
    reqd_throw_count = 0
    for appointment in appointment_documents:
        url = get_url_to_form("Patient Appointment", appointment)
        msg += f"<a href='{url}'><b>{appointment}</b></a> , "

        if merged_appointments:
            for app in frappe.utils.unique(merged_appointments):
                if appointment == app:
                    reqd_throw_count += 1

    # rock 163
    if caller:
        unique_claims_appointments = 0
        if len(frappe.utils.unique(merged_appointments)) < len(claim_details):
            unique_claims_appointments = len(claim_details)
        else:
            unique_claims_appointments = len(frappe.utils.unique(merged_appointments))

        if (len(appointment_documents) - 1) == unique_claims_appointments:
            frappe.msgprint("<strong>Release Patient Card</strong>", 20, alert=True)
            frappe.msgprint("<strong>Release Patient Card</strong>")
        else:
            msg += f"<br> with same authorization no: <b>{self.authorization_no}</b><br><br>\
                Please <strong>Hold patient card</strong> until claims for all <b>{len(appointment_documents)}</b> appointments to be created.</p>"
            frappe.msgprint("<strong>Please Hold Card</strong>", 20, alert=True)
            frappe.msgprint(str(msg))

        return

    msg += f"<br> with same authorization no: <b>{self.authorization_no}</b><br><br> Please consider <strong>merging of claims</strong>\
        if Claims for all <b>{len(appointment_documents)}</b> appointments have already been created</p>"

    if reqd_throw_count < len(appointment_documents):
        frappe.throw(msg)


def get_item_refcode(item_code):
    code_list = frappe.get_all(
        "Item Customer Detail",
        filters={"parent": item_code, "customer_name": "NHIF"},
        fields=["ref_code"],
    )
    if len(code_list) == 0:
        frappe.throw(_(f"Item {item_code} has not NHIF Code Reference"))
    ref_code = code_list[0].ref_code
    if not ref_code:
        frappe.throw(_(f"Item {item_code} has not NHIF Code Reference"))
    return ref_code


def generate_pdf(doc):
    file_list = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "NHIF Patient Claim",
            "file_name": str(doc.name + ".pdf"),
        },
    )
    if file_list:
        patientfile = frappe.get_doc("File", file_list[0].name)
        if patientfile:
            pdf = patientfile.get_content()
            return to_base64(pdf)

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

    pdf = download_multi_pdf(
        doctype, doc.name, print_format=print_format, no_letterhead=1
    )
    if pdf:
        ret = frappe.get_doc(
            {
                "doctype": "File",
                "attached_to_doctype": "NHIF Patient Claim",
                "attached_to_name": doc.name,
                "folder": "Home/Attachments",
                "file_name": doc.name + ".pdf",
                "file_url": "/private/files/" + doc.name + ".pdf",
                "content": pdf,
                "is_private": 1,
            }
        )
        ret.save(ignore_permissions=1)
        # ret.db_update()
        base64_data = to_base64(pdf)
        return base64_data


def download_multi_pdf(doctype, name, print_format=None, no_letterhead=0):
    output = PdfFileWriter()
    if isinstance(doctype, dict):
        for doctype_name in doctype:
            for doc_name in doctype[doctype_name]:
                try:
                    output = frappe.get_print(
                        doctype_name,
                        doc_name,
                        print_format,
                        as_pdf=True,
                        output=output,
                        no_letterhead=no_letterhead,
                    )
                except Exception:
                    frappe.log_error(frappe.get_traceback())

    return read_multi_pdf(output)


def read_multi_pdf(output):
    fname = os.path.join("/tmp", "frappe-pdf-{0}.pdf".format(frappe.generate_hash()))
    output.write(open(fname, "wb"))

    with open(fname, "rb") as fileobj:
        filedata = fileobj.read()

    return filedata


def get_claim_pdf_file(doc):
    file_list = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "NHIF Patient Claim",
            "file_name": str(doc.name + "-claim.pdf"),
        },
    )
    if file_list:
        for file in file_list:
            frappe.delete_doc("File", file.name, ignore_permissions=True)

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

    html = frappe.get_print(doctype, docname, print_format, doc=None, no_letterhead=1)

    filename = "{name}-claim".format(name=docname.replace(" ", "-").replace("/", "-"))
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
        ret.insert(ignore_permissions=True)
        ret.db_update()
        if not ret.name:
            frappe.throw("ret name not exist")
        base64_data = to_base64(pdf)
        return base64_data
    else:
        frappe.throw(_("Failed to generate pdf"))


def get_child_map():
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
            "ref_doctype": "Delivery Note Item",
            "ref_docname": "dn_detail",
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
    return childs_map


def get_LRPMT_status(encounter_no, row, child):
    status = None
    if child["doctype"] == "Therapy Type" or row.get(child["ref_docname"]):
        status = "Submitted"

    elif child["doctype"] == "Lab Test Template" and not row.get(child["ref_docname"]):
        lab_workflow_state = frappe.get_value(
            "Lab Test",
            {
                "ref_docname": encounter_no,
                "ref_doctype": "Patient Encounter",
                "hms_tz_ref_childname": row.name,
            },
            "workflow_state",
        )
        if lab_workflow_state and lab_workflow_state != "Lab Test Requested":
            status = "Submitted"
        else:
            status = "Draft"
    else:
        status = "Draft"

    return status


@frappe.whitelist()
def reconcile_repeated_items(claim_no):
    def reconcile_items(claim_items):
        unique_items = []
        repeated_items = []
        unique_refcodes = []

        for row in claim_items:
            if row.item_code not in unique_refcodes:
                unique_refcodes.append(row.item_code)
                unique_items.append(row)
            else:
                repeated_items.append(row)

        if len(repeated_items) > 0:
            items = []
            for item in unique_items:
                ref_docnames = []
                ref_encounters = []

                for d in repeated_items:
                    if item.item_code == d.item_code:
                        item.item_quantity += d.item_quantity
                        item.amount_claimed += d.amount_claimed

                        if d.approval_ref_no:
                            approval_ref_no = None
                            if item.approval_ref_no:
                                approval_ref_no = (
                                    str(item.approval_ref_no)
                                    + ","
                                    + str(d.approval_ref_no)
                                )
                            else:
                                approval_ref_no = d.approval_ref_no

                            item.approval_ref_no = approval_ref_no

                        if d.patient_encounter:
                            ref_encounters.append(d.patient_encounter)
                        if d.ref_docname:
                            ref_docnames.append(d.ref_docname)

                        if item.status != "Submitted" and d.status == "Submitted":
                            item.status = "Submitted"

                if item.patient_encounter:
                    ref_encounters.append(item.patient_encounter)
                if item.ref_docname:
                    ref_docnames.append(item.ref_docname)

                if len(ref_encounters) > 0:
                    item.patient_encounter = ",".join(set(ref_encounters))

                if len(ref_docnames) > 0:
                    item.ref_docname = ",".join(set(ref_docnames))

                items.append(item)

            for record in repeated_items:
                frappe.delete_doc(
                    record.doctype,
                    record.name,
                    force=True,
                    ignore_permissions=True,
                    ignore_on_trash=True,
                    delete_permanently=True,
                )
            return items

        else:
            return unique_items

    claim_doc = frappe.get_doc("NHIF Patient Claim", claim_no)
    claim_doc.allow_changes = 1
    claim_doc.nhif_patient_claim_item = reconcile_items(
        claim_doc.nhif_patient_claim_item
    )
    claim_doc.original_nhif_patient_claim_item = reconcile_items(
        claim_doc.original_nhif_patient_claim_item
    )

    claim_doc.save(ignore_permissions=True)
    claim_doc.reload()
    return True


def update_original_patient_claim(doc):
    """Update original patient claim incase merging if done for this claim"""

    ref_docnames = []
    for item in doc.original_nhif_patient_claim_item:
        if item.ref_docname:
            d = item.ref_docname.split(",")
            ref_docnames.extend(d)

    for row in doc.nhif_patient_claim_item:
        if row.ref_docname not in ref_docnames:
            new_row = row.as_dict()
            for fieldname in [
                "name",
                "owner",
                "creation",
                "modified",
                "modified_by",
                "docstatus",
            ]:
                new_row[fieldname] = None
            doc.append("original_nhif_patient_claim_item", new_row)
