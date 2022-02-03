# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, getdate, nowtime, add_to_date
from hms_tz.nhif.api.healthcare_utils import (
    get_item_rate,
    get_warehouse_from_service_unit,
    get_item_price,
    create_individual_lab_test,
    create_individual_radiology_examination,
    create_individual_procedure_prescription,
    msgThrow,
    msgPrint,
    get_template_company_option,
)
from erpnext.healthcare.doctype.healthcare_settings.healthcare_settings import (
    get_receivable_account,
    get_income_account,
)
import time
from hms_tz.nhif.api.patient_appointment import get_mop_amount
from erpnext.accounts.utils import get_balance_on


def on_trash(doc, method):
    pmr_list = frappe.get_all(
        "Patient Medical Record",
        fields={"name"},
        filters={
            "reference_doctype": "Patient Encounter",
            "reference_name": doc.name,
        },
    )
    for pmr_doc in pmr_list:
        frappe.delete_doc(
            "Patient Medical Record", pmr_doc.name, ignore_permissions=True
        )


def on_submit_validation(doc, method):
    if doc.encounter_type == "Initial":
        doc.reference_encounter = doc.name
    show_last_prescribed(doc, method)
    show_last_prescribed_for_lrpt(doc)
    submitting_healthcare_practitioner = frappe.db.get_value(
        "Healthcare Practitioner", {"user_id": frappe.session.user}, ["name"]
    )
    if submitting_healthcare_practitioner:
        doc.practitioner = submitting_healthcare_practitioner
    checkـforـduplicate(doc, method)
    mtuha_missing = ""
    for final_diagnosis in doc.patient_encounter_final_diagnosis:
        if not final_diagnosis.mtuha:
            mtuha_missing += "-  <b>" + final_diagnosis.medical_code + "</b><br>"

    if mtuha_missing:
        msgThrow(
            _("{0}<br>MTUHA Code not defined for the above diagnosis").format(
                mtuha_missing
            ),
            method,
        )

    insurance_subscription = doc.insurance_subscription
    child_tables = {
        "lab_test_prescription": "lab_test_code",
        "radiology_procedure_prescription": "radiology_examination_template",
        "procedure_prescription": "procedure",
        "drug_prescription": "drug_code",
        "therapies": "therapy_type",
        # "diet_recommendation": "diet_plan" dosent have Healthcare Service Insurance Coverage
    }

    childs_map = [
        {
            "table": "lab_test_prescription",
            "doctype": "Lab Test Template",
            "item": "lab_test_code",
        },
        {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Examination Template",
            "item": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "doctype": "Clinical Procedure Template",
            "item": "procedure",
        },
        {
            "table": "drug_prescription",
            "doctype": "Medication",
            "item": "drug_code",
        },
        {
            "table": "therapies",
            "doctype": "Therapy Type",
            "item": "therapy_type",
        },
    ]
    for child in childs_map:
        for row in doc.get(child.get("table")):
            healthcare_doc = frappe.get_doc(
                child.get("doctype"), row.get(child.get("item"))
            )
            if healthcare_doc.disabled:
                msgThrow(
                    _(
                        "{0} {1} selected at {2} is disabled. Please select an enabled item."
                    ).format(child.get("doctype"), row.get(child.get("item")), row.idx),
                    method,
                )

    prescribed_list = ""
    for key, value in child_tables.items():
        table = doc.get(key)
        for row in table:
            quantity = row.get("quantity") or row.get("no_of_sessions")
            if (
                (not doc.insurance_subscription)
                or row.prescribe
                or row.is_not_available_inhouse
            ):
                row.prescribe = 1
                prescribed_list += "-  <b>" + row.get(value) + "</b><BR>"
                if row.is_not_available_inhouse:
                    prescribed_list += " - THIS ITEM IS NOT AVAILABLE INHOUSE "
                prescribed_list += "<BR>"
            elif not row.prescribe:
                if row.get("no_of_sessions") and doc.insurance_subscription:
                    if row.no_of_sessions != 1:
                        row.no_of_sessions = 1
                        frappe.msgprint(
                            _(
                                "No of sessions have been set to 1 for {0} as per"
                                " insurance rules."
                            ).format(row.get(value)),
                            alert=True,
                        )
            if not row.is_not_available_inhouse:
                validate_stock_item(
                    row.get(value),
                    quantity,
                    doc.company,
                    healthcare_service_unit=row.get("healthcare_service_unit"),
                    method=method,
                )
    if prescribed_list:
        msgPrint(
            _(
                "{0}<BR>The above been prescribed. <b>Request the patient to visit the"
                " cashier for billing/cash payment</b> or prescription printout."
            ).format(prescribed_list),
            method,
        )

    if not insurance_subscription:
        return

    if not doc.healthcare_service_unit:
        # doc.healthcare_service_unit = "NW2F Room 05 OPD - SHMH-DSM"
        frappe.throw(_("Healthcare Service Unit not set"))
    healthcare_insurance_coverage_plan = frappe.get_value(
        "Healthcare Insurance Subscription",
        insurance_subscription,
        "healthcare_insurance_coverage_plan",
    )
    if not healthcare_insurance_coverage_plan:
        frappe.throw(_("Healthcare Insurance Coverage Plan is Not defiend"))
    today = nowdate()
    healthcare_service_templates = {}
    for key, value in child_tables.items():
        for row in doc.get(key):
            if row.override_subscription or row.prescribe:
                continue

            # healthcare_service_templates is like {"CBC": [cbc1_lab_prescription_line_object, cbc2_lab_prescription_line_object], "XRay Abdomen": [radiology_prescription_line_object], ["Panadol": drug_prescription_line_object]}
            rows_affected = healthcare_service_templates.setdefault(row.get(value), [])
            rows_affected.append(row)
    # hsic => Healthcare Service Insurance Coverage
    hsic_list = frappe.get_all(
        "Healthcare Service Insurance Coverage",
        fields={
            "healthcare_service_template",
            "maximum_number_of_claims",
            "approval_mandatory_for_claim",
        },
        filters={
            "is_active": 1,
            "healthcare_insurance_coverage_plan": healthcare_insurance_coverage_plan,
            "start_date": ("<=", today),
            "end_date": (">=", today),
            "healthcare_service_template": ("in", healthcare_service_templates),
        },
        order_by="modified desc",
    )
    # hsic_map is like {"CBC": HSIC_object_for_CBC, "XRay Abdomen": HSIC_object_for_xray_abdomen, "Panadol": HSIC_object_for_panadol}
    hsic_map = {hsic.healthcare_service_template: hsic for hsic in hsic_list}
    hicp_name, is_exclusions = frappe.get_value(
        "Healthcare Insurance Coverage Plan",
        healthcare_insurance_coverage_plan,
        ["coverage_plan_name", "is_exclusions"],
    )
    for template in healthcare_service_templates:
        if not is_exclusions:
            if template not in hsic_map:
                msg = _(
                    "{0} not covered in Healthcare Insurance Coverage Plan "
                    + str(hicp_name)
                ).format(template)
                msgThrow(
                    msg,
                    method,
                )
                continue
        else:
            if template in hsic_map:
                msg = _(
                    "{0} not covered in Healthcare Insurance Coverage Plan "
                    + str(hicp_name)
                ).format(template)
                msgThrow(
                    msg,
                    method,
                )
                continue
        coverage_info = hsic_map[template]
        for row in healthcare_service_templates[template]:
            row.is_restricted = coverage_info.approval_mandatory_for_claim
            if row.is_restricted:
                frappe.msgprint(
                    _("{0} with template {1} requires additional authorization").format(
                        _(row.doctype), template
                    ),
                    alert=True,
                )
        if coverage_info.maximum_number_of_claims == 0:
            continue
        # if maximum_number_of_claims is more than 12 it means more times per month. Times will be less than 1
        times = 12 / coverage_info.maximum_number_of_claims
        count = 1
        days = int(times * 30)
        if times < 0.1:
            count = 1 / times
            days = 30
        if not coverage_info.number_of_claims:
            lrpt_names_sql = """
                SELECT hsi.name FROM `tabLab Prescription` hsi
                INNER JOIN `tabPatient Encounter` pe ON hsi.parent = pe.name
                WHERE pe.insurance_subscription = "{0}"
                  AND hsi.lab_test_code = "{1}"
                  AND hsi.prescribe = 0
                  AND DATE(pe.creation) BETWEEN "{2}" AND "{3}"
                UNION ALL
                SELECT hsi.name FROM `tabRadiology Procedure Prescription` hsi
                INNER JOIN `tabPatient Encounter` pe ON hsi.parent = pe.name
                WHERE pe.insurance_subscription = "{0}"
                  AND hsi.radiology_examination_template = "{1}"
                  AND hsi.prescribe = 0
                  AND DATE(pe.creation) BETWEEN "{2}" AND "{3}"
                UNION ALL
                SELECT hsi.name FROM `tabProcedure Prescription` hsi
                INNER JOIN `tabPatient Encounter` pe ON hsi.parent = pe.name
                WHERE pe.insurance_subscription = "{0}"
                  AND hsi.procedure = "{1}"
                  AND hsi.prescribe = 0
                  AND DATE(pe.creation) BETWEEN "{2}" AND "{3}"
                UNION ALL
                SELECT hsi.name FROM `tabTherapy Plan Detail` hsi
                INNER JOIN `tabPatient Encounter` pe ON hsi.parent = pe.name
                WHERE pe.insurance_subscription = "{0}"
                  AND hsi.therapy_type = "{1}"
                  AND hsi.prescribe = 0
                  AND DATE(pe.creation) BETWEEN "{2}" AND "{3}"
            """.format(
                insurance_subscription, template, add_to_date(today, days=-days), today
            )
            lrpt_names = frappe.db.sql(lrpt_names_sql)
            lrpt_count = len(lrpt_names) or 0
            drug_count_sql = """
                SELECT SUM(quantity) FROM `tabDrug Prescription` hsi
                INNER JOIN `tabPatient Encounter` pe ON hsi.parent = pe.name
                WHERE pe.insurance_subscription = "{0}"
                  AND hsi.drug_code = "{1}"
                  AND hsi.prescribe = 0
                  AND DATE(pe.creation) BETWEEN "{2}" AND "{3}"
            """.format(
                insurance_subscription, template, add_to_date(today, days=-days), today
            )
            drug_count = (
                frappe.db.sql(drug_count_sql, as_dict=0,)[
                    0
                ][0]
                or 0
            )
            coverage_info.number_of_claims = lrpt_count + drug_count
        if coverage_info.number_of_claims > int(count):
            msgThrow(
                _(
                    "Maximum Number of Claims for {0} per year is exceeded within the"
                    " last {1} days. The allowed count is {2} where as past prescription count is {3}"
                ).format(template, days, int(count), coverage_info.number_of_claims),
                method,
            )
    validate_totals(doc)


