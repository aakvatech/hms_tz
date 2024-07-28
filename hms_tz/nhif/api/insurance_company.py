# get_nhif_price_package

from __future__ import unicode_literals
from codecs import ignore_errors
from time import perf_counter
import frappe
from frappe import _
from hms_tz.nhif.api.token import get_claimsservice_token
import json
import requests
from frappe.utils.background_jobs import enqueue
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from frappe.utils import now
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from frappe.model.naming import set_new_name
import ast
from hms_tz.nhif.doctype.nhif_custom_excluded_services.nhif_custom_excluded_services import (
    get_custom_excluded_services,
)

from time import sleep


@frappe.whitelist()
def enqueue_get_nhif_price_package(company):
    enqueue(
        method=get_nhif_price_package,
        queue="long",
        timeout=10000000,
        is_async=True,
        kwargs=company,
    )
    return


def get_nhif_price_package(kwargs):
    company = kwargs
    user = frappe.session.user
    token = get_claimsservice_token(company, "NHIF")
    claimsserver_url, facility_code = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "insurance_provider": "NHIF"},
        ["claimsserver_url", "facility_code"],
    )
    headers = {"Authorization": "Bearer " + token}
    url = (
        str(claimsserver_url)
        + "/claimsserver/api/v1/Packages/GetPricePackageWithExcludedServices?FacilityCode="
        + str(facility_code)
    )
    r = requests.get(url, headers=headers, timeout=300)
    if r.status_code != 200:
        add_log(
            request_type="GetPricePackageWithExcludedServices",
            request_url=url,
            request_header=headers,
            response_data=r.text,
            status_code=r.status_code,
        )
        frappe.throw(json.loads(r.text))
    else:
        if json.loads(r.text):
            frappe.db.sql(
                """DELETE FROM `tabNHIF Price Package` WHERE company = '{0}' """.format(
                    company
                )
            )
            frappe.db.sql(
                """DELETE FROM `tabNHIF Excluded Services` WHERE company = '{0}' """.format(
                    company
                )
            )
            frappe.db.commit()

            # wait for 60 seconds before creating records again
            sleep(60)

            log_name = add_log(
                request_type="GetPricePackageWithExcludedServices",
                request_url=url,
                request_header=headers,
                response_data=r.text,
                status_code=r.status_code,
            )
            time_stamp = now()
            data = json.loads(r.text)
            insert_data = []
            for item in data.get("PricePackage"):
                insert_data.append(
                    (
                        frappe.generate_hash("", 20),
                        facility_code,
                        time_stamp,
                        log_name,
                        item.get("ItemCode"),
                        item.get("PriceCode"),
                        item.get("LevelPriceCode"),
                        item.get("OldItemCode"),
                        item.get("ItemTypeID"),
                        item.get("ItemName"),
                        item.get("Strength"),
                        item.get("Dosage"),
                        item.get("PackageID"),
                        item.get("SchemeID"),
                        item.get("FacilityLevelCode"),
                        item.get("UnitPrice"),
                        item.get("IsRestricted"),
                        item.get("MaximumQuantity"),
                        item.get("AvailableInLevels"),
                        item.get("PractitionerQualifications"),
                        item.get("IsActive"),
                        time_stamp,
                        time_stamp,
                        user,
                        user,
                        company,
                    )
                )
            frappe.db.sql(
                """
                INSERT INTO `tabNHIF Price Package`
                (
                    `name`, `facilitycode`, `time_stamp`, `log_name`, `itemcode`, `pricecode`,
                    `levelpricecode`, `olditemcode`, `itemtypeid`, `itemname`, `strength`, 
                    `dosage`, `packageid`, `schemeid`, `facilitylevelcode`, `unitprice`, 
                    `isrestricted`, `maximumquantity`, `availableinlevels`, 
                    `practitionerqualifications`, `IsActive`, `creation`, `modified`,
                    `modified_by`, `owner`,`company`
                )
                VALUES {}
            """.format(
                    ", ".join(["%s"] * len(insert_data))
                ),
                tuple(insert_data),
            )
            insert_data = []
            for item in data.get("ExcludedServices"):
                insert_data.append(
                    (
                        frappe.generate_hash("", 20),
                        facility_code,
                        time_stamp,
                        log_name,
                        item.get("ItemCode"),
                        item.get("SchemeID"),
                        item.get("SchemeName"),
                        item.get("ExcludedForProducts"),
                        time_stamp,
                        time_stamp,
                        user,
                        user,
                        company,
                    )
                )
            frappe.db.sql(
                """
                INSERT INTO `tabNHIF Excluded Services`
                (
                    `name`, `facilitycode`, `time_stamp`, `log_name`, `itemcode`, `schemeid`,
                    `schemename`, `excludedforproducts`, `creation`, `modified`,
                    `modified_by`, `owner`, `company`
                )
                VALUES {}
            """.format(
                    ", ".join(["%s"] * len(insert_data))
                ),
                tuple(insert_data),
            )
            set_nhif_diff_records(facility_code)
            frappe.db.commit()
            frappe.msgprint(_("Received data from NHIF"))
            return insert_data


