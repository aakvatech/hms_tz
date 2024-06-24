import json
import frappe
from time import sleep
from frappe.utils import now_datetime
from frappe.query_builder import DocType


def sync_jubilee_price_package(
    packages, company, log_name, insurance_provider="Jubilee"
):
    if len(packages) == 0:
        return

    delete_price_package(company)

    sleep(30)
    create_price_package(packages, company, log_name)

    sleep(30)
    set_package_diff(company)


def delete_price_package(company):
    jpp = DocType("Jubilee Price Package")
    frappe.qb.from_(jpp).delete().where(jpp.company == company).run()


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