def checkـforـduplicate(doc, method):
    items = []
    for item in doc.drug_prescription:
        if item.drug_code not in items:
            items.append(item.drug_code)
        else:
            msgThrow(
                _("Drug '{0}' is duplicated in line '{1}' in Drug Prescription").format(
                    item.drug_code, item.idx
                ),
                method,
            )


@frappe.whitelist()
def duplicate_encounter(encounter):
    doc = frappe.get_doc("Patient Encounter", encounter)
    if not doc.docstatus == 1 or doc.encounter_type == "Final" or doc.duplicated == 1:
        frappe.msgprint(
            _(
                "This encounter cannot be duplicated. Check if it is already duplicated"
                " using Menu/Links."
            ),
            alert=True,
        )
        return
    encounter_doc = frappe.copy_doc(doc)
    encounter_dict = encounter_doc.as_dict()
    child_tables = {
        "drug_prescription": "previous_drug_prescription",
        "lab_test_prescription": "previous_lab_prescription",
        "procedure_prescription": "previous_procedure_prescription",
        "radiology_procedure_prescription": "previous_radiology_procedure_prescription",
        "therapies": "previous_therapy_plan_detail",
        "diet_recommendation": "previous_diet_recommendation",
    }

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
        "sales_invoice",
        "is_not_billable",
    ]

    for key, value in child_tables.items():
        cur_table = encounter_dict.get(key)
        if not cur_table:
            continue
        for row in cur_table:
            new_row = row
            for fieldname in fields_to_clear:
                new_row[fieldname] = None
            encounter_dict[value].append(new_row)
        encounter_dict[key] = []
    encounter_dict["duplicated"] = 0
    encounter_dict["encounter_type"] = "Ongoing"
    if not encounter_dict.get("reference_encounter"):
        encounter_dict["reference_encounter"] = doc.name
    encounter_dict["from_encounter"] = doc.name
    encounter_dict["previous_total"] = doc.previous_total + doc.current_total
    encounter_dict["current_total"] = 0
    encounter_dict["encounter_date"] = nowdate()
    encounter_dict["encounter_time"] = nowtime()
    encounter_doc = frappe.get_doc(encounter_dict)
    encounter_doc.save(ignore_permissions=True)
    frappe.msgprint(_("Patient Encounter {0} created".format(encounter_doc.name)))
    frappe.db.update(doc.doctype, doc.name, {"duplicated": 1})
    return encounter_doc.name