@frappe.whitelist()
def process_nhif_records(company):
    enqueue(
        method=process_prices_list,
        queue="long",
        timeout=10000000,
        is_async=True,
        kwargs=company,
    )
    frappe.msgprint(_("Queued Processing NHIF price lists"), alert=True)
    enqueue(
        method=process_insurance_coverages,
        queue="long",
        timeout=10000000,
        is_async=True,
        kwargs=company,
    )
    frappe.msgprint(_("Queued Processing NHIF Insurance Coverages"), alert=True)


def process_prices_list(kwargs):
    company = kwargs
    facility_code = frappe.get_cached_value(
        "Company Insurance Setting",
        {"company": company, "insurance_provider": "NHIF"},
        "facility_code",
    )
    currency = frappe.get_cached_value("Company", company, "default_currency")
    schemeid_list = frappe.db.sql(
        """
            SELECT packageid, schemeid from `tabNHIF Price Package`
                WHERE facilitycode = {0}
                AND company = '{1}'
                GROUP BY packageid, schemeid
        """.format(
            facility_code, company
        ),
        as_dict=1,
    )

    for scheme in schemeid_list:
        price_list_name = "NHIF-" + scheme.packageid + "-" + facility_code
        if not frappe.db.exists("Price List", price_list_name):
            price_list_doc = frappe.new_doc("Price List")
            price_list_doc.price_list_name = price_list_name
            price_list_doc.currency = currency
            price_list_doc.buying = 0
            price_list_doc.selling = 1
            price_list_doc.save(ignore_permissions=True)

    item_list = frappe.db.sql(
        """
            SELECT icd.ref_code, icd.parent as item_code, npp.schemeid from `tabItem Customer Detail` icd
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                GROUP by icd.ref_code, icd.parent, npp.schemeid
        """,
        as_dict=1,
    )

    for item in item_list:
        for scheme in schemeid_list:
            schemeid = scheme.schemeid
            if item.schemeid != schemeid:
                continue
            price_list_name = "NHIF-" + scheme.packageid + "-" + facility_code
            package_list = frappe.db.sql(
                """
                    SELECT schemeid, itemcode, unitprice, isactive
                    FROM `tabNHIF Price Package` 
                    WHERE facilitycode = {0} and schemeid = {1} and itemcode = {2}
                    GROUP BY itemcode, schemeid, facilitylevelcode
                    ORDER BY facilitylevelcode
                    LIMIT 1
                """.format(
                    facility_code, schemeid, item.ref_code
                ),
                as_dict=1,
            )
            if len(package_list) > 0:
                for package in package_list:
                    item_price_list = frappe.get_all(
                        "Item Price",
                        filters={
                            "price_list": price_list_name,
                            "item_code": item.item_code,
                            "currency": currency,
                            "selling": 1,
                        },
                        fields=["name", "item_code", "price_list_rate"],
                    )
                    if len(item_price_list) > 0:
                        for price in item_price_list:
                            # 2023-05-16
                            # remove condition for isactive
                            # if package.isactive and int(package.isactive) == 1:

                            if float(price.price_list_rate) != float(package.unitprice):
                                # delete Item Price if no package.unitprice or it is 0
                                if (
                                    not float(package.unitprice)
                                    or float(package.unitprice) == 0
                                ):
                                    frappe.delete_doc("Item Price", price.name)
                                else:
                                    frappe.set_value(
                                        "Item Price",
                                        price.name,
                                        "price_list_rate",
                                        float(package.unitprice),
                                    )
                            # else:
                            # frappe.delete_doc("Item Price", price.name)

                    # elif package.isactive and int(package.isactive) == 1:
                    else:
                        item_price_doc = frappe.new_doc("Item Price")
                        item_price_doc.update(
                            {
                                "item_code": item.item_code,
                                "price_list": price_list_name,
                                "currency": currency,
                                "price_list_rate": float(package.unitprice),
                                "buying": 0,
                                "selling": 1,
                            }
                        )
                        item_price_doc.insert(ignore_permissions=True)
                        item_price_doc.save(ignore_permissions=True)
    frappe.db.commit()


