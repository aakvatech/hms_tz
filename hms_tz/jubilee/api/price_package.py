import json
import frappe
from time import sleep
from frappe.query_builder import DocType
from frappe.utils.background_jobs import enqueue
from frappe.query_builder.terms import ValueWrapper
from frappe.utils import now_datetime, nowdate, flt


@frappe.whitelist()
def process_jubilee_records(company):
    enqueue(
        method=process_jubilee_price_list,
        job_name="process_jubilee_price_list",
        queue="default",
        timeout=10000000,
        is_async=True,
        company=company,
    )

    enqueue(
        method=process_jubilee_coverage,
        job_name="process_jubilee_coverage",
        queue="default",
        timeout=10000000,
        is_async=True,
        company=company,
    )


def sync_jubilee_price_package(
    packages, company, log_name, insurance_provider="Jubilee"
):
    if len(packages) == 0:
        return

    jpp = DocType("Jubilee Price Package")
    frappe.qb.from_(jpp).delete().where(jpp.company == company).run()

    sleep(60)
    create_price_package(packages, company, log_name)

    sleep(60)
    set_package_diff(company)


def create_price_package(packages, company, log_name):
    fields = [
        "name",
        "company",
        "itemcode",
        "itemname",
        "cleanname",
        "itemprice",
        "providerid",
        "log_name",
        "time_stamp",
    ]

    data = []
    time_stamp = now_datetime()
    for row in packages:
        jpp_name = frappe.generate_hash(length=10)

        data.append(
            (
                jpp_name,
                company,
                row.get("ItemCode"),
                row.get("ItemName"),
                row.get("CleanName"),
                row.get("ItemPrice"),
                row.get("ProviderID"),
                log_name,
                time_stamp,
            )
        )
    frappe.db.bulk_insert(
        "Jubilee Price Package", fields=fields, values=data, chunk_size=1000
    )


def process_jubilee_coverage(company, coverage_plan=None):
    hsic = DocType("Healthcare Service Insurance Coverage")

    coverage_plan_list = None
    if coverage_plan:
        coverage_plan_list.append({"name": coverage_plan})
    else:
        coverage_plan_list = frappe.get_all(
            "Healthcare Insurance Coverage Plan",
            fields={"name"},
            filters={
                "insurance_company": ["like", "%Jubilee%"],
                "company": company,
                "is_active": 1,
            },
            page_length=1,
        )

    if len(coverage_plan_list) == 0:
        frappe.throw("No active coverage plan found for Jubilee")

    for coverage_plan in coverage_plan_list:
        item_list = get_jubile_items(company)
        if len(item_list) == 0:
            frappe.throw("No items found for Jubilee")

        data = []
        for item in item_list:
            hsic_name = frappe.generate_hash(length=10)
            data.append(
                (
                    hsic_name,
                    now_datetime(),
                    now_datetime(),
                    frappe.session.user,
                    frappe.session.user,
                    company,
                    coverage_plan.get("name"),
                    100,
                    nowdate(),
                    "2099-12-31",
                    item.dt,
                    item.service_template,
                    1,
                    1,
                )
            )

        if len(data) > 0 and coverage_plan.get("name"):
            frappe.qb.from_(hsic).delete().where(
                (hsic.healthcare_insurance_coverage_plan == coverage_plan.get("name"))
                & (hsic.company == company)
                & (hsic.is_auto_generated == 1)
            ).run()

            sleep(60)

            fields = [
                "name",
                "creation",
                "modified",
                "modified_by",
                "owner",
                "company",
                "healthcare_insurance_coverage_plan",
                "coverage",
                "start_date",
                "end_date",
                "healthcare_service",
                "healthcare_service_template",
                "is_auto_generated",
                "is_active",
            ]
            frappe.db.bulk_insert(
                "Healthcare Service Insurance Coverage",
                fields=fields,
                values=data,
                chunk_size=1000,
            )

            sleep(60)