def get_item_info(item_code=None, medication_name=None):
    data = {}
    if not item_code and medication_name:
        item_code = frappe.get_value("Medication", medication_name, "item")
    if item_code:
        is_stock, disabled = frappe.get_value(
            "Item", item_code, ["is_stock_item", "disabled"]
        )
        data = {"item_code": item_code, "is_stock": is_stock, "disabled": disabled}
    return data


def get_stock_availability(item_code, warehouse):
    latest_sle = frappe.db.sql(
        """SELECT qty_after_transaction AS actual_qty
        FROM `tabStock Ledger Entry`
        WHERE item_code = %s AND warehouse = %s
          AND is_cancelled = 0
        ORDER BY creation DESC
        LIMIT 1""",
        (item_code, warehouse),
        as_dict=1,
    )

    sle_qty = latest_sle[0].actual_qty or 0 if latest_sle else 0
    return sle_qty


@frappe.whitelist()
def validate_stock_item(
    healthcare_service,
    qty,
    company,
    warehouse=None,
    healthcare_service_unit=None,
    caller="Unknown",
    method="throw",
):
    # frappe.msgprint(_("{0} warehouse passed. <br> {1} healthcare service unit passed").format(warehouse, healthcare_service_unit), alert=True)
    # frappe.msgprint(_("{0} healthcare_service. <br>").format(healthcare_service), alert=True)

    company_option = get_template_company_option(healthcare_service, company)
    if not company_option.get("service_unit"):
        msgThrow(
            _(
                "The 'Company Option' in {0} - {2} for company {1} is not setup. Open {2} and correctly define it in Company Options child table".format(
                    caller, company, healthcare_service
                )
            ),
            method=method,
        )
    if caller != "Drug Prescription" and not healthcare_service_unit:
        # LRPT code stock check goes here
        return
    if company_option.get("is_not_available"):
        return

    qty = float(qty)
    if qty == 0:
        qty = 1

    item_info = get_item_info(medication_name=healthcare_service)
    stock_qty = 0
    if healthcare_service_unit:
        warehouse = get_warehouse_from_service_unit(healthcare_service_unit)
        # frappe.msgprint(_("{0} selected using {1}").format(warehouse, healthcare_service_unit), alert=True)
    if not warehouse:
        msgThrow(
            _(
                "Warehouse is missing in healthcare service unit {0} when checking"
                " for {1}"
            ).format(healthcare_service_unit, item_info.get("item_code")),
            method,
        )
    if item_info.get("is_stock") and item_info.get("item_code"):
        stock_qty = get_stock_availability(item_info.get("item_code"), warehouse) or 0
        if float(qty) > float(stock_qty):
            # To be removed after few months of stability. 2021-03-18 17:01:46
            # This is to avoid socketio diconnection when bench is restarted but user session is on.
            msgThrow(
                _(
                    "Available quantity for item: <h4 style='background-color:"
                    " LightCoral'>{0} is {3}</h4>In {1}/{2}."
                ).format(
                    item_info.get("item_code"),
                    warehouse,
                    healthcare_service_unit,
                    stock_qty,
                ),
                method,
            )
            return False
    # if stock_qty > 0:
    #     frappe.msgprint(_("Available quantity for the item {0} in {1}/{2} is {3} pcs.").format(
    #         healthcare_service, warehouse, healthcare_service_unit, stock_qty), alert=True)
    return True