def get_insurance_coverage_items(company):
    items_list = frappe.db.sql(
        """
            SELECT 'Appointment Type' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabAppointment Type` m ON icd.parent = m.out_patient_consulting_charge_item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Lab Test Template' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabLab Test Template` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Radiology Examination Template' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabRadiology Examination Template` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Clinical Procedure Template' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabClinical Procedure Template` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Medication' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabMedication` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Therapy Type' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabTherapy Type` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
            UNION ALL
            SELECT 'Healthcare Service Unit Type' as dt, m.name as healthcare_service_template, icd.ref_code, icd.parent as item_code, npp.schemeid
                FROM `tabItem Customer Detail` icd
                INNER JOIN `tabItem` i ON i.name = icd.parent and i.disabled = 0
                INNER JOIN `tabHealthcare Service Unit Type` m ON icd.parent = m.item
                INNER JOIN `tabNHIF Price Package` npp ON icd.ref_code = npp.itemcode
                WHERE icd.customer_name = 'NHIF'
                AND npp.company = {company}
                GROUP BY dt, m.name, icd.ref_code , icd.parent, npp.schemeid
        """.format(
            company=frappe.db.escape(company)
        ),
        as_dict=1,
    )
    return items_list


def get_excluded_services(itemcode, company):
    excluded_services = None
    excluded_services_list = frappe.get_all(
        "NHIF Excluded Services",
        filters={"itemcode": itemcode, "company": company},
        fields=["excludedforproducts", "schemeid"],
    )
    if len(excluded_services_list) > 0:
        excluded_services = excluded_services_list[0]
    return excluded_services


def get_price_package(itemcode, schemeid, company):
    price_package = ""
    price_package_list = frappe.get_all(
        "NHIF Price Package",
        filters={"itemcode": itemcode, "schemeid": schemeid, "company": company},
        fields=["maximumquantity", "isrestricted"],
    )
    if len(price_package_list) > 0:
        price_package = price_package_list[0]
    return price_package