def process_jubilee_price_list(company, item=None):
    itp = DocType("Item Price")

    company_info = frappe.get_cached_value(
        "Company", company, ["abbr", "default_currency"], as_dict=True
    )
    price_list_name = f"Jubilee {company_info.abbr}"
    if not frappe.db.exists("Price List", price_list_name):
        price_list_doc = frappe.new_doc("Price List")
        price_list_doc.price_list_name = price_list_name
        price_list_doc.currency = company_info.default_currency
        price_list_doc.buying = 0
        price_list_doc.selling = 1
        price_list_doc.save(ignore_permissions=True)

    item_list = get_items_for_price_list(company, item)

    for item in item_list:
        item_price_list = (
            frappe.qb.from_(itp)
            .select("name", "item_code", "price_list_rate")
            .where(
                (itp.selling == 1)
                & (itp.price_list == price_list_name)
                & (itp.item_code == item.get("item_code"))
                & (itp.currency == company_info.default_currency)
            )
        ).run(as_dict=True)

        if len(item_price_list) > 0:
            for price in item_price_list:
                if flt(price.price_list_rate) != flt(item.itemprice):
                    # delete Item Price if no item.itemprice or it is 0
                    if not flt(item.itemprice) or flt(item.itemprice) == 0:
                        frappe.qb.from_(itp).delete().where(
                            itp.name == price.name
                        ).run()
                    else:
                        # update Item Price with the new price
                        frappe.qb.update(itp).set(
                            itp.price_list_rate, flt(item.itemprice)
                        ).where(itp.name == price.name).run()
        else:
            item_price_doc = frappe.new_doc("Item Price")
            item_price_doc.update(
                {
                    "item_code": item.item_code,
                    "price_list": price_list_name,
                    "currency": company_info.default_currency,
                    "price_list_rate": flt(item.itemprice),
                    "buying": 0,
                    "selling": 1,
                }
            )
            item_price_doc.insert(ignore_permissions=True)
            item_price_doc.save(ignore_permissions=True)

    frappe.db.commit()


def set_package_diff(company):
    logs = frappe.get_all(
        "Jubilee Response Log",
        filters={
            "request_type": "GetPricePackage",
            "response_data": ["not in", ["", None]],
            "company": company,
        },
        fields=["name", "response_data"],
        order_by="creation desc",
        page_length=2,
    )
    if len(logs) < 2:
        return

    current_rec = json.loads(logs[0]["response_data"])
    previous_rec = json.loads(logs[1]["response_data"])
    current_price_packages = current_rec.get("Description")
    previousـprice_packages = previous_rec.get("Description")

    diff_price_packages_from_current = [
        i for i in current_price_packages if i not in previousـprice_packages
    ]
    diff_price_packages_from_previous = [
        i for i in previousـprice_packages if i not in current_price_packages
    ]

    changed_price_packages = []
    new_price_packages = []

    for e in diff_price_packages_from_current:
        exist_rec = next(
            (
                item
                for item in diff_price_packages_from_previous
                if item.get("ItemCode") == e.get("ItemCode")
            ),
            None,
        )
        if exist_rec:
            changed_price_packages.append(exist_rec)
        else:
            new_price_packages.append(e)

    deleted_price_packages = []

    for z in diff_price_packages_from_previous:
        exist_rec = next(
            (
                item
                for item in diff_price_packages_from_current
                if item.get("ItemCode") == z.get("ItemCode")
            ),
            None,
        )
        if not exist_rec:
            deleted_price_packages.append(z)

    if (
        len(changed_price_packages) > 0
        or len(new_price_packages) > 0
        or len(deleted_price_packages) > 0
    ):
        doc = frappe.new_doc("Jubilee Update")

        add_price_packages_records(doc, changed_price_packages, "Changed")
        add_price_packages_records(doc, new_price_packages, "New")
        add_price_packages_records(doc, deleted_price_packages, "Deleted")

        if (doc.get("price_package") and len(doc.price_package)) or ():
            doc.company = company
            doc.current_log = logs[0].name
            doc.previous_log = logs[1].name
            doc.save(ignore_permissions=True)


def add_price_packages_records(doc, rec, type):
    if not len(rec) > 0:
        return

    for e in rec:
        price_row = doc.append("price_package", {})
        price_row.itemcode = e.get("ItemCode")
        price_row.type = type
        price_row.olditemcode = e.get("OldItemCode")
        price_row.itemname = e.get("ItemName")
        price_row.strength = e.get("Strength")
        price_row.dosage = e.get("Dosage")
        price_row.unitprice = e.get("UnitPrice")
        price_row.record = json.dumps(e)