def on_submit(doc, method):
    if (
        not doc.insurance_subscription and doc.inpatient_record
    ):  # Cash inpatient billing
        inpatient_billing(doc, method)
    else:  # insurance patient
        on_submit_validation(doc, method)
        create_healthcare_docs(doc, method)
        create_delivery_note(doc, method)
    if doc.inpatient_record:
        update_inpatient_record_consultancy(doc)
        validate_patient_balance_vs_patient_costs(doc)


@frappe.whitelist()
def create_healthcare_docs_from_name(patient_encounter_doc_name):
    patient_encounter_doc = frappe.get_doc(
        "Patient Encounter", patient_encounter_doc_name
    )
    create_healthcare_docs(patient_encounter_doc, "from_button")
    create_delivery_note(patient_encounter_doc, "from_button")


def create_healthcare_docs(patient_encounter_doc, method="event"):
    encounter_list = frappe.get_list(
        "Patient Encounter",
        filters={"reference_encounter": patient_encounter_doc.reference_encounter},
    )
    for encounter in encounter_list:
        # frappe.msgprint(
        #     _("Patient Encounter {0} being processed.").format(encounter.name)
        # )
        create_healthcare_docs_per_encounter(
            frappe.get_doc("Patient Encounter", encounter)
        )
    if method == "from_button":
        frappe.msgprint(
            _(
                "The {0} patient encounters were processed for creating pending healthcare docs."
            ).format(str(len(encounter_list)))
        )


def create_healthcare_docs_per_encounter(patient_encounter_doc):
    if patient_encounter_doc.docstatus != 1:
        frappe.msgprint(
            _(
                "Cannot process Patient Encounter that is not submitted! Please submit"
                " and try again."
            ),
            alert=True,
        )
        return
    if not patient_encounter_doc.appointment:
        frappe.msgprint(
            _(
                "Patient Encounter does not have patient appointment number! Request"
                " for support with this message."
            ),
            alert=True,
        )
        return
    if (
        not patient_encounter_doc.insurance_subscription
        and not patient_encounter_doc.inpatient_record
    ):
        return

    child_tables_list = [
        "lab_test_prescription",
        "radiology_procedure_prescription",
        "procedure_prescription",
    ]
    for child_table_field in child_tables_list:
        if patient_encounter_doc.get(child_table_field):
            child_table = patient_encounter_doc.get(child_table_field)
            for child in child_table:
                if patient_encounter_doc.insurance_subscription and child.prescribe:
                    continue
                if child.doctype == "Lab Prescription":
                    create_individual_lab_test(patient_encounter_doc, child)
                elif child.doctype == "Radiology Procedure Prescription":
                    create_individual_radiology_examination(
                        patient_encounter_doc, child
                    )
                elif child.doctype == "Procedure Prescription":
                    create_individual_procedure_prescription(
                        patient_encounter_doc, child
                    )


def create_delivery_note(patient_encounter_doc, method):
    encounter_list = frappe.get_list(
        "Patient Encounter",
        filters={"reference_encounter": patient_encounter_doc.reference_encounter},
    )
    for encounter in encounter_list:
        create_delivery_note_per_encounter(
            frappe.get_doc("Patient Encounter", encounter), method
        )
    if method == "from_button":
        frappe.msgprint(
            _(
                "The {0} patient encounters were processed for creating pending delivery notes."
            ).format(str(len(encounter_list)))
        )


