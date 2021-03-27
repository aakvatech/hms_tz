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

fixtures = [
    {"doctype": "Custom Field", "filters": [["name", "in", (
        "Delivery Note Item-reference_doctype",
        "Delivery Note Item-reference_name",
        "Delivery Note-reference_doctype",
        "Delivery Note-reference_name",
        "Diet Recommendation-medical_code",
        "Drug Prescription-medical_code",
        "Drug Prescription-override_subscription",
        "Drug Prescription-prescribe",
        "Healthcare Insurance Claim-column_break_38",
        "Healthcare Insurance Claim-insurance_company_item_code",
        "Healthcare Insurance Claim-insurance_company_item_name",
        "Healthcare Insurance Claim-order_encounter",
        "Healthcare Insurance Claim-ready_to_submit",
        "Healthcare Insurance Claim-reference_dn",
        "Healthcare Insurance Claim-reference_dt",
        "Healthcare Insurance Claim-section_break_35",
        "Healthcare Insurance Claim-section_break_40",
        "Healthcare Insurance Company-default_price_list",
        "Healthcare Insurance Company-facility_code",
        "Healthcare Insurance Subscription-coverage_plan_card_number",
        "Healthcare Insurance Subscription-coverage_plan_name",
        "Patient Encounter-healthcare_practitioner_signature",
        "Patient Encounter-patient_signature",
        "Healthcare Practitioner-doctors_signature",
        "Healthcare Practitioner-title_and_qualification",
        "Healthcare Practitioner-tz_mct_code",
        "Healthcare Service Insurance Coverage-maximum_claim_duration",
        "Healthcare Service Order-clear_insurance_details",
        "Healthcare Service Order-original_his",
        "Healthcare Service Order-prescribed",
        "Inpatient Record-patient_vitals",
        "Inpatient Record-patient_vitals_summary",
        "Inpatient Record-practitioner_name",
        "Inpatient Record-primary_practitioner_name",
        "Inpatient Record-secondary_practitioner_name",
        "Lab Prescription-medical_code",
        "Lab Prescription-override_subscription",
        "Lab Prescription-prescribe",
        "Lab Test Template-c_max_range",
        "Lab Test Template-c_min_range",
        "Lab Test Template-c_text",
        "Lab Test Template-column_break_26",
        "Lab Test Template-column_break_30",
        "Lab Test Template-column_break_34",
        "Lab Test Template-f_max_range",
        "Lab Test Template-f_min_range",
        "Lab Test Template-f_text",
        "Lab Test Template-i_max_range",
        "Lab Test Template-i_min_range",
        "Lab Test Template-i_text",
        "Lab Test Template-lab_routine_normals",
        "Lab Test Template-m_max_range",
        "Lab Test Template-m_min_range",
        "Lab Test Template-m_text",
        "Medication-default_comments",
        "Normal Test Result-detailed_normal_range",
        "Normal Test Result-max_normal",
        "Normal Test Result-min_normal",
        "Normal Test Result-result_status",
        "Normal Test Result-text_normal",
        "Patient Appointment-authorization_number",
        "Patient Appointment-coverage_plan_card_number",
        "Patient Appointment-coverage_plan_name",
        "Patient Appointment-get_authorization_number",
        "Patient Appointment-insurance_company_name",
        "Patient Appointment-nhif_patient_claim",
        "Patient Appointment-patient_image2",
        "Patient Appointment-ref_vital_signs",
        "Patient Appointment-reference_journal_entry",
        "Patient Appointment-healthcare_referrer_type",
        "Patient Appointment-healthcare_referrer",
        "Patient Appointment-referral_no",
        "Patient Encounter Symptom-system",
        "Patient Encounter-blood_group",
        "Patient Encounter-column_break_31",
        "Patient Encounter-encounter_type",
        "Patient Encounter-examination_detail",
        "Patient Encounter-from_encounter",
        "Patient Encounter-healthcare_referrer",
        "Patient Encounter-healthcare_service_unit",
        "Patient Encounter-image",
        "Patient Encounter-patient_encounter_final_diagnosis",
        "Patient Encounter-patient_encounter_preliminary_diagnosis",
        "Patient Encounter-previous_diet_recommendation",
        "Patient Encounter-previous_drug_prescription",
        "Patient Encounter-previous_lab_prescription",
        "Patient Encounter-previous_procedure_prescription",
        "Patient Encounter-previous_radiology_procedure_prescription",
        "Patient Encounter-previous_therapy_plan_detail",
        "Patient Encounter-reference",
        "Patient Encounter-reference_encounter",
        "Patient Encounter-section_break_28",
        "Patient Encounter-section_break_52",
        "Patient Encounter-symptoms_and_signs",
        "Patient Encounter-system_and_symptoms",
        "Patient-card_no",
        "Patient-column_break_3",
        "Patient-insurance_company",
        "Patient-insurance_details",
        "Patient-membership_no",
        "Patient-next_to_kid_column_break",
        "Patient-next_to_kin_details",
        "Patient-next_to_kin_mobile_no",
        "Patient-next_to_kin_name",
        "Patient-next_to_kin_relationship",
        "Patient-patient_details_with_formatting",
        "Patient-product_code",
        "Payment Entry Reference-end_date",
        "Payment Entry Reference-posting_date",
        "Payment Entry Reference-section_break_9",
        "Payment Entry Reference-start_date",
        "Procedure Prescription-column_break_10",
        "Procedure Prescription-hso_payment_method",
        "Procedure Prescription-medical_code",
        "Procedure Prescription-override_insurance_subscription",
        "Procedure Prescription-override_subscription",
        "Procedure Prescription-prescribe",
        "Radiology Examination Template-body_part",
        "Radiology Examination Template-radiology_report",
        "Radiology Examination Template-radiology_report_details",
        "Radiology Examination Template-radiology_report_type",
        "Radiology Examination-body_part",
        "Radiology Examination-radiology_report",
        "Radiology Examination-radiology_report_details",
        "Radiology Procedure Prescription-medical_code",
        "Radiology Procedure Prescription-override_subscription",
        "Radiology Procedure Prescription-prescribe",
        "Therapy Plan Detail-column_break_6",
        "Therapy Plan Detail-comment",
        "Therapy Plan Detail-medical_code",
        "Therapy Plan Detail-override_subscription",
        "Therapy Plan Detail-prescribe",
        "Vital Signs-height_in_cm",
        "Vital Signs-image",
        "Vital Signs-oxygen_saturation_spo2",
        "Vital Signs-rbg",
        "Patient-old_hms_registration_no",
        "Patient Encounter-insurance_coverage_plan",
        "Patient Encounter-mode_of_payment",
        "Patient-insurance_card_detail",
        "Healthcare Service Insurance Coverage-is_auto_generated",
        "Patient Encounter-current_total",
        "Patient Encounter-previous_total",
        "Patient Encounter-daily_limit",
        "Patient Appointment-daily_limit",
        "Healthcare Practitioner-abbreviation",
        "Patient Encounter-abbr",
        "Healthcare Insurance Subscription-daily_limit",
        "Vital Signs-healthcare_practitioner",
        "Vital Signs-verbal_response",
        "Vital Signs-motor_response",
        "Vital Signs-eye_opening",
        "Vital Signs-glasgow_coma_scale",
        "Vital Signs-column_break_29",
        "Patient Appointment-send_vfd",
        "Lab Test-ref_doctype",
        "Lab Test-ref_docname",
        "Radiology Examination-ref_doctype",
        "Radiology Examination-ref_docname",
        "Clinical Procedure-ref_doctype",
        "Clinical Procedure-ref_docname",
        "Medication-ref_doctype",
        "Medication-ref_docname",
        "Therapy Plan-ref_doctype",
        "Therapy Plan-ref_docname",
        "Medication-strength_text",
        "Appointment Type-visit_type_id",
        "Patient Encounter Symptom-complaint_comments",
        "Patient Encounter Symptom-complaint_duration",
        "Patient Encounter-ed_no_of_days",
        "Patient Encounter-ed_addressed_to",
        "Patient Encounter-ed_reason_for_absence",
        "Codification Table-mtuha",
        "Sample Collection-section_break_20",
        "Sample Collection-ref_doctype",
        "Sample Collection-ref_docname",
        "Healthcare Practitioner-nhif_physician_qualification",
        "Vital Signs-patient_progress",
        "Stock Entry Detail-inpatient_medication_entry_child",
        "Stock Entry Detail-patient",
        "Stock Entry-inpatient_medication_entry",
        "Sales Invoice Item-reference_dn",
        "Sales Invoice Item-reference_dt",
        "Sales Invoice-ref_practitioner",
        "Sales Invoice-patient_name",
        "Sales Invoice-patient",
        "Patient Referral-referred_to_facility",
        "Clinical Procedure Template-is_not_available_inhouse",
        "Therapy Plan Template-is_not_available_inhouse",
        "Medication-is_not_available_inhouse",
        "Lab Test Template-is_not_available_inhouse",
        "Radiology Examination Template-is_not_available_inhouse",
        "Descriptive Test Result-result_component_option",
        "Descriptive Test Template-result_component",
        "Patient Encounter-patient_info_section_break",
        "Vital Signs-mode_of_payment",
        "Delivery Note Item-recommended_qty",
        "Item-recommended_qty",
        "Delivery Note Item-last_qty_prescribed",
        "Delivery Note Item-last_date_prescribed",
        "Delivery Note Item-column_break_89",
        "Delivery Note Item-approval_type",
        "Delivery Note Item-approval_number",
        "Delivery Note Item-original_stock_uom_qty",
        "Delivery Note Item-original_item",
        "Delivery Note Item-healthcare",
        "Delivery Note-patient_name",
        "Delivery Note-patient",
        "Delivery Note-healthcare_service_unit",
        "Delivery Note-medical_department",
        "Drug Prescription-is_restricted",
        "Delivery Note Item-is_restricted",
        "Patient Encounter-encounter_category",
        "Patient Encounter-finalized",
        "Patient-nida_card_number",
        "Patient Encounter-encounter_mode_of_payment",
        "Patient Encounter-create_sales_invoice",
        "Patient Encounter-sales_invoice",
        "Patient Encounter-sent_to_vfd",
        "Lab Test Template-healthcare_service_unit",
        "Drug Prescription-healthcare_service_unit",
        "Patient Encounter-default_healthcare_service_unit",
        "Radiology Examination Template-healthcare_service_unit",
        "Clinical Procedure Template-healthcare_service_unit"
        "Inpatient Record-when_to_obtain_urgent_care",
        "Inpatient Record-surgical_procedure",
        "Inpatient Record-medication",
        "Inpatient Record-review",
        "Inpatient Record-on_examination",
        "Inpatient Record-history",
        "Patient Appointment-payment_reference",
        "Mode of Payment-price_list",
        "Patient Encounter-signatures",
        "Patient Encounter-copy_from_preliminary_diagnosis",
        "Patient Encounter-get_chronic_medications",
        "Patient Encounter-get_chronic_diagnosis",
        "Patient-chronic_medications",
        "Patient-codification_table",
        "Patient-chronic_section",
        "Inpatient Record-insurance_coverage_plan",
        "Inpatient Occupancy-delivery_note",
        "Inpatient Occupancy-confirmed",
        "Inpatient Record-inpatient_consultancy",
        "Inpatient Record-inpatient_consultancies",
        "Vital Signs-section_break_2",
        "Vital Signs-patient_vitals",
        "Vital Signs-patient_vitals_summary",
        "Therapy Type-is_not_available_inhouse",
        "Radiology Examination-healthcare_practitioner_name",
        "Clinical Procedure Template-healthcare_service_unit",
        "Healthcare Practitioner-default_medication_healthcare_service_unit",
        "Healthcare Practitioner-default_values",
        "Lab Test-is_restricted",
        "Lab Test-approval_number",
        "Lab Test-approval_type",
        "Healthcare Service Insurance Coverage-item",
        "Radiology Examination-is_restricted",
        "Radiology Examination-approval_number",
        "Radiology Examination-approval_type",
        "Clinical Procedure-is_restricted",
        "Clinical Procedure-approval_number",
        "Clinical Procedure-approval_type",
        "Previous Therapy Plan Detail-comment",
        "Previous Therapy Plan Detail-column_break_6",
        "Previous Therapy Plan Detail-prescribe",
        "Previous Therapy Plan Detail-override_subscription",
        "Inpatient Consultancy-encounter",
        "Patient Encounter-is_not_billable",
        "Patient Encounter-duplicated",
        "Procedure Prescription-is_not_available_inhouse",
        "Radiology Procedure Prescription-is_not_available_inhouse",
        "Drug Prescription-is_not_available_inhouse",
        "Lab Prescription-is_not_available_inhouse",
        "Therapy Plan Detail-is_not_available_inhouse",
        "Clinical Procedure-service_comment",
        "Sales Invoice Payment-payment_reference",
        "Patient Appointment-follow_up",
        "Patient Encounter-old_hms_registration_no",
        "Prescription Dosage-section_break_3",
        "Radiology Examination-service_comment",
        "Lab Test-service_comment",
        "Healthcare Insurance Coverage Plan-nhif_scheme_id",
        "Prescription Dosage-dosage_form",
        "Prescription Dosage-column_break_1",
    )]]},
    {"doctype": "Property Setter", "filters": [["name", "in", (
        "Appointment Type-main-sort_field",
        "Appointment Type-main-sort_order",
        "Customer-main-search_fields",
        "Drug Prescription-comment-fetch_from",
        "Drug Prescription-comment-mandatory_depends_on",
        "Drug Prescription-dosage_form-fetch_if_empty",
        "Drug Prescription-dosage-fetch_if_empty",
        "Drug Prescription-period-fetch_if_empty",
        "Healthcare Insurance Subscription-country-hidden",
        "Healthcare Insurance Subscription-customer-hidden",
        "Healthcare Insurance Subscription-gender-read_only",
        "Healthcare Insurance Subscription-insurance_company_customer-hidden",
        "Healthcare Insurance Subscription-insurance_company_name-read_only",
        "Healthcare Insurance Subscription-main-search_fields",
        "Healthcare Insurance Subscription-patient_name-read_only",
        "Healthcare Practitioner-main-search_fields",
        "Healthcare Practitioner-practitioner_name-in_global_search",
        "Healthcare Service Insurance Coverage-end_date-Allow on Submit",
        "Healthcare Service Insurance Coverage-is_active-allow_on_submit",
        "Inpatient Record-company-read_only",
        "Inpatient Record-diagnosis-hidden",
        "Inpatient Record-diet_recommendation_section-hidden",
        "Inpatient Record-diet_recommendation_section-collapsible",
        "Inpatient Record-drug_prescription-label",
        "Inpatient Record-drug_prescription-permlevel",
        "Inpatient Record-encounter_details_section-collapsible",
        "Inpatient Record-investigations_section-collapsible",
        "Inpatient Record-investigations_section-collapsible_depends_on",
        "Inpatient Record-investigations_section-label",
        "Inpatient Record-investigations_section-hidden",
        "Inpatient Record-lab_test_prescription-label",
        "Inpatient Record-medication_section-collapsible",
        "Inpatient Record-medication_section-collapsible_depends_on",
        "Inpatient Record-medication_section-label",
        "Inpatient Record-medication_section-hidden",
        "Inpatient Record-procedure_prescription-label",
        "Inpatient Record-procedures_section-collapsible",
        "Inpatient Record-procedures_section-collapsible_depends_on",
        "Inpatient Record-procedures_section-label",
        "Inpatient Record-procedures_section-hidden",
        "Inpatient Record-radiology_orders_section-collapsible",
        "Inpatient Record-radiology_orders_section-collapsible_depends_on",
        "Inpatient Record-radiology_orders_section-hidden",
        "Inpatient Record-rehabilitation_section-collapsible",
        "Inpatient Record-rehabilitation_section-collapsible_depends_on",
        "Inpatient Record-rehabilitation_section-hidden",
        "Item-customer_details-collapsible",
        "Item-customer_details-collapsible_depends_on",
        "Lab Prescription-lab_test_comment-mandatory_depends_on",
        "Lab Test-insurance_section-hidden",
        "Medication-main-search_fields",
        "Patient Appointment-duration-read_only",
        "Patient Appointment-main-image_field",
        "Patient Appointment-paid_amount-read_only",
        "Patient Appointment-radiology_examination_template-depends_on",
        "Patient Appointment-section_break_19-hidden",
        "Patient Appointment-service_unit-read_only",
        "Patient Encounter-appointment_type-read_only_depends_on",
        "Patient Encounter-codification-collapsible",
        "Patient Encounter-codification-hidden",
        "Patient Encounter-company-read_only",
        "Patient Encounter-diagnosis_in_print-hidden",
        "Patient Encounter-diagnosis-hidden",
        "Patient Encounter-diet_recommendation_section-collapsible",
        "Patient Encounter-encounter_comment-hidden",
        "Patient Encounter-insurance_section-collapsible",
        "Patient Encounter-main-image_field",
        "Patient Encounter-physical_examination-hidden",
        "Patient Encounter-radiology_procedures_section-collapsible",
        "Patient Encounter-radiology_procedures_section-collapsible_depends_on",
        "Patient Encounter-rehabilitation_section-collapsible",
        "Patient Encounter-rehabilitation_section-collapsible_depends_on",
        "Patient Encounter-sb_drug_prescription-collapsible_depends_on",
        "Patient Encounter-sb_procedures-collapsible",
        "Patient Encounter-sb_procedures-collapsible_depends_on",
        "Patient Encounter-sb_source-collapsible",
        "Patient Encounter-sb_symptoms-hidden",
        "Patient Encounter-sb_test_prescription-collapsible",
        "Patient Encounter-sb_test_prescription-collapsible_depends_on",
        "Patient Encounter-section_break_3-collapsible",
        "Patient Encounter-sort_field",
        "Patient Encounter-sort_order",
        "Patient Encounter-source-read_only_depends_on",
        "Patient Encounter-symptoms_in_print-hidden",
        "Patient-allergy_medical_and_surgical_history-permlevel",
        "Patient-default_currency-read_only",
        "Patient-default_price_list-hidden",
        "Patient-invite_user-default",
        "Patient-main-quick_entry",
        "Patient-more_info-collapsible_depends_on",
        "Patient-patient_details-hidden",
        "Patient-personal_and_social_history-permlevel",
        "Patient-risk_factors-permlevel",
        "Patient-territory-hidden",
        "Patient-triage-hidden",
        "Procedure Prescription-comments-mandatory_depends_on",
        "Radiology Examination Template-main-quick_entry",
        "Radiology Examination-appointment-hidden",
        "Radiology Examination-insurance_section-hidden",
        "Radiology Examination-tc_name-fetch_from",
        "Radiology Examination-tc_name-hidden",
        "Radiology Examination-terms-hidden",
        "Radiology Procedure Prescription-radiology_test_comment-mandatory_depends_on",
        "Vital Signs-height-hidden",
        "Vital Signs-main-image_field",
        "Patient Encounter-appointment_type-read_only",
        "Patient-mobile-reqd",
        "Patient-search_fields",
        "Practitioner Availability-availability-in_list_view",
        "Practitioner Availability-practitioner-in_list_view",
        "Practitioner Availability-to_date-in_list_view",
        "Patient-show_preview_popup",
        "Vital Signs-reflexes-hidden",
        "Vital Signs-abdomen-hidden",
        "Vital Signs-tongue-hidden",
        "Patient Encounter-diet_recommendation_section-collapsible_depends_on",
        "Patient Encounter-sb_drug_prescription-collapsible",
        "Patient-surgical_history-in_preview",
        "Patient-medical_history-in_preview",
        "Patient-medication-in_preview",
        "Patient-allergies-in_preview",
        "Patient-patient_name-in_preview",
        "Patient-medication-read_only",
        "Patient-medical_history-read_only",
        "Patient-surgical_history-permlevel",
        "Patient-medical_history-permlevel",
        "Patient-allergies-permlevel",
        "Descriptive Test Result-result_value-hidden",
        "Descriptive Test Result-lab_test_particulars-fetch_from",
        "Descriptive Test Result-result_value-in_list_view",
        "Descriptive Test Result-result_value-read_only",
        "Descriptive Test Result-result_value-fetch_from",
        "Patient-medical_history-hidden",
        "Patient-medication-hidden",
        "Patient Encounter-medical_department-hidden",
        "Patient Encounter-company-hidden",
        "Patient Encounter-patient_sex-hidden",
        "Patient Encounter-triage-hidden",
        "Patient Encounter-patient_name-hidden",
        "Patient Encounter-appointment-hidden",
        "Drug Prescription-comment-fetch_if_empty",
        "Radiology Examination-healthcare_practitioner_name",
        "Patient Encounter-diagnosis-permlevel",
        "Patient Encounter-symptoms-permlevel",
        "Patient Encounter-sb_symptoms-permlevel",
        "Patient Encounter-inpatient_status-permlevel",
        "Patient Encounter-inpatient_record-permlevel",
        "Patient Encounter-triage-permlevel",
        "Patient Encounter-patient_vitals-permlevel",
        "Patient Encounter-patient_vitals_summary_section-permlevel",
        "Lab Test-lab_test_name-in_list_view",
        "Lab Test-patient_name-in_list_view",
        "Patient Encounter-section_break_33-permlevel",
        "Patient Encounter-patient-default",
        "Patient Encounter-appointment_type-default",
        "Patient Encounter-appointment_type-mandatory_depends_on",
        "Vital Signs-patient-read_only_depends_on",
        "Delivery Note Item-rate-permlevel",
        "Delivery Note Item-item_name-permlevel",
        "Delivery Note Item-item_code-permlevel",
        "Normal Test Result-result_value-depends_on",
        "Practitioner Availability-main-allow_rename",
        "Sales Invoice Item-item_tax_template-fetch_from",
        "Practitioner Availability-practitioner-in_standard_filter",
        "Practitioner Availability-main-allow_copy",
        "Inpatient Occupancy-service_unit-read_only",
        "Inpatient Occupancy-check_in-read_only",
        "Inpatient Occupancy-left-read_only",
        "Inpatient Occupancy-check_out-read_only",
        "Inpatient Record-inpatient_occupancies-read_only",
        "Inpatient Record-insurance_subscription-fetch_if_empty",
        "Inpatient Record-insurance_subscription-fetch_from",
        "Inpatient Occupancy-check_out-in_list_view",
        "Inpatient Occupancy-left-in_list_view",
        "Inpatient Record-references-collapsible",
        "Radiology Examination-insurance_section-read_only",
        "Radiology Examination-patient_name-fetch_from",
        "Patient-medication-permlevel",
        "Patient Encounter-naming_series-hidden",
        "Patient Encounter-insurance_subscription-read_only",
        "Patient Encounter-encounter_time-in_list_view",
        "Normal Test Result-normal_range-columns",
        "Healthcare Service Order-origin_section-hidden",
        "Exercise-difficulty_level-fetch_if_empty",
        "Drug Prescription-drug_name-in_list_view",
        "Delivery Note-items-permlevel",
        "Drug Prescription-period-reqd",
        "Drug Prescription-dosage-reqd",
        "Descriptive Test Result-lab_test_particulars-columns",
        "Patient Appointment-appointment_type-default",
        "Patient-customer_group-default",
        "Clinical Procedure-insurance_section-hidden",
        "Clinical Procedure-sb_source-hidden",
        "Clinical Procedure-patient_name-fetch_if_empty",
        "Clinical Procedure-patient_name-fetch_from",
        "Clinical Procedure-practitioner_name-in_list_view",
        "Clinical Procedure-patient_name-in_list_view",
        "Clinical Procedure-procedure_template-in_list_view",
        "Radiology Examination-appointment-in_list_view",
        "Radiology Examination-radiology_examination_template-in_list_view",
        "Radiology Examination-patient_name-in_list_view",
        "Patient-allergy_medical_and_surgical_history-collapsible",
        "Patient-sb_relation-hidden",
        "Patient-personal_and_social_history-collapsible",
        "Vital Signs-patient-in_list_view",
        "Sales Invoice-subscription_section-read_only",
        "Sales Invoice-section_break2-hidden",
        "Sales Invoice-sales_team_section_break-hidden",
        "Sales Invoice-debit_to-permlevel",
        "Sales Invoice-column_break4-permlevel",
        "Sales Invoice-loyalty_points_redemption-hidden",
        "Sales Invoice-time_sheet_list-hidden",
        "Sales Invoice-set_warehouse-permlevel",
        "Sales Invoice-customer_po_details-permlevel",
        "Sales Invoice-accounting_dimensions_section-hidden",
        "Sales Invoice-set_posting_time-permlevel",
        "Sales Invoice-is_return-permlevel",
        "Radiology Examination-patient_name-in_standard_filter",
        "Descriptive Test Result-result_value-fetch_if_empty",
        "Patient-risk_factors-collapsible",
        "Sales Invoice-is_pos-default",
        "Drug Prescription-drug_prescription_created-read_only",
        "Drug Prescription-drug_prescription_created-label",
        "Sales Invoice Item-rate-permlevel",
        "Sales Invoice Item-qty-permlevel",
        "Sales Invoice Item-item_code-permlevel",
        "Sales Invoice-section_break2-hidden",
        "Sales Invoice-sales_team_section_break-hidden",
        "Sales Invoice-debit_to-permlevel",
        "Sales Invoice-column_break4-permlevel",
        "Patient Encounter-practitioner-default",
        "Patient Encounter-practitioner-mandatory_depends_on",
        "Patient Encounter-appointment_type-mandatory_depends_on",
        "Patient Encounter-appointment_type-hidden",
        "Patient Appointment-main-default_print_format",
        "Patient Encounter-encounter_time-read_only",
        "Patient Encounter-encounter_date-read_only",
        "Inpatient Consultancy-confirmed-permlevel"
        "Radiology Examination-practitioner-in_standard_filter",
        "Healthcare Practitioner-main-search_fields",
        "Chronic Medications-period-fetch_if_empty",
        "Chronic Medications-dosage-fetch_if_empty",
    )]]},
    {"doctype": "Accounting Dimension", "filters": [["name", "in", (
        "Healthcare Practitioner",
        "Healthcare Service Unit",
    )]]},
]

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
}
# csf_tz.nhif.api.patient_appointment
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
inpatient_record_list_js = {"doctype": "nhif/api/inpatient_record_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
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
            "hms_tz.nhif.api.patient_appointment.make_vital",
        ]
    },
    "Vital Signs": {
        "on_submit": "hms_tz.nhif.api.patient_appointment.make_encounter",
    },
    "Patient": {
        "validate": "hms_tz.nhif.api.patient.validate",
    },
    "Healthcare Insurance Claim": {
        "before_insert": [
            "hms_tz.nhif.api.insurance_claim.set_patient_encounter",
            "hms_tz.nhif.api.insurance_claim.set_price",
        ]
    },
    "Patient Encounter": {
        "after_insert": "hms_tz.nhif.api.patient_encounter.after_insert",
        "validate": "hms_tz.nhif.api.patient_encounter.validate",
        "on_trash": "hms_tz.nhif.api.patient_encounter.on_trash",
        "on_submit": "hms_tz.nhif.api.patient_encounter.on_submit",
        "before_submit": "hms_tz.nhif.api.patient_encounter.on_submit",
        "on_update_after_submit": "hms_tz.nhif.api.patient_encounter.on_update_after_submit",
    },
    "Healthcare Service Order": {
        "before_insert": "hms_tz.nhif.api.service_order.set_missing_values",
        "on_update": "hms_tz.nhif.api.service_order.after_save",
    },
    "Sales Invoice": {
        "before_submit": "hms_tz.nhif.api.sales_invoice.before_submit",
        "on_submit": "hms_tz.nhif.api.sales_invoice.create_healthcare_docs",
        "validate": "hms_tz.nhif.api.sales_invoice.validate",
    },
    "Healthcare Insurance Subscription": {
        "on_submit": "hms_tz.nhif.api.insurance_subscription.on_submit",
        "before_cancel": "hms_tz.nhif.api.insurance_subscription.on_cancel",
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
    },
    "Inpatient Record": {
        "validate": "hms_tz.nhif.api.inpatient_record.validate",
    },
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
    "cron": {
        "*/5 * * * *": [
            # "hms_tz.nhif.api.inpatient_record.daily_update_inpatient_occupancies",
            "hms_tz.nhif.api.inpatient_record.daily_update_inpatient_occupancies",
        ]
    },
    "daily": [
        "hms_tz.nhif.api.service_order.real_auto_submit"
    ],
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
