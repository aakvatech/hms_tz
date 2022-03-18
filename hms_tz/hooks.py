# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "hms_tz"
app_title = "HMS TZ"
app_publisher = "Aakvatech"
app_description = "HMS TZ"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@aakvatech.com"
app_license = "MIT"


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hms_tz/css/hms_tz.css"
# app_include_js = "/assets/hms_tz/js/hms_tz.js"

# include js, css files in header of web template
# web_include_css = "/assets/hms_tz/css/hms_tz.css"
# web_include_js = "/assets/hms_tz/js/hms_tz.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hms_tz/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Patient Appointment": "nhif/api/patient_appointment.js",
    "Patient": "nhif/api/patient.js",
    "Sales Order": "nhif/api/sales_order.js",
    "Sales Invoice": "nhif/api/sales_invoice.js",
    "Patient Encounter": "nhif/api/patient_encounter.js",
    "Lab Test": "nhif/api/lab_test.js",
    "Healthcare Service Order": "nhif/api/service_order.js",
    "Healthcare Insurance Company": "nhif/api/insurance_company.js",
    "Vital Signs": "nhif/api/vital_signs.js",
    "Healthcare Insurance Subscription": "nhif/api/insurance_subscription.js",
    "Inpatient Record": "nhif/api/inpatient_record.js",
    "Healthcare Service Unit": "nhif/api/service_unit.js",
    "Therapy Plan": "nhif/api/therapy_plan.js",
}
# csf_tz.nhif.api.patient_appointment
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
doctype_list_js = {"Therapy Plan" : "nhif/api/therapy_plan_list.js"}

inpatient_record_list_js = {"doctype": "nhif/api/inpatient_record_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "hms_tz.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "hms_tz.install.before_install"
# after_install = "hms_tz.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hms_tz.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Patient Appointment": {
        "validate": [
            "hms_tz.nhif.api.patient_appointment.make_next_doc",
        ]
    },
    "Vital Signs": {
        "on_submit": "hms_tz.nhif.api.patient_appointment.make_encounter",
    },
    "Patient": {
        "validate": "hms_tz.nhif.api.patient.validate",
        "after_insert": "hms_tz.nhif.api.patient.after_insert",
    },
    # "Healthcare Insurance Claim": {
    #     "before_insert": [
    #         "hms_tz.nhif.api.insurance_claim.set_patient_encounter",
    #         "hms_tz.nhif.api.insurance_claim.set_price",
    #     ]
    # },
    "Patient Encounter": {
        "before_submit": "hms_tz.nhif.api.patient_encounter.before_submit",
        "validate": "hms_tz.nhif.api.patient_encounter.on_submit_validation",
        "on_trash": "hms_tz.nhif.api.patient_encounter.on_trash",
        "on_submit": "hms_tz.nhif.api.patient_encounter.on_submit",
    },
    "Healthcare Service Order": {
        "before_insert": "hms_tz.nhif.api.service_order.set_missing_values",
    },
    "Sales Invoice": {
        "before_submit": "hms_tz.nhif.api.sales_invoice.before_submit",
        "on_submit": "hms_tz.nhif.api.sales_invoice.on_submit",
        "validate": "hms_tz.nhif.api.sales_invoice.validate",
    },
    "Healthcare Insurance Subscription": {
        "before_insert": "hms_tz.nhif.api.insurance_subscription.before_insert",
        "on_submit": "hms_tz.nhif.api.insurance_subscription.on_submit",
        "before_cancel": "hms_tz.nhif.api.insurance_subscription.on_cancel",
        "on_update_after_submit": "hms_tz.nhif.api.insurance_subscription.on_update_after_submit",
    },
    "Practitioner Availability": {
        "validate": "hms_tz.nhif.api.practitioner_availability.validate",
        "on_trash": "hms_tz.nhif.api.practitioner_availability.on_trash",
    },
    "Lab Test": {
        "on_submit": "hms_tz.nhif.api.lab_test.on_submit",
        "after_insert": "hms_tz.nhif.api.lab_test.after_insert",
        "on_trash": "hms_tz.nhif.api.lab_test.on_trash",
        "validate": "hms_tz.nhif.api.lab_test.validate",
    },
    "Radiology Examination": {
        "on_submit": "hms_tz.nhif.api.radiology_examination.on_submit",
        "validate": "hms_tz.nhif.api.radiology_examination.validate",
    },
    "Clinical Procedure": {
        "on_submit": "hms_tz.nhif.api.clinical_procedure.on_submit",
        "validate": "hms_tz.nhif.api.clinical_procedure.validate",
    },
    "Delivery Note": {
        "validate": "hms_tz.nhif.api.delivery_note.validate",
        "onload": "hms_tz.nhif.api.delivery_note.onload",
        "after_insert": "hms_tz.nhif.api.delivery_note.after_insert",
        "before_submit": "hms_tz.nhif.api.delivery_note.before_submit",
        "on_submit": "hms_tz.nhif.api.delivery_note.on_submit",
    },
    "Inpatient Record": {
        "validate": "hms_tz.nhif.api.inpatient_record.validate",
        "after_insert": "hms_tz.nhif.api.inpatient_record.after_insert",
    },
    "Prescription Dosage": {
        "before_insert": "hms_tz.nhif.api.prescription_dosage.before_insert",
    },
#    "Therapy Plan": {
#        "validate": "hms_tz.nhif.api.therapy_plan.validate",
#    },
}

# standard_queries = {
# 	"Healthcare Practitioner": "hms_tz.nhif.api.healthcare_practitioner.get_practitioner_list"
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    # 	"all": [
    # 		"hms_tz.tasks.all"
    # 	],
    # "cron": {"*/1 * * * *": ["hms_tz.nhif.api.service_order.real_auto_submit"]},
    "hourly": ["hms_tz.nhif.api.healthcare_utils.set_uninvoiced_so_closed"],
    "daily": ["hms_tz.nhif.api.inpatient_record.daily_update_inpatient_occupancies"],
    
    "cron": {
        # fire every saturday 2:30 pm at night
        "30 2 * * 6": [
            "hms_tz.nhif.api.healthcare_utils.delete_or_cancel_draft_document"
        ],
        # Routine for every five 5min
        "*/5 * * * *": [
            "hms_tz.nhif.api.healthcare_utils.create_invoiced_items_if_not_created"
        ]
    },
    # 	"hourly": [
    # 		"hms_tz.tasks.hourly"
    # 	],
    # 	"weekly": [
    # 		"hms_tz.tasks.weekly"
    # 	]
    # 	"monthly": [
    # 		"hms_tz.tasks.monthly"
    # 	]
}

jenv = {"methods": ["get_item_rate:hms_tz.nhif.api.healthcare_utils.get_item_rate"]}


# Testing
# -------

# before_tests = "hms_tz.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hms_tz.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hms_tz.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]