def create_delivery_note_per_encounter(patient_encounter_doc, method):
    if not patient_encounter_doc.appointment:
        return
    if (
        not patient_encounter_doc.insurance_subscription
        and not patient_encounter_doc.inpatient_record
    ):
        return
    # Create list of warehouses to process delivery notes by warehouses
    warehouses = []
    for line in patient_encounter_doc.drug_prescription:
        if line.invoiced and line.prescribe:
            frappe.msgprint(_("Invoiced and Prescribed patient who is an inpatient"))
        elif patient_encounter_doc.insurance_subscription and line.prescribe:
            continue
        if line.drug_prescription_created:
            continue
        item_code = frappe.get_value("Medication", line.drug_code, "item")
        is_stock = frappe.get_value("Item", item_code, "is_stock_item")
        if not is_stock:
            continue
        warehouse = get_warehouse_from_service_unit(line.healthcare_service_unit)
        if warehouse and warehouse not in warehouses:
            warehouses.append(warehouse)
    # Process list of warehouses
    for element in warehouses:
        items = []
        for row in patient_encounter_doc.drug_prescription:
            if row.drug_prescription_created or row.is_not_available_inhouse:
                continue
            encounter_customer = ""
            if row.invoiced and row.prescribe:
                encounter_customer = frappe.get_value(
                    "Patient", patient_encounter_doc.patient, "customer"
                )
                insurance_coverage_plan = ""
            elif patient_encounter_doc.insurance_subscription and row.prescribe:
                continue
            warehouse = get_warehouse_from_service_unit(row.healthcare_service_unit)
            if element != warehouse:
                continue
            item_code = frappe.get_value("Medication", row.drug_code, "item")
            is_stock, item_name = frappe.get_value(
                "Item", item_code, ["is_stock_item", "item_name"]
            )
            if not is_stock:
                continue
            item = frappe.new_doc("Delivery Note Item")
            item.item_code = item_code
            item.item_name = item_name
            item.warehouse = warehouse
            item.is_restricted = row.is_restricted
            item.qty = row.quantity or 1
            item.medical_code = row.medical_code
            if row.prescribe:
                item.rate = get_mop_amount(
                    item_code,
                    patient_encounter_doc.mode_of_payment,
                    patient_encounter_doc.company,
                    patient_encounter_doc.patient,
                )
            else:
                item.rate = get_item_rate(
                    item_code,
                    patient_encounter_doc.company,
                    patient_encounter_doc.insurance_subscription,
                    patient_encounter_doc.insurance_company,
                )
            item.reference_doctype = row.doctype
            item.reference_name = row.name
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
            items.append(item)
            row.drug_prescription_created = 1
            row.db_update()
        if len(items) == 0:
            continue
        authorization_number = ""
        if (
            not patient_encounter_doc.insurance_subscription
            and patient_encounter_doc.inpatient_record
        ):
            encounter_customer = frappe.get_value(
                "Patient", patient_encounter_doc.patient, "customer"
            )
            insurance_coverage_plan = ""
        elif not encounter_customer:
            encounter_customer = frappe.get_value(
                "Healthcare Insurance Company",
                patient_encounter_doc.insurance_company,
                "customer",
            )
            insurance_coverage_plan = patient_encounter_doc.insurance_coverage_plan
            authorization_number = frappe.get_value(
                "Patient Appointment",
                patient_encounter_doc.appointment,
                fieldname="authorization_number",
            )

        doc = frappe.get_doc(
            dict(
                doctype="Delivery Note",
                posting_date=nowdate(),
                posting_time=nowtime(),
                set_warehouse=warehouse,
                company=patient_encounter_doc.company,
                customer=encounter_customer,
                currency=frappe.get_value(
                    "Company", patient_encounter_doc.company, "default_currency"
                ),
                items=items,
                coverage_plan_name=insurance_coverage_plan,
                reference_doctype=patient_encounter_doc.doctype,
                reference_name=patient_encounter_doc.name,
                authorization_number=authorization_number,
                patient=patient_encounter_doc.patient,
                patient_name=patient_encounter_doc.patient_name,
                healthcare_service_unit=patient_encounter_doc.healthcare_service_unit,
                healthcare_practitioner=patient_encounter_doc.practitioner,
            )
        )
        doc.flags.ignore_permissions = True
        doc.set_missing_values()
        doc.insert(ignore_permissions=True)
        if doc.get("name"):
            update_drug_prescription(patient_encounter_doc, doc.name)
            frappe.msgprint(
                _("Pharmacy Dispensing/Delivery Note {0} created successfully.").format(
                    frappe.bold(doc.name)
                )
            )


@frappe.whitelist()
def get_chronic_diagnosis(patient):
    data = frappe.get_all(
        "Codification Table",
        filters={
            "parent": patient,
            "parenttype": "Patient",
            "parentfield": "codification_table",
        },
        fields=["medical_code", "code", "description"],
    )
    return data


@frappe.whitelist()
def get_chronic_medications(patient):
    data = frappe.get_all(
        "Chronic Medications",
        filters={
            "parent": patient,
            "parenttype": "Patient",
            "parentfield": "chronic_medications",
        },
        fields=["*"],
    )
    return data


def validate_totals(doc):
    if (
        not doc.insurance_company
        or not doc.insurance_subscription
        or "NHIF" in doc.insurance_company
        or not doc.daily_limit
        or doc.daily_limit == 0
    ):
        return
    if doc.encounter_type == "Initial":
        appointment_amount = frappe.get_value(
            "Patient Appointment", doc.appointment, "paid_amount"
        )
        doc.previous_total = appointment_amount

    childs_map = [
        {
            "table": "lab_test_prescription",
            "doctype": "Lab Test Template",
            "item": "lab_test_code",
        },
        {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Examination Template",
            "item": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "doctype": "Clinical Procedure Template",
            "item": "procedure",
        },
        {
            "table": "drug_prescription",
            "doctype": "Medication",
            "item": "drug_code",
        },
        {
            "table": "therapies",
            "doctype": "Therapy Type",
            "item": "therapy_type",
        },
    ]
    doc.current_total = 0
    for child in childs_map:
        for row in doc.get(child.get("table")):
            if row.prescribe:
                continue
            item_code = frappe.get_value(
                child.get("doctype"), row.get(child.get("item")), "item"
            )
            # Disabled items allowed to be used in Patient Encounter
            item_info = get_item_info(item_code=item_code)
            if item_info.get("disabled"):
                frappe.throw(_("The item {0} is disabled").format(item_code))
            item_rate = get_item_rate(
                item_code,
                doc.company,
                doc.insurance_subscription,
                doc.insurance_company,
            )
            if hasattr(row, "quantity"):
                quantity = row.quantity
            else:
                quantity = 1
            doc.current_total += item_rate * quantity
    diff = doc.daily_limit - doc.current_total - doc.previous_total
    if diff < 0:
        frappe.throw(
            _(
                "The total daily limit of {0} for the Insurance Subscription {1} has"
                " been exceeded by {2}. <br> Please contact the reception to increase"
                " the limit or prescribe the items"
            ).format(doc.daily_limit, doc.insurance_subscription, diff)
        )