def process_insurance_coverages(kwargs):
    company = kwargs
    items_list = get_insurance_coverage_items(company)

    coverage_plan_list = frappe.get_all(
        "Healthcare Insurance Coverage Plan",
        fields={"name", "nhif_scheme_id", "code_for_nhif_excluded_services"},
        filters={
            "insurance_company": ["like", "NHIF%"],
            "is_active": 1,
            "company": company,
        },
    )

    for plan in coverage_plan_list:
        insert_data = []
        time_stamp = now()
        user = frappe.session.user
        for item in items_list:
            if plan.nhif_scheme_id != item.schemeid:
                continue
            excluded_services = get_excluded_services(item.ref_code, company)
            if (
                excluded_services
                and excluded_services.excludedforproducts
                and plan.code_for_nhif_excluded_services
            ):
                if (
                    plan.code_for_nhif_excluded_services
                    in excluded_services.excludedforproducts
                ):
                    continue

            user_excluded_products = get_custom_excluded_services(
                company, item.ref_code
            )
            if (
                user_excluded_products
                and plan.code_for_nhif_excluded_services
                and plan.code_for_nhif_excluded_services in user_excluded_products
            ):
                continue

            doc = frappe.new_doc("Healthcare Service Insurance Coverage")
            doc.healthcare_service = item.dt
            doc.healthcare_service_template = item.healthcare_service_template
            doc.healthcare_insurance_coverage_plan = plan.name
            doc.company = company
            doc.coverage = 100
            doc.end_date = "2099-12-31"
            doc.is_active = 1
            doc.discount = 0

            maximumquantity = 0
            isrestricted = 0
            price_package = get_price_package(item.ref_code, item.schemeid, company)
            if price_package:
                if (
                    price_package.maximumquantity
                    and price_package.maximumquantity != "-1"
                ):
                    maximumquantity = int(price_package.maximumquantity)
                if price_package.isrestricted:
                    isrestricted = int(price_package.isrestricted)

            set_new_name(doc)

            insert_data.append(
                (
                    isrestricted,  # doc.approval_mandatory_for_claim,
                    doc.coverage,
                    time_stamp,
                    doc.discount,
                    doc.end_date,
                    doc.healthcare_insurance_coverage_plan,
                    doc.healthcare_service,
                    doc.healthcare_service_template,
                    doc.is_active,
                    isrestricted,  # doc.manual_approval_only,
                    maximumquantity,  # doc.maximum_number_of_claims,
                    time_stamp,
                    user,
                    doc.name,
                    doc.naming_series,
                    user,
                    doc.start_date,
                    1,
                    doc.company,
                )
            )

        if insert_data:
            if plan.name:
                frappe.db.sql(
                    "DELETE FROM `tabHealthcare Service Insurance Coverage` WHERE is_auto_generated = 1 AND healthcare_insurance_coverage_plan = '{0}'".format(
                        plan.name
                    )
                )
                frappe.db.commit()

            # wait for 60 seconds before creating HSIC records again
            sleep(60)

            frappe.db.sql(
                """
                INSERT INTO `tabHealthcare Service Insurance Coverage`
                (
                    `approval_mandatory_for_claim`, 
                    `coverage`, 
                    `creation`, 
                    `discount`, 
                    `end_date`, 
                    `healthcare_insurance_coverage_plan`, 
                    `healthcare_service`, 
                    `healthcare_service_template`, 
                    `is_active`, 
                    `manual_approval_only`, 
                    `maximum_number_of_claims`, 
                    `modified`, 
                    `modified_by`, 
                    `name`, 
                    `naming_series`, 
                    `owner`, 
                    `start_date`,
                    `is_auto_generated`,
                    `company`
                )
                VALUES {}
            """.format(
                    ", ".join(["%s"] * len(insert_data))
                ),
                tuple(insert_data),
            )
    frappe.db.commit()


