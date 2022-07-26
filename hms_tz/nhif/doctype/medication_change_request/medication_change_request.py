# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from hms_tz.nhif.api.healthcare_utils import (
    get_item_rate,
    get_warehouse_from_service_unit,
    get_template_company_option,
    msgThrow
)
from hms_tz.hms_tz.doctype.patient_encounter.patient_encounter import get_quantity
from hms_tz.nhif.api.patient_encounter import validate_stock_item
from hms_tz.nhif.api.patient_appointment import get_mop_amount
from frappe.model.workflow import apply_workflow

class MedicationChangeRequest(Document):
    def validate(self):
        self.title = "{0}/{1}".format(self.patient_encounter, self.delivery_note)
        self.warehouse = self.get_warehouse_per_delivery_note()
        if self.drug_prescription:
            for drug in self.drug_prescription:
                validate_healthcare_service_unit(self.warehouse, drug, method="validate")        
                if not drug.amount:    
                    set_amount(self, drug)
                if not drug.quantity or drug.quantity == 0:
                    # Remarked by MPC_TZ 2022-06-10 16:16 to avoid automatic qty calculations
                    # qty = drug_line.get_quantity()
                    drug.quantity = 0
                drug.delivered_quantity = drug.quantity - (drug.quantity_returned or 0)

                template_doc = get_template_company_option(drug.drug_code, self.company)
                drug.is_not_available_inhouse = template_doc.is_not_available
                if drug.is_not_available_inhouse == 1:
                    frappe.msgprint(
                        "NOTE: This healthcare service item, <b>"
                        + drug.drug_code + "</b>, is not available inhouse".format(
                            frappe.bold(drug.drug_code)
                    ))
                
                validate_restricted(self, drug)
        
    def get_warehouse_per_delivery_note(self):
        return frappe.get_value("Delivery Note", self.delivery_note, "set_warehouse")

    
    def before_insert(self):
        if self.patient_encounter:
            encounter_doc = get_patient_encounter_doc(self.patient_encounter)
            if not encounter_doc.insurance_coverage_plan:
                frappe.throw(frappe.bold("Cannot create medication change request for Cash Patient,\
                    Medication change request is only used for Insurance Patients"))
            
            self.warehouse = self.get_warehouse_per_delivery_note()

            for row in encounter_doc.drug_prescription:
                if self.warehouse == get_warehouse_from_service_unit(row.healthcare_service_unit):
                    new_row = row.as_dict()
                    new_row["name"] = None
                    self.append('original_pharmacy_prescription', new_row)
                    self.append('drug_prescription', new_row)
            
            if len(self.patient_encounter_final_diagnosis) == 0:
                for row in encounter_doc.patient_encounter_final_diagnosis:
                    row.name = None
                    self.append("patient_encounter_final_diagnosis", row)
            
        
    def before_submit(self):
        self.warehouse = self.get_warehouse_per_delivery_note()
        for item in self.drug_prescription:
            validate_healthcare_service_unit(self.warehouse, item, method="throw")
            validate_stock_item(
                    item.drug_code, 
                    item.quantity, 
                    self.company, 
                    item.doctype, 
                    item.healthcare_service_unit,
                    caller="unknown",
                    method="throw"
                )
    
    def on_submit(self):
        encounter_doc = self.update_encounter()
        self.update_delivery_note(encounter_doc)

    def update_encounter(self):
        doc = frappe.get_doc("Patient Encounter", self.patient_encounter)
        for line in self.original_pharmacy_prescription:
            for row in doc.drug_prescription:
                if (
                    line.drug_code == row.drug_code and 
                    line.healthcare_service_unit == row.healthcare_service_unit
                ):
                    frappe.delete_doc(
                        row.doctype, row.name, force=1, ignore_permissions=True, for_reload=True
                    )
        doc.reload()
        fields_to_clear = [
            "name",
            "owner",
            "creation",
            "modified",
            "modified_by",
            "docstatus",
            "amended_from",
            "amendment_date",
            "parentfield",
            "parenttype",
        ]
        for row in self.drug_prescription:
            if row.is_not_available_inhouse == 1:
                continue
            new_row = frappe.copy_doc(row).as_dict()
            for fieldname in fields_to_clear:
                new_row[fieldname] = None
            new_row["drug_prescription_created"] = 1
            doc.append("drug_prescription", new_row)
        doc.db_update_all()
        frappe.msgprint(
            _("Patient Encounter " + self.patient_encounter + " has been updated!"),
            alert=True,
        )
        return doc

    def update_delivery_note(self, encounter_doc):
        doc = frappe.get_doc("Delivery Note", self.delivery_note)
        doc.items = []
        doc.hms_tz_original_items = []

        for row in encounter_doc.drug_prescription:
            warehouse = get_warehouse_from_service_unit(row.healthcare_service_unit)
            if warehouse != doc.set_warehouse:
                continue
            
            if row.prescribe or row.is_not_available_inhouse or row.is_cancelled:
                continue
            item_code, uom = frappe.get_value("Medication", row.drug_code, ["item", "stock_uom"])
            is_stock, item_name = frappe.get_value(
                "Item", item_code, ["is_stock_item", "item_name"]
            )
            if not is_stock:
                continue
            item = frappe.new_doc("Delivery Note Item")
            if not item:
                frappe.throw(
                    _("Could not create delivery note item for " + row.drug_code)
                )
            item.item_code = item_code
            item.item_name = item_name
            item.warehouse = warehouse
            item.qty = row.delivered_quantity or 1
            item.medical_code = row.medical_code
            item.rate = row.amount
            item.amount = row.amount * row.delivered_quantity
            item.reference_doctype = row.doctype
            item.reference_name = row.name
            item.is_restricted = row.is_restricted
            item.description = (
                row.drug_name
                + " for "
                + (row.dosage or "No Prescription Dosage")
                + " for "
                + (row.period or "No Prescription Period")
                + " with "
                + row.medical_code
                + " and doctor notes: "
                + (row.comment or "Take medication as per dosage.")
            )

            doc.append("items", item)

            new_original_item = set_original_items(doc.name, item)
            new_original_item.stock_uom = uom
            new_original_item.uom = uom
            doc.append("hms_tz_original_items", new_original_item)

        doc.save(ignore_permissions=True)

        try:
            if doc.workflow_state != "Changes Made":
                apply_workflow(doc, "Make Changes")

        except Exception:
            frappe.log_error(frappe.get_traceback(), str("Apply workflow error for delivery note: {0}".format(frappe.bold(doc.name))))
            frappe.throw("Apply workflow error for delivery note: {0}".format(frappe.bold(doc.name)))

        frappe.msgprint(
            _("Delivery Note " + self.delivery_note + " has been updated!"), alert=True
        )