@frappe.whitelist()
def finalized_encounter(cur_encounter, ref_encounter=None):
    cur_encounter_doc = frappe.get_doc("Patient Encounter", cur_encounter)
    inpatient_status = frappe.get_value(
        "Patient", cur_encounter_doc.patient, "inpatient_status"
    )
    if inpatient_status:
        frappe.throw(
            _(
                "The patient {0} has inpatient status <strong>{1}</strong>. Please process the discharge before proceeding to finalize the encounter.".format(
                    cur_encounter_doc.patient, inpatient_status
                )
            )
        )

    encounters_list = frappe.get_all(
        "Patient Encounter",
        filters={"docstatus": 1, "reference_encounter": ref_encounter},
    )
    for element in encounters_list:
        frappe.set_value("Patient Encounter", element.name, "finalized", 1)

    frappe.set_value("Patient Encounter", cur_encounter, "encounter_type", "Final")
    if not ref_encounter:
        frappe.set_value("Patient Encounter", cur_encounter, "finalized", 1)
        return


@frappe.whitelist()
def create_sales_invoice(encounter, encounter_category, encounter_mode_of_payment):
    encounter_doc = frappe.get_doc("Patient Encounter", encounter)
    encounter_category = frappe.get_doc("Encounter Category", encounter_category)
    if not encounter_category.create_sales_invoice:
        return

    doc = frappe.new_doc("Sales Invoice")
    doc.patient = encounter_doc.patient
    doc.customer = frappe.get_value("Patient", encounter_doc.patient, "customer")
    doc.due_date = getdate()
    doc.company = encounter_doc.company
    doc.debit_to = get_receivable_account(encounter_doc.company)
    doc.healthcare_service_unit = encounter_doc.healthcare_service_unit
    doc.healthcare_practitioner = encounter_doc.practitioner

    item = doc.append("items", {})
    item.item_code = encounter_category.encounter_fee_item
    item.description = _("Consulting Charges: {0}").format(encounter_doc.practitioner)
    item.income_account = get_income_account(
        encounter_doc.practitioner, encounter_doc.company
    )
    item.cost_center = frappe.get_cached_value(
        "Company", encounter_doc.company, "cost_center"
    )
    item.qty = 1
    item.rate = encounter_category.encounter_fee
    item.reference_dt = "Patient Encounter"
    item.reference_dn = encounter_doc.name
    item.amount = encounter_category.encounter_fee

    doc.is_pos = 1
    payment = doc.append("payments", {})
    payment.mode_of_payment = encounter_mode_of_payment
    payment.amount = encounter_category.encounter_fee

    doc.set_taxes()
    doc.flags.ignore_permissions = True
    doc.set_missing_values(for_validate=True)
    doc.flags.ignore_mandatory = True
    doc.save(ignore_permissions=True)
    doc.calculate_taxes_and_totals()
    doc.submit()
    frappe.msgprint(_("Sales Invoice {0} created".format(doc.name)))
    encounter_doc.sales_invoice = doc.name
    encounter_doc.db_update()

    return "true"


def update_inpatient_record_consultancy(doc):
    if doc.inpatient_record:
        item_code = frappe.get_value(
            "Healthcare Practitioner", doc.practitioner, "inpatient_visit_charge_item"
        )
        rate = 0
        if doc.insurance_subscription:
            rate = get_item_rate(
                item_code,
                doc.company,
                doc.insurance_subscription,
                doc.insurance_company,
            )
        elif doc.mode_of_payment:
            price_list = frappe.get_value(
                "Mode of Payment", doc.mode_of_payment, "price_list"
            )
            rate = get_item_price(item_code, price_list, doc.company)

        record_doc = frappe.get_doc("Inpatient Record", doc.inpatient_record)
        row = record_doc.append("inpatient_consultancy", {})
        row.date = nowdate()
        row.consultation_item = item_code
        row.rate = rate
        row.encounter = doc.name
        record_doc.save(ignore_permissions=True)
        frappe.msgprint(
            _("Inpatient Consultancy record added for item {0}").format(item_code),
            alert=True,
        )


def on_update_after_submit(doc, method):
    if doc.is_not_billable:
        return
    child_tables_list = [
        "lab_test_prescription",
        "radiology_procedure_prescription",
        "procedure_prescription",
        "drug_prescription",
    ]
    services_created_pending = 0
    for child_table_field in child_tables_list:
        if services_created_pending:
            break
        if doc.get(child_table_field):
            child_table = doc.get(child_table_field)
            for child in child_table:
                if child.doctype == "Lab Prescription":
                    if child.lab_test_created == 0:
                        services_created_pending = 1
                        break
                elif child.doctype == "Radiology Procedure Prescription":
                    if child.radiology_examination_created == 0:
                        services_created_pending = 1
                        break
                elif child.doctype == "Procedure Prescription":
                    if child.procedure_created == 0:
                        services_created_pending = 1
                        break
                elif child.doctype == "Drug Prescription":
                    if child.drug_prescription_created == 0:
                        services_created_pending = 1
                        break
    if services_created_pending == 0:
        doc.is_not_billable = 1
        # frappe.msgprint("done doc.is_not_billable = 1")
    else:
        doc.is_not_billable = 0
        # frappe.msgprint("done doc.is_not_billable = 0")
    if method == "enqueue":
        # frappe.msgprint("done method enqueue db commit")
        doc.db_update()


def enqueue_on_update_after_submit(doc_name):
    time.sleep(5)
    on_update_after_submit(frappe.get_doc("Patient Encounter", doc_name), "enqueue")