def set_nhif_diff_records(FacilityCode):
    logs = frappe.get_all(
        "NHIF Response Log",
        filters={
            "request_type": "GetPricePackageWithExcludedServices",
            "response_data": ["not in", ["", None]],
            "request_url": ["like", "%" + FacilityCode + "%"],
        },
        order_by="creation desc",
        page_length=2,
    )
    if len(logs) > 1:
        current = logs[0].name
        previous = logs[1].name
    else:
        frappe.throw(_("There are not enough records in NHIF Response Log"))

    current_rec = json.loads(
        frappe.get_cached_value("NHIF Response Log", current, "response_data")
    )
    previous_rec = json.loads(
        frappe.get_cached_value("NHIF Response Log", previous, "response_data")
    )
    current_price_packages = current_rec.get("PricePackage")
    previousـprice_packages = previous_rec.get("PricePackage")

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
                if item.get("PriceCode") == e.get("PriceCode")
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
                if item.get("PriceCode") == z.get("PriceCode")
            ),
            None,
        )
        if not exist_rec:
            deleted_price_packages.append(z)

    doc = frappe.new_doc("NHIF Update")
    if (
        len(changed_price_packages)
        or len(new_price_packages)
        or len(deleted_price_packages)
    ):
        add_price_packages_records(doc, changed_price_packages, "Changed")
        add_price_packages_records(doc, new_price_packages, "New")
        add_price_packages_records(doc, deleted_price_packages, "Deleted")

    current_excluded_services = current_rec.get("ExcludedServices")
    previous_excluded_services = previous_rec.get("ExcludedServices")

    diff_current_excluded_services = [
        i for i in current_excluded_services if i not in previous_excluded_services
    ]
    diff_previous_excluded_services = [
        i for i in previous_excluded_services if i not in previous_excluded_services
    ]

    changed_excluded_services = []
    new_excluded_services = []

    for e in diff_current_excluded_services:
        exist_rec = next(
            (
                item
                for item in diff_previous_excluded_services
                if item.get("ItemCode") == e.get("ItemCode")
            ),
            None,
        )
        if exist_rec:
            changed_excluded_services.append(exist_rec)
        else:
            new_excluded_services.append(e)

    deleted_excluded_services = []

    for z in diff_previous_excluded_services:
        exist_rec = next(
            (
                item
                for item in diff_current_excluded_services
                if item.get("ItemCode") == z.get("ItemCode")
            ),
            None,
        )
        if not exist_rec:
            deleted_excluded_services.append(z)

    if (
        len(changed_excluded_services)
        or len(new_excluded_services)
        or len(deleted_excluded_services)
    ):
        add_excluded_services_records(doc, changed_excluded_services, "Changed")
        add_excluded_services_records(doc, new_excluded_services, "New")
        add_excluded_services_records(doc, deleted_excluded_services, "Deleted")

    if (doc.get("price_package") and len(doc.price_package)) or (
        doc.get("excluded_services") and (doc.excluded_services)
    ):
        doc.current_log = current
        doc.previous_log = previous
        doc.save(ignore_permissions=True)


def add_price_packages_records(doc, rec, type):
    if not len(rec) > 0:
        return
    for e in rec:
        price_row = doc.append("price_package", {})
        price_row.itemcode = e.get("ItemCode")
        price_row.type = type
        price_row.facilitycode = e.get("FacilityCode")
        price_row.package_item_id = e.get("PackageItemID")
        price_row.pricecode = e.get("PriceCode")
        price_row.levelpricecode = e.get("LevelPriceCode")
        price_row.olditemcode = e.get("OldItemCode")
        price_row.itemtypeid = e.get("ItemTypeID")
        price_row.itemname = e.get("ItemName")
        price_row.schemename = e.get("SchemeName")
        price_row.strength = e.get("Strength")
        price_row.dosage = e.get("Dosage")
        price_row.packageid = e.get("PackageID")
        price_row.schemeid = e.get("SchemeID")
        price_row.facilitylevelcode = e.get("FacilityLevelCode")
        price_row.unitprice = e.get("UnitPrice")
        price_row.isrestricted = e.get("IsRestricted")
        price_row.maximumquantity = e.get("MaximumQuantity")
        price_row.availableinlevels = e.get("AvailableInLevels")
        price_row.practitionerqualifications = e.get("PractitionerQualifications")
        price_row.IsActive = e.get("IsActive")
        price_row.record = json.dumps(e)


def add_excluded_services_records(doc, rec, type):
    if not len(rec) > 0:
        return
    for e in rec:
        price_row = doc.append("excluded_services", {})
        price_row.type = type
        price_row.itemcode = e.get("ItemCode")
        price_row.schemeid = e.get("SchemeID")
        price_row.schemename = e.get("SchemeName")
        price_row.excludedforproducts = e.get("ExcludedForProducts")
        price_row.record = json.dumps(e)