@frappe.whitelist()
def get_delivery_note(patient, patient_encounter):
    d_list = frappe.get_all(
        "Delivery Note", filters={"reference_name": patient_encounter, "docstatus": 0},
        fields=["name", "set_warehouse"]
    )
    if len(d_list) > 1:
        frappe.throw("There is {0} delivery note of IPD and OPD warehouses, for patient: {1}, and encounter: {2}, \
            Please choose one delivery note between {3} and {4}".format(
                frappe.bold(len(d_list)),
                frappe.bold(patient),
                frappe.bold(patient_encounter),
                frappe.bold(d_list[0].name +': warehouse: '+ d_list[0].set_warehouse),
                frappe.bold(d_list[1].name +': warehouse: '+ d_list[1].set_warehouse)
        ))
    
    if len(d_list) == 1:
        return d_list[0].name
    if len(d_list) == 0:
        return ""


@frappe.whitelist()
def get_patient_encounter_name(delivery_note):
    doc = frappe.get_doc("Delivery Note", delivery_note)
    if doc.reference_doctype and doc.reference_name:
        if doc.reference_doctype == "Patient Encounter":
            return doc.reference_name
    return ""


@frappe.whitelist()
def get_patient_encounter_doc(patient_encounter):
    doc = frappe.get_doc("Patient Encounter", patient_encounter)
    return doc

def get_insurance_details(self):
    insurance_subscription, insurance_company = frappe.get_value(
        "Patient Appointment", self.appointment,
        ["insurance_subscription", "insurance_company"],
    )
    return insurance_subscription, insurance_company

def set_amount(self, item):
    item_code = frappe.get_value("Medication", item.drug_code, "item")

    if not item.prescribe:
        insurance_subscription, insurance_company = get_insurance_details(self)

        item.amount = get_item_rate(
            item_code, self.company, insurance_subscription, insurance_company
        )

    else:
        item.amount = get_mop_amount(item_code, "Cash", self.company,self.patient)