def before_submit(doc, method):
    set_amounts(doc)
    encounter_create_sales_invoice = frappe.get_value(
        "Encounter Category", doc.encounter_category, "create_sales_invoice"
    )
    if encounter_create_sales_invoice:
        if not doc.sales_invoice:
            frappe.throw(
                _(
                    "The encounter cannot be submitted as the Sales Invoice is not"
                    " created yet!<br><br>Click on Create Sales Invoice and Send to VFD"
                    " before submitting.",
                    "Cannot Submit Encounter",
                )
            )
        vfd_status = frappe.get_value("Sales Invoice", doc.sales_invoice, "vfd_status")
        if vfd_status == "Not Sent":
            frappe.throw(
                _(
                    "The encounter cannot be submitted as the Sales Invoice has not"
                    " been sent to VFD!<br><br>Click on Send to VFD before submitting.",
                    "Cannot Submit Encounter",
                )
            )


@frappe.whitelist()
def undo_finalized_encounter(cur_encounter, ref_encounter=None):
    encounters_list = frappe.get_all(
        "Patient Encounter",
        filters={"docstatus": 1, "reference_encounter": ref_encounter},
    )
    for element in encounters_list:
        frappe.set_value("Patient Encounter", element.name, "finalized", 0)
    if not ref_encounter:
        frappe.set_value("Patient Encounter", cur_encounter, "finalized", 0)
        return
    frappe.set_value("Patient Encounter", cur_encounter, "encounter_type", "Ongoing")


def set_amounts(doc):
    childs_map = [
        {
            "table": "lab_test_prescription",
            "doctype": "Lab Test Template",
            "item": "lab_test_code",
        },
        {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Examination Template",
            "item": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "doctype": "Clinical Procedure Template",
            "item": "procedure",
        },
        {
            "table": "drug_prescription",
            "doctype": "Medication",
            "item": "drug_code",
        },
        {
            "table": "therapies",
            "doctype": "Therapy Type",
            "item": "therapy_type",
        },
    ]
    for child in childs_map:
        for row in doc.get(child.get("table")):
            item_rate = 0
            item_code = frappe.get_value(
                child.get("doctype"), row.get(child.get("item")), "item"
            )
            if row.amount:
                continue
            if row.prescribe and not doc.insurance_subscription:
                if doc.get("mode_of_payment"):
                    mode_of_payment = doc.get("mode_of_payment")
                elif doc.get("encounter_mode_of_payment"):
                    mode_of_payment = doc.get("encounter_mode_of_payment")
                item_rate = get_mop_amount(
                    item_code, mode_of_payment, doc.company, doc.patient
                )
                if not item_rate or item_rate == 0:
                    frappe.throw(
                        _("Cannot get mode of payment rate for item {0}").format(
                            item_code
                        )
                    )
            elif not row.prescribe:
                item_rate = get_item_rate(
                    item_code,
                    doc.company,
                    doc.insurance_subscription,
                    doc.insurance_company,
                )
            row.amount = item_rate


def inpatient_billing(patient_encounter_doc, method):
    if patient_encounter_doc.insurance_subscription:  # IPD/OPD insurance
        return
    if not patient_encounter_doc.inpatient_record:  # OPD cash or insurance
        return
    child_tables_list = [
        "lab_test_prescription",
        "radiology_procedure_prescription",
        "procedure_prescription",
    ]
    for child_table_field in child_tables_list:
        if patient_encounter_doc.get(child_table_field):
            child_table = patient_encounter_doc.get(child_table_field)
            for child in child_table:
                if child.doctype == "Lab Prescription":
                    create_individual_lab_test(patient_encounter_doc, child)
                elif child.doctype == "Radiology Procedure Prescription":
                    create_individual_radiology_examination(
                        patient_encounter_doc, child
                    )
                elif child.doctype == "Procedure Prescription":
                    create_individual_procedure_prescription(
                        patient_encounter_doc, child
                    )
    create_delivery_note(patient_encounter_doc, method)


def show_last_prescribed(doc, method):
    if doc.is_new():
        return
    if method == "validate":
        msg = None
        for row in doc.drug_prescription:
            medication_list = frappe.db.sql(
                """
            select dn.posting_date, dni.item_code, dni.stock_qty, dni.uom from `tabDelivery Note` dn
            inner join `tabDelivery Note Item` dni on dni.parent = dn.name
                            where dni.item_code = %s
                            and dn.patient = %s
                            and dn.docstatus = 1
                            order by posting_date desc
                            limit 1"""
                % ("%s", "%s"),
                (row.drug_code, doc.patient),
                as_dict=1,
            )
            if len(medication_list) > 0:
                msg = (
                    (msg or "")
                    + _(
                        "<strong>"
                        + row.drug_code
                        + "</strong>"
                        + " qty: <strong>"
                        + str(medication_list[0].get("stock_qty"))
                        + "</strong>, prescribed last on: <strong>"
                        + str(medication_list[0].get("posting_date"))
                    )
                    + "</strong><br>"
                )
        if msg:
            frappe.msgprint(
                _(
                    "The below are the last related medication prescriptions:<br><br>"
                    + msg
                )
            )


def update_drug_prescription(patient_encounter_doc, name):
    dn_doc = frappe.get_doc("Delivery Note", name)

    for d in patient_encounter_doc.drug_prescription:
        if d.parent == dn_doc.reference_name:
            for item in dn_doc.items:
                if (d.name == item.reference_name) and (d.drug_code == item.item_code):
                    frappe.db.set_value(
                        "Drug Prescription", item.reference_name, "dn_detail", item.name
                    )