def get_jubile_items(company):
    lab_items = get_lab_templates(company)
    radiology_items = get_radiology_templates(company)
    procedure_items = get_procedure_templates(company)
    medication_items = get_medication_templates(company)
    therapy_items = get_therapy_templates(company)
    hsut_items = get_healthcare_service_unit_types(company)

    item_list = (
        lab_items
        + radiology_items
        + procedure_items
        + medication_items
        + therapy_items
        + hsut_items
    )

    return item_list


def get_lab_templates(company):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")
    lab = DocType("Lab Test Template")

    lab_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(lab)
        .on(icd.parent == lab.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Lab Test Template").as_("dt"),
            lab.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "Jubilee")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(lab.name, icd.ref_code, icd.parent)
    )
    lab_data = lab_query.run(as_dict=True)

    return lab_data


def get_radiology_templates(company):
    jpp = DocType("Jubilee Price Package")
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    radiology = DocType("Radiology Examination Template")

    radiology_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(radiology)
        .on(icd.parent == radiology.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Radiology Examination Template").as_("dt"),
            radiology.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "The Jubilee Insurance (T) Ltd")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(radiology.name, icd.ref_code, icd.parent)
    )

    radiology_data = radiology_query.run(as_dict=True)

    return radiology_data


def get_procedure_templates(company):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")
    procedure = DocType("Clinical Procedure Template")

    procedure_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(procedure)
        .on(icd.parent == procedure.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Clinical Procedure Template").as_("dt"),
            procedure.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "The Jubilee Insurance (T) Ltd")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(procedure.name, icd.ref_code, icd.parent)
    )

    procedure_data = procedure_query.run(as_dict=True)
    return procedure_data


def get_medication_templates(company):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")
    medication = DocType("Medication")

    medication_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(medication)
        .on(icd.parent == medication.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Medication").as_("dt"),
            medication.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "The Jubilee Insurance (T) Ltd")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(medication.name, icd.ref_code, icd.parent)
    )

    medication_data = medication_query.run(as_dict=True)
    return medication_data


def get_therapy_templates(company):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")
    therapy = DocType("Therapy Type")

    therapy_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(therapy)
        .on(icd.parent == therapy.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Therapy Type").as_("dt"),
            therapy.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "The Jubilee Insurance (T) Ltd")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(therapy.name, icd.ref_code, icd.parent)
    )

    therapy_data = therapy_query.run(as_dict=True)
    return therapy_data


def get_healthcare_service_unit_types(company):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")
    hsut = DocType("Healthcare Service Unit Type")

    hsut_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(hsut)
        .on(icd.parent == hsut.item)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            ValueWrapper("Healthcare Service Unit Type").as_("dt"),
            hsut.name.as_("service_template"),
            icd.ref_code,
            icd.parent.as_("item_code"),
        )
        .where(
            (icd.customer_name == "The Jubilee Insurance (T) Ltd")
            & (it.disabled == 0)
            & (jpp.company == company)
        )
        .groupby(hsut.name, icd.ref_code, icd.parent)
    )

    hsut_data = hsut_query.run(as_dict=True)
    return hsut_data


def get_items_for_price_list(company, item=None):
    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    jpp = DocType("Jubilee Price Package")

    item_query = (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(it.name == icd.parent)
        .inner_join(jpp)
        .on(icd.ref_code == jpp.itemcode)
        .select(
            icd.ref_code,
            icd.parent.as_("item_code"),
            jpp.itemcode,
            jpp.itemname,
            jpp.cleanname,
            jpp.itemprice,
        )
        .where(
            (it.disabled == 0)
            & (jpp.company == company)
            & (icd.customer_name == "The Jubilee Insurance (T) Ltd")
        )
        .groupby(icd.ref_code, icd.parent)
    )
    if item:
        item_query = item_query.where(icd.parent == item)

    item_data = item_query.run(as_dict=True)
    return item_data