def validate_restricted(self, row):
    items = {}
    insurance_subscription, insurance_company = get_insurance_details(self)

    insurance_coverage_plan = frappe.get_value(
        "Healthcare Insurance Subscription",
        {"name" :insurance_subscription},
        "healthcare_insurance_coverage_plan"
    )
    if not insurance_coverage_plan:
        frappe.throw(_("Healthcare Insurance Coverage Plan is Not defiend"))
    
    today = frappe.utils.nowdate()
    service_coverage = frappe.get_all("Healthcare Service Insurance Coverage",
        filters={"is_active": 1, "start_date": ["<=", today],"end_date": [">=", today],
            "healthcare_service_template": row.drug_code, 
            "healthcare_insurance_coverage_plan": insurance_coverage_plan,
        }, fields=["name", "approval_mandatory_for_claim"],
    )
    if service_coverage:
        row.is_restricted = service_coverage[0].approval_mandatory_for_claim
    else:
        row.is_restricted = 0

@frappe.whitelist()
def validate_healthcare_service_unit(warehouse, item, method):
    if warehouse != get_warehouse_from_service_unit(item.healthcare_service_unit):
        msgThrow(
            _("Please change healthcare service unit: {0}, for drug: {1} row: {2}\
                as it is of different warehouse".format(
                    frappe.bold(item.healthcare_service_unit),
                    frappe.bold(item.drug_code),
                    frappe.bold(item.idx)
                )   
            ), 
            method
        )

@frappe.whitelist()
def get_items_on_change_of_delivery_note(name, encounter, delivery_note):
    doc = frappe.get_doc("Medication Change Request", name)
    
    if not doc or not encounter or not delivery_note:
        return 

    patient_encounter_doc = frappe.get_doc("Patient Encounter", encounter)
    delivery_note_doc = frappe.get_doc("Delivery Note", delivery_note)

    doc.original_pharmacy_prescription = []
    doc.drug_prescription = []
    for item_line in patient_encounter_doc.drug_prescription:
        if delivery_note_doc.set_warehouse != get_warehouse_from_service_unit(item_line.healthcare_service_unit):
            continue
        row = item_line.as_dict()
        row["name"] = None
        row["parent"] = None 
        row["parentfield"] =  None 
        row["parenttype"] = None
        doc.append('original_pharmacy_prescription', row)
        doc.append("drug_prescription", row)
    doc.delivery_note = delivery_note
    doc.save(ignore_permissions=True)
    doc.reload()
    return doc


def get_fields_to_clear():
    return ["name", "owner", "creation", "modified", "modified_by", "docstatus"]


def set_original_items(name, item):
    new_row = item.as_dict()
    for fieldname in get_fields_to_clear():
        new_row[fieldname] = None
        
    new_row.update({
        "parent": name,
        "parentfield": "hms_tz_original_items",
        "parenttype": "Delivery Note",
        "doctype": "Original Delivery Note Item"
    })
    
    return new_row


@frappe.whitelist()
def create_md_change_request_from_dn(doctype, name):
    source_doc = frappe.get_doc(doctype, name)
    if source_doc.reference_doctype != "Patient Encounter":
        frappe.throw("Delivery note should have reference doctype of {0}".format(frappe.bold("Patient Encounter")))

    doc = frappe.new_doc("Medication Change Request")
    doc.patient = source_doc.patient
    doc.patient_name = source_doc.patient_name
    doc.appointment = source_doc.hms_tz_appointment_no
    doc.company = source_doc.company
    doc.patient_encounter = source_doc.reference_name
    doc.delivery_note = source_doc.name
    doc.healthcare_practitioner = source_doc.healthcare_practitioner

    try:
        doc.save(ignore_permissions=True)
        doc.reload()
        
        if doc.get("name"):
            try:
                if source_doc.workflow_state != "Changes Requested":
                    apply_workflow(source_doc, "Request Changes")

            except Exception:
                frappe.log_error(frappe.get_traceback(), str("Apply workflow error for delivery note: {0}".format(frappe.bold(source_doc.name))))
                frappe.throw("Apply workflow error for delivery note: {0}".format(frappe.bold(source_doc.name)))

    except Exception:
        frappe.log_error(frappe.get_traceback(), str(doc.doctype))
        frappe.throw("Medication Change Request was not created")

    return doc.name