def validate_patient_balance_vs_patient_costs(doc):
    encounters = get_patient_encounters(doc)
    if not encounters or len(encounters) == 0:
        return

    total_amount_billed = 0
    for enc in encounters:
        encounter_doc = frappe.get_doc("Patient Encounter", enc)

        for lab in encounter_doc.lab_test_prescription:
            if (
                lab.prescribe == 0 or 
                lab.is_not_available_inhouse ==  1 or 
                lab.invoiced == 1 or
                lab.is_cancelled == 1
            ):
                continue
        
            total_amount_billed += lab.amount
        
        for radiology in encounter_doc.radiology_procedure_prescription:
            if (
                radiology.prescribe == 0 or
                radiology.is_not_available_inhouse == 1 or
                radiology.invoiced == 1 or
                radiology.is_cancelled == 1
            ):
                retur
                
            total_amount_billed += radiology.amount

        for procedure in encounter_doc.procedure_prescription:
            if (
                procedure.prescribe == 0 or
                procedure.is_not_available_inhouse == 1 or
                procedure.invoiced == 1 or
                procedure.is_cancelled == 1
            ):
                return

            total_amount_billed += procedure.amount
        
        for drug in encounter_doc.drug_prescription:
            if (
                drug.prescribe == 0 or
                drug.is_not_available_inhouse == 1 or
                drug.invoiced == 1 or
                drug.is_cancelled == 1
            ):
                return

            total_amount_billed += (drug.quantity * drug.amount)
        
        for plan in encounter_doc.therapies:
            if (
                plan.prescribe == 0 or
                plan.is_not_available_inhouse == 1 or
                plan.invoiced == 1 or
                lab.is_cancelled == 1
            ):
                return

            total_amount_billed += plan.amount

    inpatient_record_doc = frappe.get_doc("Inpatient Record", doc.inpatient_record)

    cash_limit = inpatient_record_doc.cash_limit

    for record in inpatient_record_doc.inpatient_occupancies:
        if not record.is_confirmed:
            continue

        total_amount_billed += record.amount

    for record in inpatient_record_doc.inpatient_consultancy:
        if not record.is_confirmed:
            continue
        
        total_amount_billed += record.rate

    # get balance from payment entry after patient has deposit advances 
    deposit_balance = get_balance_on(party_type="Customer", party=doc.patient_name, company=doc.company)

    patient_balance = ( -1 * deposit_balance) + cash_limit

    if patient_balance < total_amount_billed:
        frappe.throw(frappe.bold("The deposit balance of this patient {0} - {1} is not enough or\
            the patient has reached the cash limit. In order to submit this encounter,\
            please request patient to deposit advances or request patient cash limit adjustment".format(doc.patient, doc.patient_name)))

def get_patient_encounters(doc):
    if doc.mode_of_payment != "" and doc.inpatient_record != "":
        patient_encounters = frappe.get_all(
            "Patient Encounter",
            filters={
                "patient": doc.patient,
                "appointment": doc.appointment,
                "inpatient_record": doc.inpatient_record,
            },
            fields=["name"],
            pluck="name",
        )
        return patient_encounters


def show_last_prescribed_for_lrpt(doc):
    childs_map = [
        {
            "table": "lab_test_prescription",
            "doctype": "Lab Test Template",
            "item": "lab_test_code",
            "ref_doc": "Lab Test",
            "field_name": "template",
        },
        {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Examination Template",
            "item": "radiology_examination_template",
            "ref_doc": "Radiology Examination",
            "field_name": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "doctype": "Clinical Procedure Template",
            "item": "procedure",
            "ref_doc": "Clinical Procedure",
            "field_name": "procedure_template",
        },
        # {
        # "table": "therapies",
        # "doctype": "Therapy Type",
        # "item": "therapy_type",
        # "ref_doc": "Therapy Plan",
        # "field_name": "therapy_plan_template"
        # }
    ]

    msg = ""
    for child in childs_map:
        msg_print = ""
        for entry in doc.get(child.get("table")):
            conditions = {
                "patient": doc.patient,
                child.get("field_name"): entry.get(child.get("item")),
            }

            item_doc = frappe.get_all(
                child.get("ref_doc"),
                filters=conditions,
                fields=[child.get("field_name"), "creation"],
                order_by="creation DESC",
                limit=1,
            )

            if len(item_doc) > 0:
                date = item_doc[0]["creation"].strftime("%Y-%m-%d")

                msg_print += _(
                    msg_print
                    + "{0} prescribed last on: {1}".format(
                        frappe.bold(entry.get(child.get("item"))), frappe.bold(date)
                    )
                    + "<br>"
                )

        msg += msg_print

    for plan in doc.therapies:
        items = frappe.db.sql(
            """ 
            SELECT tpd.therapy_type, Date(tpd.creation) AS date FROM `tabTherapy Plan Detail` tpd
            INNER JOIN `tabTherapy Plan` tp ON tpd.parent = tp.name WHERE tp.patient = %s 
            AND tpd.therapy_type = %s """
            % (frappe.db.escape(doc.patient), frappe.db.escape(plan.therapy_type)),
            as_dict=1,
        )

        if items:
            msg = _(
                msg
                + "{0} prescribed last on: {1}".format(
                    frappe.bold(items[0]["therapy_type"]), frappe.bold(items[0]["date"])
                )
                + "<br>"
            )

    if msg:
        frappe.msgprint(
            _("The below are the last related Item prescribed:<br><br>" + msg)
        )
