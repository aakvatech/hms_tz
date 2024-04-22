import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    frappe.reload_doc("nhif", "doctype", "original_delivery_note_item", force=True)
    frappe.db.commit()

    fields = {
        "Appointment Type": [
            dict(
                fieldname="source",
                label="Source",
                fieldtype="Data",
                insert_after="visit_type_id",
                translatable=1
            ),
            dict(
                fieldname="visit_type_id",
                label="Visit Type ID",
                fieldtype="Select",
                insert_after="medical_code",
                translatable=1,
                options="1-Normal Visit\
                        2-Emergency\
                        3-Referral\
                        4-Follow up Visit\
                        5-Investigation Only\
                        6-Occupational Visit\
                        7-Medicine Only"
            ),
        ],
        "Clinical Procedure Template": [
            dict(
                fieldname="healthcare_notes_template",
                label="Healthcare Notes Template",
                fieldtype="Link",
                insert_after="description",
                
                options="Healthcare Notes Template",
            ),
            dict(
                fieldname="healthcare_service_unit",
                label="Healthcare Service Unit",
                fieldtype="Link",
                insert_after="healthcare_service_unit_type",
                
                translatable=1,
                options="Healthcare Service Unit"
            ),
            dict(
                fieldname="is_not_completed",
                label="Is Not Completed",
                fieldtype="Check",
                insert_after="disabled",
                
                translatable=1,
            ),
            dict(
                fieldname="is_inpatient",
                label="Is Inpatient",
                fieldtype="Check",
                insert_after="is_not_completed",
                
                description="If ticked, this procedure will be provided to admitted patient only",
                translatable=1,
            ),
        ],
        "Codification Table": [
            dict(
                fieldname="mtuha",
                label="MTUHA",
                fieldtype="Link",
                insert_after="description",
                
                options="MTUHA"
            )
        ],
        "Delivery Note Item": [
            dict(
                fieldname="approval_number",
                label="Service Reference Number",
                fieldtype="Data",
                insert_after="is_restricted",
                
            ),
            dict(
                fieldtype='Select',
                label='Approval type',
                fieldname='approval_type',
                insert_after='approval_number',
                
                options='Local\nNHIF\nOther Insurance',
            ),
            dict(
                fieldtype='Column Break',
                fieldname='column_break_89',
                insert_after='approval_type',
                
            ),
            dict(
                fieldtype='Link',
                label='Department',
                fieldname='department',
                insert_after='healthcare_practitioner',
                
                options='Department',
            ),
            dict(
                fieldtype='Section Break',
                label='Healthcare',
                fieldname='healthcare',
                insert_after='reference_name',
                
            ),
            dict(
                fieldtype='Link',
                label='Healthcare Practitioner',
                fieldname='healthcare_practitioner',
                insert_after='healthcare_service_unit',
                
                options='Healthcare Practitioner',
            ),
            dict(
                fieldtype='Link',
                label='Healthcare Service Unit',
                fieldname='healthcare_service_unit',
                insert_after='accounting_dimensions_section',
                
                options='Healthcare Service Unit',
            ),
            dict(
                fieldtype='Check',
                label='Is Discount Applied',
                fieldname='hms_tz_is_discount_applied',
                insert_after='amount',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Out of Stock',
                fieldname='hms_tz_is_out_of_stock',
                insert_after='customer_item_code',
                
                bold=1,
            ),
            dict(
                fieldtype='Check',
                label='Is Restricted',
                fieldname='is_restricted',
                insert_after='original_stock_uom_qty',
                
            ),
            dict(
                fieldtype='Date',
                label='Last Date Prescribed',
                fieldname='last_date_prescribed',
                insert_after='column_break_89',
                
            ),
            dict(
                fieldtype='Float',
                label='Last Qty Prescribed',
                fieldname='last_qty_prescribed',
                insert_after='last_date_prescribed',
                
            ),
            dict(
                fieldtype='Data',
                label='Original Item',
                fieldname='original_item',
                insert_after='healthcare',
                
            ),
            dict(
                fieldtype='Float',
                label='Original Stock UOM Qty',
                fieldname='original_stock_uom_qty',
                insert_after='original_item',
                
            ),
            dict(
                fieldtype='Float',
                label='Recommended Qty',
                fieldname='recommended_qty',
                insert_after='last_qty_prescribed',
                
            ),
            dict(
                fieldtype='Link',
                label='Reference Doctype',
                fieldname='reference_doctype',
                insert_after='page_break',
                
                options='DocType',
            ),
            dict(
                fieldtype='Dynamic Link',
                label='Reference Name',
                fieldname='reference_name',
                insert_after='reference_doctype',
                
                options='reference_doctype',
            ),

        ],
        "Delivery Note": [
            dict(
                fieldtype='Data',
                label='Authorization Number',
                fieldname='authorization_number',
                insert_after='reference_name',
                
            ),
            dict(
                fieldtype='Column Break',
                fieldname='column_break_21',
                insert_after='department',
                
            ),
            dict(
                fieldtype='Data',
                label='Coverage Plan Name',
                fieldname='coverage_plan_name',
                insert_after='form_sales_invoice',
                
            ),
            dict(
                fieldtype='Link',
                label='Department',
                fieldname='department',
                insert_after='sales_team',
                
                options='Department',
            ),
            dict(
                fieldtype='Link',
                label='Form Sales Invoice',
                fieldname='form_sales_invoice',
                insert_after='patient_name',
                
                options='Sales Invoice',
            ),
            dict(
                fieldtype='Link',
                label='Healthcare Practitioner',
                fieldname='healthcare_practitioner',
                insert_after='healthcare_service_unit',
                
                options='Healthcare Practitioner',
                read_only=1,
            ),
            dict(
                fieldtype='Check',
                label='All Items Out of Stock',
                fieldname='hms_tz_all_items_out_of_stock',
                
                insert_after='authorization_number',
                hidden=1,
                read_only=1,
            ),
            dict(
                fieldtype='Data',
                label='Appointment Number',
                fieldname='hms_tz_appointment_no',
                insert_after='coverage_plan_name',
                
                fetch_from="reference_name.appointment",
                fetch_if_empty=1,
                read_only=1,
            ),
            dict(
                fieldtype='Small Text',
                label='Comment',
                fieldname='hms_tz_comment',
                insert_after='set_target_warehouse',
                
            ),
            dict(
                fieldtype='Button',
                label='LRPMT Returns',
                fieldname='hms_tz_lrpmt_returns',
                insert_after='hms_tz_comment',
                
            ),
            dict(
                fieldtype='Button',
                label='Medicatiion Change Request',
                fieldname='hms_tz_medicatiion_change_request',
                insert_after='hms_tz_lrpmt_returns',
                
            ),
            dict(
                fieldtype='Button',
                label='Medicatiion Change Request',
                fieldname='hms_tz_medicatiion_change_request',
                insert_after='hms_tz_lrpmt_returns',
                
            ),
            dict(
                fieldtype='Table',
                label='Original Items',
                fieldname='hms_tz_original_items',
                insert_after='original_prescription',
                
                options='Original Delivery Note Item',
                read_only=1,
            ),
            dict(
                fieldtype='Data',
                label='Phone Number',
                fieldname='hms_tz_phone_no',
                insert_after='patient_name',
                
                read_only=1,
            ),
            dict(
                fieldtype='Data',
                label='Medical Department',
                fieldname='medical_department',
                insert_after='customer_name',
                
            ),
            dict(
                fieldtype='Section Break',
                label='Medical References',
                fieldname='medical_references',
                insert_after='authorization_number',
                
            ),
            dict(
                fieldtype='Section Break',
                label='Original Prescription',
                fieldname='original_prescription',
                insert_after='items',
                
            ),
            dict(
                fieldtype='Data',
                label='Patient',
                fieldname='patient',
                insert_after='vehicle',
                
            ),
            dict(
                fieldtype='Data',
                label='Patient Name',
                fieldname='patient_name',
                insert_after='patient',
                
            ),
            dict(
                fieldtype='Link',
                label='Reference Doctype',
                fieldname='reference_doctype',
                insert_after='return_against',
                
                options='DocType',
            ),
            dict(
                fieldtype='Dynamic Link',
                label='Reference Name',
                fieldname='reference_name',
                insert_after='reference_doctype',
                
                options='reference_doctype',
            ),
            dict(
                fieldtype='Link',
                label='Vehicle',
                fieldname='vehicle',
                insert_after='healthcare_practitioner',
                
                options='Vehicle',
                hidden=1,
            ),
            dict(
                fieldtype='Link',
                label='Workflow State',
                fieldname='workflow_state',
                
                options='Workflow State',
            ),
        ],
        "Descriptive Test Template": [
            dict(
                fieldtype='Link',
                label='Result Component',
                fieldname='result_component',
                insert_after='particulars',
                
                options='Result Component',
            )
        ],
        "Diet Recommendation": [
            dict(
                fieldtype='Select',
                label='Medical Code',
                fieldname='medical_code',
                insert_after='diet_plan',
                
            )
        ],
        "Drug Prescription": [
            dict(
                fieldtype='Float',
                label='Amount',
                fieldname='amount',
                insert_after='is_restricted',
                
            ),
            dict(
                fieldtype='Check',
                label='Cancelled',
                fieldname='cancelled',
                insert_after='reference_journal_entry',
                
            ),
            dict(
                fieldtype='Column Break',
                fieldname='column_break_34',
                insert_after='delivered_quantity',
                
            ),
            dict(
                fieldtype='Float',
                label='Delivered Quantity',
                fieldname='delivered_quantity',
                insert_after='drug_prescription_created',
                
            ),
            dict(
                fieldtype='Data',
                label='Department HSU',
                fieldname='department_hsu',
                insert_after='dn_detail',
                
            ),
            dict(
                fieldtype='Data',
                label='dn detail',
                fieldname='dn_detail',
                insert_after='delivered_quantity',
                
            ),
            dict(
                fieldtype='Link',
                label='Healthcare Service Unit',
                fieldname='healthcare_service_unit',
                insert_after='dosage_form',
                
                options='Healthcare Service Unit',
            ),
            dict(
                fieldtype='Check',
                label='Is Discount Applied',
                fieldname='hms_tz_is_discount_applied',
                insert_after='hms_tz_is_discount_percent',
                
            ),
            dict(
                fieldtype='Percent',
                label='Discount (%) on Price',
                fieldname='hms_tz_is_discount_percent',
                insert_after='update_schedule',
                
            ),
            dict(
                fieldtype='Check',
                label='Invoiced',
                fieldname='invoiced',
                insert_after='cancelled',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Cancelled',
                fieldname='is_cancelled',
                insert_after='reference_journal_entry',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Not Available Inhouse',
                fieldname='is_not_available_inhouse',
                insert_after='prescribe',
                
                allow_on_submit=1,
                read_only=1,
                bold=1,
            ),
            dict(
                fieldtype='Check',
                label='Is Out of Stock',
                fieldname='hms_tz_is_out_of_stock',
                insert_after='is_not_available_inhouse',
                
                allow_on_submit=1,
                read_only=1,
                bold=1,
            ),
            dict(
                fieldtype='Check',
                label='Is Restricted',
                fieldname='is_restricted',
                insert_after='healthcare_service_unit',
                
            ),
            dict(
                fieldtype='Select',
                label='Medical Code',
                fieldname='medical_code',
                insert_after='drug_code',
                
            ),
            dict(
                fieldtype='Check',
                label='NHIF 2C Form',
                fieldname='nhif_2c_form',
                insert_after='prescribe',
                
            ),
            dict(
                fieldtype='Check',
                label='Override Healthcare Insurance Subscription',
                fieldname='override_subscription',
                insert_after='medical_code',
                
            ),
            dict(
                fieldtype='Check',
                label='Prescribe',
                fieldname='prescribe',
                insert_after='override_subscription',
                
            ),
            dict(
                fieldtype='Int',
                label='Quantity Returned',
                fieldname='quantity_returned',
                
            ),
            dict(
                fieldtype='Data',
                label='Reference Journal Entry',
                fieldname='reference_journal_entry',
                insert_after='sales_invoice_number',
                
            ),
            dict(
                fieldtype='Data',
                label='Sales Invoice Number',
                fieldname='sales_invoice_number',
                insert_after='column_break_34',
                
            ),
        ],
        "Healthcare Insurance Company": [
            dict(
                fieldtype='Link',
                label='Default Price List',
                fieldname='default_price_list',
                insert_after='customer',
                
                options='Price List',
            ),
            dict(
                fieldtype='Check',
                label='Disabled',
                fieldname='disabled',
                insert_after='default_price_list',
                
                bold=1,
            ),
            dict(
                fieldtype='Data',
                label='Facility Code',
                fieldname='facility_code',
                insert_after='insurance_company_name',
                
            ),
            dict(
                fieldtype='Check',
                label='Has Price Discount',
                fieldname='hms_tz_has_price_discount',
                insert_after='disabled',
                
            ),
            dict(
                fieldtype='Percent',
                label='Price Discount(%)',
                fieldname='hms_tz_price_discount',
                insert_after='hms_tz_has_price_discount',
                
                depends_on="eval: doc.hms_tz_has_price_discount == 1",
                mandatory_depends_on="eval: doc.hms_tz_has_price_discount == 1",
                bold=1
            ),
            
        ],
        "Healthcare Insurance Coverage Plan": [
            dict(
                fieldtype='Data',
                label='Code for NHIF Excluded Services',
                fieldname='code_for_nhif_excluded_services',
                insert_after='daily_limit',
                
            ),
            dict(
                fieldtype='Currency',
                label='Default Daily Limit',
                fieldname='daily_limit',
                insert_after='insurance_company_name',
                
            ),
            dict(
                fieldtype='Data',
                label='NHIF Scheme ID',
                fieldname='nhif_scheme_id',
                insert_after='secondary_price_list',
                
            ),
            dict(
                fieldtype='Link',
                label='Secondary Price List',
                fieldname='secondary_price_list',
                insert_after='price_list',
                
                options='Price List',
            ),
        ],
        "Healthcare Insurance Subscription": [
            dict(
                fieldtype='Link',
                label='Company',
                fieldname='company',
                insert_after='coverage_plan_card_number',
                
                options='Company',
            ),
            dict(
                fieldtype='Data',
                label='Coverage Plan Card Number',
                fieldname='coverage_plan_card_number',
                insert_after='coverage_plan_name',
                
            ),
            dict(
                fieldtype='Data',
                label='Coverage Plan Name',
                fieldname='coverage_plan_name',
                insert_after='healthcare_insurance_coverage_plan',
                
            ),
            dict(
                fieldtype='Currency',
                label='Daily Limit',
                fieldname='daily_limit',
                insert_after='insurance_company_customer',
                
            ),
            dict(
                fieldtype='Section Break',
                label='Product and Scheme Details',
                fieldname='hms_tz_scheme_section_break',
                insert_after='coverage_plan_card_number',
                
            ),
            dict(
                fieldtype='Data',
                label='Product Code',
                fieldname='hms_tz_product_code',
                insert_after='hms_tz_scheme_section_break',
                
            ),
            dict(
                fieldname="hms_tz_product_name",
                label="Product Name",
                fieldtype="Data",
                insert_after="hms_tz_product_code",
                
            ),
            dict(
                fieldtype='Column Break',
                label="",
                fieldname='hms_tz_scheme_column_break',
                insert_after='hms_tz_product_name',
                
            ),
            dict(
                fieldname="hms_tz_scheme_id",
                label="SchemeId",
                fieldtype="Data",
                insert_after="hms_tz_scheme_column_break",
                
            ),
            dict(
                fieldtype='Data',
                label='Scheme Name',
                fieldname='hms_tz_scheme_name',
                insert_after='hms_tz_scheme_id',
                
            ),
        ],
        "Healthcare Practitioner": [
            dict(
                fieldtype='Data',
                label='Abbreviation',
                fieldname='abbreviation',
                insert_after='practitioner_name',
                
            ),
            dict(
                fieldtype='Check',
                label='Bypass Vitals',
                fieldname='bypass_vitals',
                insert_after='nhif_physician_qualification',
                
            ),
            dict(
                fieldtype='Link',
                label='Default Medication Healthcare Service Unit',
                fieldname='default_medication_healthcare_service_unit',
                insert_after='default_values',
                
                options='Healthcare Service Unit',
            ),
            dict(
                fieldtype='Section Break',
                label='Default Values',
                fieldname='default_values',
                insert_after='hospital',
                
            ),
            dict(
                fieldtype='Signature',
                label='Doctors Signature',
                fieldname='doctors_signature',
                insert_after='bypass_vitals',
                
            ),
            dict(
                fieldtype='Link',
                label='NHIF Physician Qualification',
                fieldname='nhif_physician_qualification',
                insert_after='tz_mct_code',
                
                options='NHIF Physician Qualification',
            ),
            dict(
                fieldtype='Data',
                label='Title and Qualification',
                fieldname='title_and_qualification',
                insert_after='supplier',
                
            ),
            dict(
                fieldtype='Data',
                label='TZ MCT Code',
                fieldname='tz_mct_code',
                insert_after='office_phone',
                
            ),
            dict(
                fieldname="hms_tz_company",
                fieldtype="Link",
                label="Company",
                insert_after="status",
                
                options="Company",
                reqd=1
            )
        ],
        "Healthcare Service Insurance Coverage": [
            dict(
                fieldtype='Check',
                label='Is Auto Generated',
                fieldname='is_auto_generated',
                insert_after='end_date',
                
            ),
            dict(
                fieldtype='Link',
                label='Item',
                fieldname='item',
                insert_after='healthcare_service_template',
                
                options='Item',
            ),
            dict(
                fieldtype='Duration',
                label='Maximum Claim Duration',
                fieldname='maximum_claim_duration',
                insert_after='maximum_number_of_claims',
                
            ),
        ],
        "Healthcare Service Unit Type": [
            # dict(
            #     fieldtype='Check',
            #     label='Disabled',
            #     fieldname='disabled',
            #     insert_after='is_group',
            #     
            # ),
            dict(
                fieldtype='Check',
                label='Is Consultancy Chargeable',
                fieldname='is_consultancy_chargeable',
                insert_after='occupancy_status',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Service Chargeable',
                fieldname='is_service_chargeable',
                insert_after='is_consultancy_chargeable',
                
            ),
        ],
        "Inpatient Consultancy": [
            dict(
                fieldtype='Link',
                label='Encounter',
                fieldname='encounter',
                insert_after='delivery_note',
                
                options='Patient Encounter',
            ),
            dict(
                fieldtype='Check',
                label='Invoiced',
                fieldname='hms_tz_invoiced',
                insert_after='encounter',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Discount Applied',
                fieldname='hms_tz_is_discount_applied',
                insert_after='rate',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Confirmed',
                fieldname='is_confirmed',
                insert_after='hms_tz_invoiced',
                
            ),
        ],
        "Inpatient Occupancy": [
            dict(
                fieldtype='Currency',
                label='Amount',
                fieldname='amount',
                insert_after='check_out',
                
            ),
            dict(
                fieldtype='Button',
                label='Confirmed',
                fieldname='confirmed',
                insert_after='amount',
                
            ),
            dict(
                fieldtype='Link',
                label='Delivery Note',
                fieldname='delivery_note',
                insert_after='confirmed',
                
                options='Delivery Note',
            ),
            dict(
                fieldtype='Check',
                label='Is Discount Applied',
                fieldname='hms_tz_is_discount_applied',
                insert_after='amount',
                
            ),
            dict(
                fieldtype='Check',
                label='Is Confirmed',
                fieldname='is_confirmed',
                insert_after='invoiced',
                
            ),
        ],
        "Inpatient Record": [
            dict(
                fieldtype='Currency',
                label='Cash Limit',
                fieldname='cash_limit',
                insert_after='claim_status',
                
                fetch_if_empty=1
            ),
            dict(
                fieldtype='Column Break',
                fieldname='column_break_45',
                insert_after='duplicate',
                
            ),
            dict(
                fieldtype='Column Break',
                fieldname='column_break_92',
                insert_after='when_to_obtain_urgent_care',
                
            ),
            dict(
                fieldtype='Check',
                label='Duplicate',
                fieldname='duplicate',
                insert_after='inpatient_record_type',
                
            ),
            dict(
                fieldtype='Link',
                label='Duplicated From',
                fieldname='duplicated_from',
                insert_after='reference_inpatient_record',
                
                options='Inpatient Record',
            ),
            dict(
                fieldtype='Small Text',
                label='History',
                fieldname='history',
                insert_after='discharge_note',
                
            ),
            dict(
                fieldtype='Section Break',
                label='Inpatient Consultancies',
                fieldname='inpatient_consultancies',
                insert_after='btn_transfer',
                
            ),
            dict(
                fieldtype='Table',
                label='Inpatient Consultancy',
                fieldname='inpatient_consultancy',
                insert_after='inpatient_consultancies',
                
                options='Inpatient Consultancy',
            ),
            dict(
                fieldtype='Table',
                label='Inpatient Record Final Diagnosis',
                fieldname='inpatient_record_final_diagnosis',
                insert_after='section_break_57',
                
                options='Codification Table',
            ),
            dict(
                fieldtype='Table',
                label='Inpatient Record Preliminary Diagnosis',
                fieldname='inpatient_record_preliminary_diagnosis',
                insert_after='section_break_47',
                
                options='Codification Table',
            ),
            dict(
                fieldtype='Select',
                label='Inpatient Record Type',
                fieldname='inpatient_record_type',
                insert_after='reference',
                
                options='Initial\nOngoing\nFinal',
            ),
            dict(
                fieldtype='Data',
                label='Insurance Coverage Plan',
                fieldname='insurance_coverage_plan',
                insert_after='insurance_subscription',
                
            ),
            dict(
                fieldtype='Small Text',
                label='Medication',
                fieldname='medication',
                insert_after='history',
                
            ),
            dict(
                fieldtype='Small Text',
                label='On Examination',
                fieldname='on_examination',
                insert_after='column_break_92',
                
            ),
            dict(
                fieldtype='Link',
                label='Patient Appointment',
                fieldname='patient_appointment',
                insert_after='admission_encounter',
                
                options='Patient Appointment',
                fetch_from='admission_encounter.appointment',
            ),
            dict(
                fieldtype='HTML',
                label='Patient Vitals',
                fieldname='patient_vitals',
                insert_after='patient_vitals_summary',
                
            ),
            dict(
                fieldtype='Section Break',
                label='Patient Vitals Summary',
                fieldname='patient_vitals_summary',
                
            ),
            dict(
                fieldtype='Data',
                label='Practitioner Name',
                fieldname='practitioner_name',
                insert_after='admission_practitioner',
                
                fetch_from='practitioner.practitioner_name',
            ),
            dict(
                fieldtype='Table',
                label='Previous Clinical Procedures',
                fieldname='previous_clinical_procedures',
                insert_after='procedure_prescription',
                
                options='Previous Procedure Prescription',
            ),
            {
                'fieldtype': 'Table',
                'label': 'Previous Diet Recommendation',
                'fieldname': 'previous_diet_recommendation',
                'insert_after': 'diet_recommendation',
                
                'options': 'Previous Diet Recommendation',
                'read_only': 1,
            },
            {
                'fieldtype': 'Table',
                'label': 'Previous Items',
                'fieldname': 'previous_drug_prescription',
                'insert_after': 'drug_prescription',
                
                'options': 'Previous Drug Prescription',
                'read_only': 1,
            },
            {
                'fieldtype': 'Table',
                'label': 'Previous Lab Tests',
                'fieldname': 'previous_lab_tests',
                'insert_after': 'lab_test_prescription',
                
                'options': 'Previous Lab Prescription',
                'read_only': 1,
            },
            {
                'fieldtype': 'Table',
                'label': 'Previous Radiology Procedure',
                'fieldname': 'previous_radiology_procedure',
                'insert_after': 'radiology_procedure_prescription',
                'options': 'Previous Radiology Procedure Prescription',
                
            },
            {
                'fieldtype': 'Table',
                'label': 'Previous Therapies',
                'fieldname': 'previous_therapy_plan_detail',
                'insert_after': 'therapies',
                'options': 'Previous Therapy Plan Detail',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Price List',
                'fieldname': 'price_list',
                'insert_after': 'expected_discharge',
                'options': 'Price List',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Primary Practitioner Name',
                'fieldname': 'primary_practitioner_name',
                'insert_after': 'primary_practitioner',
                'fetch_from': 'primary_practitioner.practitioner_name',
                
            },
            {
                'fieldtype': 'Section Break',
                'label': 'Reference',
                'fieldname': 'reference',
                'insert_after': 'diagnosis',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Reference Inpatient Record',
                'fieldname': 'reference_inpatient_record',
                'insert_after': 'column_break_45',
                'options': 'Inpatient Record',
                
            },
            {
                'fieldtype': 'Button',
                'label': 'Reset Admission Status To Admission Scheduled',
                'fieldname': 'reset_admission_status_to_admission_scheduled',
                'insert_after': 'status',
                
            },
            {
                'fieldtype': 'Text',
                'label': 'Review',
                'fieldname': 'review',
                'insert_after': 'surgical_procedure',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Secondary Practitioner Name',
                'fieldname': 'secondary_practitioner_name',
                'insert_after': 'secondary_practitioner',
                'fetch_from': 'secondary_practitioner.practitioner_name',
                
            },
            {
                'fieldtype': 'Section Break',
                'label': "",
                'fieldname': 'section_break_47',
                'insert_after': 'duplicated_from',
                
            },
            {
                'fieldtype': 'Section Break',
                'label': "",
                'fieldname': 'section_break_57',
                'insert_after': 'previous_radiology_procedure',
                
            },
            {
                'fieldtype': 'Small Text',
                'label': 'Surgical procedure',
                'fieldname': 'surgical_procedure',
                'insert_after': 'on_examination',
                
            },
            {
                'fieldtype': 'Small Text',
                'label': 'When to Obtain Urgent Care',
                'fieldname': 'when_to_obtain_urgent_care',
                'insert_after': 'medication',
                
            },
        ],
        "Item": [
            {
                'fieldtype': 'Data',
                'label': 'Healthcare Service Template',
                'fieldname': 'healthcare_service_template',
                'insert_after': 'hms_item_name',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'HMS Item Name',
                'fieldname': 'hms_item_name',
                'insert_after': 'item_name',
                
            },
        ],
        "Lab Prescription": [
            {
                'fieldtype': 'Float',
                'label': 'Amount',
                'fieldname': 'amount',
                'insert_after': 'lab_test_name',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Cancelled',
                'fieldname': 'cancelled',
                'insert_after': 'reference_journal_entry',
                
            },
            {
                'fieldtype': 'Column Break',
                'label': "",
                'fieldname': 'column_break_23',
                'insert_after': 'delivered_quantity',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'Delivered Quantity',
                'fieldname': 'delivered_quantity',
                'insert_after': 'section_break_21',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Discount Applied',
                'fieldname': 'hms_tz_is_discount_applied',
                'insert_after': 'amount',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Cancelled',
                'fieldname': 'is_cancelled',
                'insert_after': 'reference_journal_entry',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Not Available Inhouse',
                'fieldname': 'is_not_available_inhouse',
                'insert_after': 'prescribe',
                
            },
            {
                'fieldtype': 'Select',
                'label': 'Medical Code',
                'fieldname': 'medical_code',
                'insert_after': 'lab_test_code',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Override Healthcare Insurance Subscription',
                'fieldname': 'override_subscription',
                'insert_after': 'medical_code',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Prescribe',
                'fieldname': 'prescribe',
                'insert_after': 'override_subscription',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Reference Journal Entry',
                'fieldname': 'reference_journal_entry',
                'insert_after': 'sales_invoice_number',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Sales Invoice Number',
                'fieldname': 'sales_invoice_number',
                'insert_after': 'column_break_23',
                
            },
            {
                'fieldtype': 'Section Break',
                'label': '',
                'fieldname': 'section_break_21',
                'insert_after': 'note',
                
            },
        ],
        "Lab Test Template": [
            {
                'fieldtype': 'Float',
                'label': 'C Max Range',
                'fieldname': 'c_max_range',
                'insert_after': 'c_min_range',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'C Min Range',
                'fieldname': 'c_min_range',
                'insert_after': 'column_break_30',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'C Text',
                'fieldname': 'c_text',
                'insert_after': 'c_max_range',
                
            },
            {
                'fieldtype': 'Column Break',
                'fieldname': 'column_break_26',
                'insert_after': 'm_text',
                
            },
            {
                'fieldtype': 'Column Break',
                'fieldname': 'column_break_30',
                'insert_after': 'f_text',
                
            },
            {
                'fieldtype': 'Column Break',
                'fieldname': 'column_break_34',
                'insert_after': 'c_text',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'F Max Range',
                'fieldname': 'f_max_range',
                'insert_after': 'f_min_range',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'F Min Range',
                'fieldname': 'f_min_range',
                'insert_after': 'column_break_26',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'F Text',
                'fieldname': 'f_text',
                'insert_after': 'f_max_range',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Healthcare Service Unit',
                'fieldname': 'healthcare_service_unit',
                'insert_after': 'healthcare_service_unit_type',
                'options': 'Healthcare Service Unit',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'I Max Range',
                'fieldname': 'i_max_range',
                'insert_after': 'i_min_range',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'I Min Range',
                'fieldname': 'i_min_range',
                'insert_after': 'column_break_34',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'I Text',
                'fieldname': 'i_text',
                'insert_after': 'i_max_range',
                
            },
            {
                'fieldtype': 'Section Break',
                'label': 'Lab Routine Normals',
                'fieldname': 'lab_routine_normals',
                'insert_after': 'lab_test_normal_range',
                'depends_on': "eval:doc.lab_test_template_type == 'Single'",
                
            },
            {
                'fieldtype': 'Float',
                'label': 'M Max Range',
                'fieldname': 'm_max_range',
                'insert_after': 'm_min_range',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'M Min Range',
                'fieldname': 'm_min_range',
                'insert_after': 'lab_routine_normals',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'M Text',
                'fieldname': 'm_text',
                'insert_after': 'm_max_range',
            }
        ],
        "Lab Test": [
            {
                'fieldtype': 'Data',
                'label': 'Service Reference Number',
                'fieldname': 'approval_number',
                'insert_after': 'is_restricted',
                'depends_on': 'eval: doc.is_restricted',
                'mandatory_depends_on': 'eval: doc.is_restricted',
                
            },
            {
                'fieldtype': 'Select',
                'label': 'Approval Type',
                'fieldname': 'approval_type',
                'insert_after': 'approval_number',
                'options': 'Local\nNHIF\nOther Insurance',
                'depends_on': 'eval: doc.is_restricted',
                'mandatory_depends_on': 'eval: doc.is_restricted',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Ref Childname',
                'fieldname': 'hms_tz_ref_childname',
                'insert_after': 'ref_docname',
                'read_pnly': 1,
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Restricted',
                'fieldname': 'is_restricted',
                'insert_after': 'department',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Ref DocType',
                'fieldname': 'ref_doctype',
                'insert_after': 'prescription',
                'options': 'DocType',
                
            },
            {
                'fieldtype': 'Dynamic Link',
                'label': 'Ref DocName',
                'fieldname': 'ref_docname',
                'insert_after': 'ref_doctype',
                'options': 'ref_doctype',
                
            },
            {
                'fieldtype': 'Text',
                'label': 'Service Comment',
                'fieldname': 'service_comment',
                'insert_after': 'practitioner_name',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Title',
                'fieldname': 'title',
                'insert_after': 'naming_series',
                'default': '{patient_name} - {template}',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Workflow State',
                'fieldname': 'workflow_state',
                'insert_after': 'ref_docname',
                
            },
            {
                "fieldname":"hms_tz_insurance_coverage_plan",
                "fieldtype": "Data",
                "label": "Insurance Coverage Plan",
                "insert_after": "insurance_subscription",
                "fetch_from": "insurance_subscription.healthcare_insurance_coverage_plan",
                "fetch_if_empty": 1,
                "read_only": 1
            }
        ],
        "LRPMT Returns": [
            {
                'fieldtype': 'Section Break',
                'label': "",
                'fieldname': 'hms_tz_help_msg_section_break',
                'insert_after': "",
                'idx': 1,
                
            },
            {
                'fieldtype': 'HTML',
                'label': '',
                'fieldname': 'hms_tz_lrpmt_returns_help_msg',
                'insert_after': 'hms_tz_help_msg_section_break',
                'options': "<div class='alert alert-warning'>\
				    LRPMT Returns can be used to:<br>\
                        1. Cancel draft and submitted lab test, radiology examination and clinical procedure<br>\
                        2. Cancel non-created lab test, radiology examination and clinical procedure to remove them from itemized bill<br>\
                        3. Cancel non-created drug items to remove them from itemized bill<br>\
                        4. Cancel whole draft delivery note, even if one item of draft delivery note is selected<br>\
                        5. Return quantities of submitted delivery note\
			    </div>",
                
            },
            {
                'fieldtype': 'Section Break',
                'label': '',
                'fieldname': 'hms_tz_patient_info',
                'insert_after': 'hms_tz_lrpmt_returns_help_msg',
                
            }
        ],
        # The field (Comment) shifted to json of medication change request 2024-03-12
        # "Medication Change Request": [
        #     {
        #         'fieldtype': 'Small Text',
        #         'label': 'Comment',
        #         'fieldname': 'hms_tz_comment',
        #         'insert_after': 'appointment',
        #         'description': 'comment indicates an item that required to be changed',
        #         "read_only": 1,
        #     }
        # ],
        "Medication": [
            {
                'fieldtype': 'Table',
                'label': 'Company Options',
                'fieldname': 'company_options',
                'insert_after': 'column_break_6',
                'options': 'Healthcare Company Option',
                
            },
            {
                'fieldtype': 'Small Text',
                'label': 'Default Comments',
                'fieldname': 'default_comments',
                'insert_after': 'default_prescription_dosage',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Healthcare Service Unit',
                'fieldname': 'healthcare_service_unit',
                'insert_after': 'default_comments',
                'options': 'Healthcare Service Unit',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Strength Text',
                'fieldname': 'strength_text',
                'insert_after': 'disabled',
            }
        ],
        "NHIF Patient Claim": [
            {
                'fieldtype': 'Data',
                'label': 'hms_tz_appointment_string',
                'fieldname': 'hms_tz_appointment_string',
                'insert_after': 'naming_series',
                
            },
            {
                'fieldtype': 'Rating',
                'label': 'How Likely Would You Recommend Our Services To Others',
                'fieldname': 'how_likely_would_you_recommend_our_services_to_others',
                'insert_after': 'total_amount',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Internal Form Number',
                'fieldname': 'internal_form_number',
                'insert_after': 'allow_changes',
                
            },
            {
                'fieldtype': 'Select',
                'label': 'Unsubmittable Claim',
                'fieldname': 'unsubmittable_claim',
                'insert_after': 'internal_form_number',
                'options': '\nUnclaimable - Only Consultation\nUnclaimable - Zero Amount\nUnclaimable - Same Auth Number Submitted On The Same Day\nChecked and Ready to Send\nAuthorization Number Checked\nTo Delete (Same Auth No. Claim Already Merged)',
            }
        ],
        "Normal Test Result": [
            {
                'fieldtype': 'Data',
                'label': 'Detailed Normal Range',
                'fieldname': 'detailed_normal_range',
                'insert_after': 'conversion_factor',
                'columns': 2,
                
            },
            {
                'fieldtype': 'Float',
                'label': 'Max Normal',
                'fieldname': 'max_normal',
                'insert_after': 'min_normal',
                
            },
            {
                'fieldtype': 'Float',
                'label': 'Min Normal',
                'fieldname': 'min_normal',
                'insert_after': 'require_result_value',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Result Status',
                'fieldname': 'result_status',
                'insert_after': 'detailed_normal_range',
                'read_only': 1,
                'columns': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Text Normal',
                'fieldname': 'text_normal',
                'insert_after': 'max_normal',
                'read_only': 1,
                
            }
        ],
        "Original Delivery Note Item": [
            {
                'fieldtype': 'Check',
                'label': 'Is Discount Applied',
                'fieldname': 'hms_tz_is_discount_applied',
                'insert_after': 'amount',
                'description': 'Discount is applied only if the discount percent is defined on Healthcare Insurance Company',
                
            }
        ],
        "Patient Appointment": [
            {
                'fieldtype': 'Data',
                'label': 'Authorization Number',
                'fieldname': 'authorization_number',
                'insert_after': 'get_authorization_number',
                'depends_on': 'eval:doc.insurance_company && doc.practitioner',
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Coverage Plan Card Number',
                'fieldname': 'coverage_plan_card_number',
                'insert_after': 'coverage_plan_name',
                'fetch_from': 'insurance_subscription.coverage_plan_card_number',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Coverage Plan Name',
                'fieldname': 'coverage_plan_name',
                'insert_after': 'insurance_subscription',
                'fetch_from': 'insurance_subscription.coverage_plan_name',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Float',
                'label': 'Daily Limit',
                'fieldname': 'daily_limit',
                'insert_after': 'insurance_company_name',
                'depends_on': "eval:doc.insurance_company && doc.insurance_company!='NHIF';",
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Follow Up',
                'fieldname': 'follow_up',
                'insert_after': 'ref_patient_encounter',
                
            },
            {
                'fieldtype': 'Button',
                'label': 'Get Authorization Number',
                'fieldname': 'get_authorization_number',
                'insert_after': 'column_break_49',
                'depends_on': 'eval:doc.insurance_company && !doc.authorization_number && doc.practitioner',
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Healthcare Referrer Type',
                'fieldname': 'healthcare_referrer_type',
                'insert_after': 'referring_practitioner',
                'options': 'DocType',
                
                'hidden': 1,
            },
            {
                'fieldtype': 'Dynamic Link',
                'label': 'Healthcare Referrer',
                'fieldname': 'healthcare_referrer',
                'insert_after': 'healthcare_referrer_type',
                'options': 'healthcare_referrer_type',
                'read_only_depends_on': 'eval:doc.invoiced || doc.authorization_number;',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Discount Applied',
                'fieldname': 'hms_tz_is_discount_applied',
                'insert_after': 'paid_amount',
                'description': 'Discount is applied only if the discount percent is defined on Healthcare Insurance Company',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Insurance Company Name',
                'fieldname': 'insurance_company_name',
                'insert_after': 'insurance_company',
                'fetch_from': 'insurance_company.insurance_company_name',
                'read_only': 1,
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Mobile',
                'fieldname': 'mobile',
                'insert_after': 'patient_age',
                'options': 'Phone',
                'fetch_from': 'patient.mobile',
                'read_only': 1,
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Link',
                'label': 'NHIF Patient Claim',
                'fieldname': 'nhif_patient_claim',
                'insert_after': 'insurance_claim',
                'options': 'NHIF Patient Claim',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Old HMS Registration No.',
                'fieldname': 'old_hms_number',
                'insert_after': 'notes',
                'fetch_from': 'patient.old_hms_registration_no',
                
            },
            {
                'fieldtype': 'Attach Image',
                'label': 'Patient Image2',
                'fieldname': 'patient_image2',
                'insert_after': 'old_hms_number',
                'fetch_from': 'patient.image',
                'read_only': 1,
                'hidden': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Payment Reference',
                'fieldname': 'payment_reference',
                'insert_after': 'mode_of_payment',
                'depends_on': 'eval: doc.mode_of_payment && !doc.mode_of_payment.includes("Cash")',
                'mandatory_depends_on': 'eval: doc.mode_of_payment && !doc.mode_of_payment.includes("Cash")',
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Ref Patient Encounter',
                'fieldname': 'ref_patient_encounter',
                'insert_after': 'ref_vital_signs',
                'read_only': 1,
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Reference Vital Signs',
                'fieldname': 'ref_vital_signs',
                'insert_after': 'duration',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Link',
                'label': 'Reference Journal Entry',
                'fieldname': 'reference_journal_entry',
                'insert_after': 'send_vfd',
                'options': 'Journal Entry',
                'read_only': 1,
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Referral No',
                'fieldname': 'referral_no',
                'insert_after': 'healthcare_referrer',
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Small Text',
                'label': 'Remarks',
                'fieldname': 'remarks',
                'insert_after': 'referral_no',
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Button',
                'label': 'Send To VFD',
                'fieldname': 'send_vfd',
                'insert_after': 'ref_sales_invoice',
                'depends_on': 'ref_sales_invoice',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'SMS Sent',
                'fieldname': 'sms_sent',
                
                'insert_after': 'reminded',
            }
        ],
        "Patient Encounter Symptom": [
            {
                'fieldtype': 'Small Text',
                'label': 'Complaint Comments',
                'fieldname': 'complaint_comments',
                'insert_after': 'complaint_duration',
                'default': 'Onset: \nLocation: \nDuration: \nCharacterization: \nAlleviating and Aggravating factors: \nRadiation: \nTemporal factor: \nSeverity: \n',
                'in_list_view': 1,
                'translatable': 1,
                'description': '<hr>Onset: When did the CC begin?<br>\nLocation: Where is the CC located?<br>\nDuration: How long has the CC been going on for?<br>\nCharacterization: How does the patient describe the CC?<br>\nAlleviating and Aggravating factors: What makes the CC better? Worse?<br>\nRadiation: Does the CC move or stay in one location?<br>\nTemporal factor: Is the CC worse (or better) at a certain time of the day?<br>\nSeverity: Using a scale of 1 to 10, 1 being the least, 10 being the worst, how does the patient rate the CC?<br>\n',
                
            },
            {
                'fieldtype': 'Data',
                'label': 'Complaint Duration',
                'fieldname': 'complaint_duration',
                'insert_after': 'complaint',
                'in_list_view': 1,
                'translatable': 1,
                
            },
            {
                'fieldtype': 'Duration',
                'label': 'Compliant Duration',
                'fieldname': 'compliant_duration',
                'insert_after': 'complaint',
                'hidden': 1,
                
            },
            {
                'fieldtype': 'Link',
                'label': 'System',
                'fieldname': 'system',
                
            }
        ],
        "Patient Encounter": [
            {
                "fieldtype": "Data",
                "label": "Abbreviation",
                "fieldname": "abbr",
                "insert_after": "practitioner_name",
                "fetch_from": "practitioner.abbreviation",
                "read_only": 1,
                "hidden": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Blood Group",
                "fieldname": "blood_group",
                "insert_after": "image",
                "options": "\nA Positive\nA Negative\nAB Positive\nAB Negative\nB Positive\nB Negative\nO Positive\nO Negative",
                "fetch_from": "patient.blood_group",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Column Break",
                "label": "", "fieldname": "column_break_31",
                "insert_after": "duplicated",
                
            },
            {
                "fieldtype": "Button",
                "label": "Copy From Preliminary Diagnosis",
                "fieldname": "copy_from_preliminary_diagnosis",
                "insert_after": "section_break_52",
                
            },
            {
                "fieldtype": "Button",
                "label": "Create Sales Invoice",
                "fieldname": "create_sales_invoice",
                "insert_after": "encounter_mode_of_payment",
                "depends_on": "eval: !doc.sales_invoice && doc.encounter_category == \"Direct Cash\" && !!doc.__islocal",
                
            },
            {
                "fieldtype": "Float",
                "label": "Current Total",
                "fieldname": "current_total",
                "insert_after": "previous_total",
                "read_only": 1,
                "hidden": 1,
                "print_hide": 1,
                
            },
            {
                "fieldtype": "Float",
                "label": "Daily Limit",
                "fieldname": "daily_limit",
                "insert_after": "insurance_subscription",
                "fetch_from": "appointment.daily_limit",
                "depends_on": "eval:doc.insurance_company != \"NHIF\"",
                
            },
            {
                "fieldtype": "Link",
                "label": "Default Healthcare Service Unit",
                "fieldname": "default_healthcare_service_unit",
                "insert_after": "get_chronic_medications",
                "options": "Healthcare Service Unit",
                "fetch_from": "practitioner.default_medication_healthcare_service_unit",
                
            },
            {
                "fieldtype": "Check",
                "label": "Duplicated",
                "fieldname": "duplicated",
                "insert_after": "amended_from",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Small Text",
                "label": "ED Addressed To",
                "fieldname": "ed_addressed_to",
                "insert_after": "ed_reason_for_absence",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Int",
                "label": "ED No of Days",
                "fieldname": "ed_no_of_days",
                "insert_after": "ed_addressed_to",
                
            },
            {
                "fieldtype": "Data",
                "label": "ED Reason for Absence",
                "fieldname": "ed_reason_for_absence",
                "insert_after": "section_break_33",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Encounter Category",
                "fieldname": "encounter_category",
                "insert_after": "encounter_time",
                "options": "Encounter Category",
                
            },
            {
                "fieldtype": "Link",
                "label": "Encounter Mode of Payment",
                "fieldname": "encounter_mode_of_payment",
                "insert_after": "encounter_category",
                "options": "Mode of Payment", "mandatory_depends_on": "eval: doc.encounter_category == \"Direct Cash\"",
                
            },
            {
                "fieldtype": "Select",
                "label": "Encounter Type",
                "fieldname": "encounter_type",
                "insert_after": "reference",
                "options": "Initial\nOngoing\nFinal",
                "default": "Initial",
                "read_only": 1,
                "allow_on_submit": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Text Editor",
                "label": "History of the Symptoms and Examination Details",
                "fieldname": "examination_detail",
                "insert_after": "system_and_symptoms",
                "mandatory_depends_on": "eval:!doc.practitioner.includes ('Direct')",
                "translatable": 1,
                "permlevel": 1,
                
            },
            {
                "fieldtype": "Button",
                "label": "Clear History",
                "fieldname": "clear_history",
                "insert_after": "examination_detail",
                "hidden": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Finalized",
                "fieldname": "finalized",
                "insert_after": "encounter_type",
                "read_only": 1,
                "allow_on_submit": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "in_preview": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Duplicated From",
                "fieldname": "from_encounter",
                "insert_after": "reference_encounter",
                "options": "Patient Encounter",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Button",
                "label": "Get Chronic Diagnosis",
                "fieldname": "get_chronic_diagnosis",
                "insert_after": "section_break_28",
                "depends_on": "eval: doc.docstatus == 0",
                
            },
            {
                "fieldtype": "Button",
                "label": "Get Chronic Medications",
                "fieldname": "get_chronic_medications",
                "insert_after": "sb_drug_prescription",
                
            },
            {
                "fieldtype": "Button",
                "label": "Get Lab Bundle Items",
                "fieldname": "get_lab_bundle_items",
                "insert_after": "lab_bundle",
                
            },
            {
                "fieldtype": "Signature",
                "label": "Healthcare Practitioner Signature",
                "fieldname": "healthcare_practitioner_signature",
                "insert_after": "patient_signature",
                "fetch_from": "practitioner.doctors_signature",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Healthcare Referrer",
                "fieldname": "healthcare_referrer",
                "insert_after": "referring_practitioner",
                "fetch_from": "appointment.healthcare_referrer",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Healthcare Service Unit",
                "fieldname": "healthcare_service_unit",
                "insert_after": "appointment_type",
                "options": "Healthcare Service Unit",
                "fetch_from": "appointment.service_unit",
                "fetch_if_empty": 1,
                "read_only": 1,
                "hidden": 1,
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "hms_tz_column_break",
                "insert_after": "get_chronic_diagnosis",
                
            },
            {
                "fieldtype": "Button",
                "label": "Add Chronic Diagnosis",
                "fieldname": "hms_tz_add_chronic_diagnosis",
                "insert_after": "hms_tz_column_break",
                "depends_on": "eval: doc.docstatus == 0",
                
            },
            {
                "fieldtype": "Button",
                "label": "Convert to Inpatient",
                "fieldname": "hms_tz_convert_to_inpatient",
                "insert_after": "medical_department",
                "bold": 1,
                "permlevel": 3,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Previous History of the Symptoms and Examination Details",
                "fieldname": "hms_tz_previous_section_break",
                "insert_after": "system_and_symptoms",
                "collapsible": 1,
                
            },
            {
                "fieldtype": "Text Editor",
                "label": "Notes",
                "fieldname": "hms_tz_previous_examination_detail",
                "insert_after": "hms_tz_previous_section_break",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "hms_tz_examination_detail_section_break",
                "insert_after": "hms_tz_previous_examination_detail",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "hms_tz_section_break",
                "insert_after": "hms_tz_add_chronic_diagnosis",
                
            },
            {
                "fieldtype": "Attach Image",
                "label": "Image",
                "fieldname": "image",
                "insert_after": "patient_age",
                "fetch_from": "patient.image",
                "fetch_if_empty": 1,
                "read_only": 1,
                "hidden": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Insurance Coverage Plan",
                "fieldname": "insurance_coverage_plan",
                "insert_after": "mode_of_payment",
                "fetch_from": "appointment.coverage_plan_name",
                "read_only": 1,
                "in_list_view": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Not Billable",
                "fieldname": "is_not_billable",
                "insert_after": "current_total",
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Lab Bundle",
                "fieldname": "lab_bundle",
                "insert_after": "sb_test_prescription",
                "options": "Lab Bundle",
                
            },
            {
                "fieldtype": "Data",
                "label": "Mode of Payment",
                "fieldname": "mode_of_payment",
                "insert_after": "healthcare_service_unit",
                "fetch_from": "appointment.mode_of_payment",
                "read_only": 1,   "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Old HMS Registration No",
                "fieldname": "old_hms_registration_no",
                "insert_after": "blood_group",
                "fetch_from": "patient.old_hms_registration_no",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Final Diagnosis",
                "fieldname": "patient_encounter_final_diagnosis",
                "insert_after": "copy_from_preliminary_diagnosis",
                "options": "Codification Table",
                
            },
            {
                "fieldtype": "Table",
                "label": "Preliminary Diagnosis",
                "fieldname": "patient_encounter_preliminary_diagnosis",
                "insert_after": "hms_tz_section_break",
                "options": "Codification Table",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Patient Information",
                "fieldname": "patient_info_section_break",
                "insert_after": "section_break_3",
                "collapsible": 1,
                
            },
            {
                "fieldtype": "Signature",
                "label": "Patient Signature",
                "fieldname": "patient_signature",
                "insert_after": "signatures",
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Diet Recommendation",
                "fieldname": "previous_diet_recommendation",
                "insert_after": "diet_recommendation",
                "options": "Previous Diet Recommendation",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Items",
                "fieldname": "previous_drug_prescription",
                "insert_after": "drug_prescription",
                "options": "Previous Drug Prescription",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Lab Tests",
                "fieldname": "previous_lab_prescription",
                "insert_after": "lab_test_prescription",
                "options": "Previous Lab Prescription",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Clinical Procedures",
                "fieldname": "previous_procedure_prescription",
                "insert_after": "procedure_prescription",
                "options": "Previous Procedure Prescription",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Radiology Procedure",
                "fieldname": "previous_radiology_procedure_prescription",
                "insert_after": "radiology_procedure_prescription",
                "options": "Previous Radiology Procedure Prescription",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Previous Therapies",
                "fieldname": "previous_therapy_plan_detail",
                "insert_after": "therapies",
                "options": "Previous Therapy Plan Detail",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Float",
                "label": "Previous Total",
                "fieldname": "previous_total",
                "insert_after": "sb_refs",
                "read_only": 1, "hidden": 1,
                "print_hide": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Reference",
                "fieldname": "reference",
                "insert_after": "diagnosis_in_print",
                "hidden": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Reference Encounter",
                "fieldname": "reference_encounter",
                "insert_after": "column_break_31",
                "options": "Patient Encounter",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Sales Invoice",
                "fieldname": "sales_invoice",
                "insert_after": "create_sales_invoice",
                "options": "Sales Invoice",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "PRELIMINARY DIAGNOSIS",
                "fieldname": "section_break_28",
                "insert_after": "claim_status",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_52",
                "insert_after": "previous_radiology_procedure_prescription",
                
            },
            {
                "fieldtype": "Button",
                "label": "Sent To VFD",
                "fieldname": "sent_to_vfd",
                "insert_after": "sales_invoice",
                "depends_on": "eval: doc.sales_invoice",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "Signatures",
                "fieldname": "signatures",
                "insert_after": "encounter_comment",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Symptoms and Signs",
                "fieldname": "symptoms_and_signs",
                "insert_after": "healthcare_referrer",
                "permlevel": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "System and Symptoms",
                "fieldname": "system_and_symptoms",
                "insert_after": "symptoms_and_signs",
                "options": "Patient Encounter Symptom",
                "permlevel": 1,
                
            },
            {
                "fieldtype": "Button",
                "label": "Undo Set as Final",
                "fieldname": "undo_set_as_final",
                "insert_after": "is_not_billable",
                "permlevel": 3,
                
            },
        ],
        "Patient Referral": [
            {
                "fieldtype": "Data",
                "label": "Insurance Company",
                "fieldname": "insurance_company",
                "insert_after": "patient_mobile",
                "fetch_from": "patient_encounter.insurance_company",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Insurance Coverage Plan",
                "fieldname": "insurance_coverage_plan",
                "insert_after": "insurance_company",
                "fetch_from": "patient_encounter.insurance_coverage_plan",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Patient Mobile",
                "fieldname": "patient_mobile",
                "insert_after": "patient_name",
                "fetch_from": "patient.mobile",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Patient Name",
                "fieldname": "patient_name",
                "insert_after": "patient",
                "fetch_from": "patient.patient_name",
                "read_only": 1,
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Referred to Facility",
                "fieldname": "referred_to_facility",
                "insert_after": "referred_to_medical_department",
                "options": "NHIF Facility Code",
                
            },
            {
                "fieldtype": "Data",
                "label": "Referred to Medical Department",
                "fieldname": "referred_to_medical_department",
                "insert_after": "referred_to_practitioner",
                "fetch_from": "referred_to_practitioner.department",
                "read_only": 1,
                "translatable": 1,
                
            },
        ],
        "Patient": [
            {
                "fieldtype": "Data",
                "label": "Area Old",
                "fieldname": "area",
                "insert_after": "nida_card_number",
                "hidden": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Card No",
                "fieldname": "card_no",
                "insert_after": "insurance_details",
                "read_only_depends_on": "eval: doc.card_no",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Currency",
                "label": "Cash Limit",
                "fieldname": "cash_limit",
                "insert_after": "language",
                "precision": 2,
                "default": 5000000,
                
            },
            {
                "fieldtype": "Table",
                "label": "Chronic Medications",
                "fieldname": "chronic_medications",
                "insert_after": "codification_table",
                "options": "Chronic Medications",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Chronic Section",
                "fieldname": "chronic_section",
                "insert_after": "surgical_history",
                "permlevel": 1,
                
            },
            {
                "fieldtype": "Table",
                "label": "Codification Table",
                "fieldname": "codification_table",
                "insert_after": "chronic_section",
                "options": "Codification Table",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_3",
                "insert_after": "card_no",
                
            },
            {
                "fieldtype": "Link",
                "label": "Common Occupation",
                "fieldname": "common_occupation",
                "insert_after": "age_html",
                "options": "Occupation",
                "reqd": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Area",
                "fieldname": "demography",
                "insert_after": "area",
                "options": "Demography",
                "reqd": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Ethnicity",
                "fieldname": "ethnicity",
                "insert_after": "common_occupation",
                "options": "Ethnicity",
                "reqd": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "How did you hear about us",
                "fieldname": "how_did_you_hear_about_us",
                "insert_after": "mobile",
                "options": "Campaign",
                "reqd": 1,
                
            },
            {
                "fieldtype": "Small Text",
                "label": "Insurance Card Detail",
                "fieldname": "insurance_card_detail",
                "insert_after": "column_break_3",
                "translatable": 1,
                "permlevel": 2,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Insurance Details",
                "fieldname": "insurance_details",
                
            },
            {
                "fieldtype": "Data",
                "label": "Membership No",
                "fieldname": "membership_no",
                "insert_after": "product_code",
                "read_only": 1,
                "hidden": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "next_to_kid_column_break",
                "insert_after": "next_to_kin_mobile_no",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Next to Kin Details",
                "fieldname": "next_to_kin_details",
                "insert_after": "marital_status",
                
            },
            {
                "fieldtype": "Data",
                "label": "Next to Kin Mobile No",
                "fieldname": "next_to_kin_mobile_no",
                "insert_after": "next_to_kin_name",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Next to Kin Name",
                "fieldname": "next_to_kin_name",
                "insert_after": "next_to_kin_details",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Next to Kin Relationship",
                "fieldname": "next_to_kin_relationship",
                "insert_after": "next_to_kid_column_break",
                "options": "\nFather\nMother\nSpouse\nSiblings\nFamily\nOther",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "NIDA Card Number",
                "fieldname": "nida_card_number",
                "insert_after": "report_preference",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Old HMS Registration No",
                "fieldname": "old_hms_registration_no",
                "insert_after": "phone",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Text Editor",
                "label": "Patient Details",
                "fieldname": "patient_details_with_formatting",
                "insert_after": "patient_details",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Signature",
                "label": "Patient Signature",
                "fieldname": "patient_signature",
                "insert_after": "old_hms_registration_no",
                
            },
            {
                "fieldtype": "Data",
                "label": "Product Code",
                "fieldname": "product_code",
                "insert_after": "insurance_card_detail",
                "read_only": 1,
                "hidden": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Referred From",
                "fieldname": "referred_from",
                "insert_after": "how_did_you_hear_about_us",
                "options": "Referred From",
                "depends_on": "eval:doc.how_did_you_hear_about_us == \"Referred\"",
                
            },
        ],
        "Prescription Dosage": [
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_1",
                "insert_after": "dosage",
                
            },
            {
                "fieldtype": "Float",
                "label": "Quantity in PCs",
                "fieldname": "default_strength",
                "insert_after": "column_break_1",
                "allow_in_quick_entry": 1,
                "description": "Enter total quantity in PCs (tabs, caps, vials) of prescription to be dispensed for each day",
                
            },
            {
                "fieldtype": "Link",
                "label": "Dosage Form",
                "fieldname": "dosage_form",
                "insert_after": "default_strength",
                "options": "Dosage Form",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_3",
                "insert_after": "dosage_form",
                
            },
        ],
        "Previous Drug Prescription": [
            {
                "fieldtype": "Check",
                "label": "Is Cancelled",
                "fieldname": "is_cancelled",
                "insert_after": "cancelled",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "NHIF 2C Form",
                "fieldname": "nhif_2c_form",
                "insert_after": "prescribe",
                
            },
        ],
        "Previous Lab Prescription": [
            {
                "fieldtype": "Check",
                "label": "Is Cancelled",
                "fieldname": "is_cancelled",
                "insert_after": "cancelled",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
        ],
        "Previous Procedure Prescription": [
            {
                'fieldtype': 'Check',
                'label': 'Is Cancelled',
                'fieldname': 'is_cancelled',
                'insert_after': 'cancelled',
                'read_only': 1,
                'allow_on_submit': 1,
            }
        ],
        "Previous Radiology Procedure Prescription": [
            {
                'fieldtype': 'Check',
                'label': 'Is Cancelled',
                'fieldname': 'is_cancelled',
                'insert_after': 'cancelled',
                'read_only': 1,
                'allow_on_submit': 1,
            }
        ],
        "Previous Therapy Plan Detail": [
            {
                'fieldtype': 'Column Break',
                'label': '',
                'fieldname': 'column_break_6',
                'insert_after': 'sessions_completed',
                
            },
            {
                'fieldtype': 'Check',
                'label': 'Is Cancelled',
                'fieldname': 'is_cancelled',
                'insert_after': 'cancelled',
                'read_only': 1,
                'allow_on_submit': 1,
            }
        ],
        "Procedure Prescription": [
            {
                "fieldtype": "Float",
                "label": "Amount",
                "fieldname": "amount",
                "insert_after": "procedure_created",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Cancelled",
                "fieldname": "cancelled",
                "insert_after": "reference_journal_entry",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_10",
                "insert_after": "clinical_procedure",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_30",
                "insert_after": "delivered_quantity",
                
            },
            {
                "fieldtype": "Float",
                "label": "Delivered Quantity",
                "fieldname": "delivered_quantity",
                "insert_after": "section_break_28",
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Discount Applied",
                "fieldname": "hms_tz_is_discount_applied",
                "insert_after": "amount",
                "read_only": 1,
                "description": "Discount is applied only if the discount percent is defined on Healthcare Insurance Company",
                
            },
            {
                "fieldtype": "Select",
                "label": "HSO Payment Method",
                "fieldname": "hso_payment_method",
                "insert_after": "override_insurance_subscription",
                "options": "\nCash\nPrescribe",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Cancelled",
                "fieldname": "is_cancelled",
                "insert_after": "reference_journal_entry",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Not Available Inhouse",
                "fieldname": "is_not_available_inhouse",
                "insert_after": "prescribe",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Medical Code",
                "fieldname": "medical_code",
                "insert_after": "procedure",
                "reqd": 1,
                "in_list_view": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Override Insurance Subscription",
                "fieldname": "override_insurance_subscription",
                "insert_after": "column_break_10",
                
            },
            {
                "fieldtype": "Check",
                "label": "Override Healthcare Insurance Subscription",
                "fieldname": "override_subscription",
                "insert_after": "medical_code",
                "permlevel": 2,
                
            },
            {
                "fieldtype": "Check",
                "label": "Prescribe",
                "fieldname": "prescribe",
                "insert_after": "override_subscription",
                
            },
            {
                "fieldtype": "Data",
                "label": "Reference Journal Entry",
                "fieldname": "reference_journal_entry",
                "insert_after": "sales_invoice_number",
                "read_only": 1,    "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Sales Invoice Number",
                "fieldname": "sales_invoice_number",
                "insert_after": "column_break_30",
                "read_only": 1,
                "allow_on_submit": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_28",
                "insert_after": "note",
                
            },
        ],
        "Radiology Examination Template": [
            {
                "fieldtype": "Link",
                "label": "Body Part",
                "fieldname": "body_part",
                "insert_after": "description",
                "options": "Body Part",
                
            },
            {
                "fieldtype": "Link",
                "label": "Healthcare Service Unit",
                "fieldname": "healthcare_service_unit",
                "insert_after": "healthcare_service_unit_type",
                "options": "Healthcare Service Unit",
                "hidden": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Radiology Report",
                "fieldname": "radiology_report",
                "insert_after": "medical_code",
                
            },
            {
                "fieldtype": "Text Editor",
                "label": "Radiology Report Details",
                "fieldname": "radiology_report_details",
                "insert_after": "radiology_report_type",
                "fetch_from": "radiology_report_type.terms",
                "fetch_if_empty": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Radiology Report Type",
                "fieldname": "radiology_report_type",
                "insert_after": "radiology_report",
                "options": "Healthcare Notes Template",
                
            },
        ],
        "Radiology Examination": [
            {
                "fieldtype": "Data",
                "label": "Service Reference Number",
                "fieldname": "approval_number",
                "insert_after": "is_restricted",
                "depends_on": "eval: doc.is_restricted",
                "mandatory_depends_on": "eval: doc.is_restricted",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Approval Type",
                "fieldname": "approval_type",
                "insert_after": "approval_number",
                "options": "Local\nNHIF\nOther Insurance",
                "depends_on": "eval: doc.is_restricted",
                "mandatory_depends_on": "eval: doc.is_restricted",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Body Part",
                "fieldname": "body_part",
                "insert_after": "amended_from",
                "options": "Body Part",
                "fetch_from": "radiology_examination_template.body_part",
                
            },
            {
                "fieldtype": "Data",
                "label": "Healthcare Practitioner Name",
                "fieldname": "healthcare_practitioner_name",
                "insert_after": "practitioner",
                "fetch_from": "practitioner.practitioner_name",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Ref Childname",
                "fieldname": "hms_tz_ref_childname",
                "insert_after": "ref_docname",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Restricted",
                "fieldname": "is_restricted",
                "insert_after": "patient_details_html",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Radiology Report",
                "fieldname": "radiology_report",
                "insert_after": "terms",
                "options": "Healthcare Notes Template",
                "fetch_from": "radiology_examination_template.radiology_report_type",
                
            },
            {
                "fieldtype": "Text Editor",
                "label": "Radiology Report Details",
                "fieldname": "radiology_report_details",
                "insert_after": "radiology_report",
                "fetch_from": "radiology_report.terms",
                "fetch_if_empty": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Ref DocType",
                "fieldname": "ref_doctype",
                "insert_after": "radiology_report_details",
                "options": "DocType",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Dynamic Link",
                "label": "Ref DocName",
                "fieldname": "ref_docname",
                "insert_after": "ref_doctype",
                "options": "ref_doctype",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Text",
                "label": "Service Comment",
                "fieldname": "service_comment",
                "insert_after": "healthcare_practitioner_name",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Status",
                "fieldname": "status",
                "insert_after": "workflow_state",
                "allow_on_submit": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Workflow State",
                "fieldname": "workflow_state",
                "options": "Workflow State",
                "hidden": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldname": "hms_tz_patient_age",
                "fieldtype": "Data",
                "label": "Age",
                "insert_after": "patient_name",
                "fetch_from ":  "ref_docname.patient_age",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
            {
                "fieldname": "hms_tz_patient_sex",
                "fieldtype": "Link",
                "label": "Gender",
                "options": "Gender",
                "insert_after": "hms_tz_patient_age",
                "fetch_from ":  "ref_docname.patient_sex",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
            {
                "fieldname": "hms_tz_insurance_coverage_plan",
                "fieldtype": "Data",
                "label": "Insurance Coverage Plan",
                "insert_after": "insurance_subscription",
                "fetch_from ":  "insurance_subscription.healthcare_insurance_coverage_plan",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            }
        ],
        "Radiology Procedure Prescription": [
            {
                "fieldtype": "Float",
                "label": "Amount",
                "fieldname": "amount",
                "insert_after": "radiology_procedure_name",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Cancelled",
                "fieldname": "cancelled",
                "insert_after": "reference_journal_entry",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_25",
                "insert_after": "delivered_quantity",
                
            },
            {
                "fieldtype": "Float",
                "label": "Delivered Quantity",
                "fieldname": "delivered_quantity",
                "insert_after": "section_break_23",
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Discount Applied",
                "fieldname": "hms_tz_is_discount_applied",
                "insert_after": "amount",
                "read_only": 1,
                "description": "Discount is applied only if the discount percent is defined on Healthcare Insurance Company",
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Cancelled",
                "fieldname": "is_cancelled",
                "insert_after": "reference_journal_entry",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Not Available Inhouse",
                "fieldname": "is_not_available_inhouse",
                "insert_after": "prescribe",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Medical Code",
                "fieldname": "medical_code",
                "insert_after": "radiology_examination_template",
                "reqd": 1,
                "in_list_view": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Override Healthcare Insurance Subscription",
                "fieldname": "override_subscription",
                "insert_after": "medical_code",
                "permlevel": 2,
                
            },
            {
                "fieldtype": "Check",
                "label": "Prescribe",
                "fieldname": "prescribe",
                "insert_after": "override_subscription",
                
            },
            {
                "fieldtype": "Data",
                "label": "Reference Journal Entry",
                "fieldname": "reference_journal_entry",
                "insert_after": "sales_invoice_number",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Sales Invoice Number",
                "fieldname": "sales_invoice_number", "insert_after": "column_break_25",
                "read_only": 1,
                "allow_on_submit": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_23",
                "insert_after": "note",
                
            },
        ],
        "Sales Invoice Item": [
            {
                "fieldtype": "Link",
                "label": "Department",
                "fieldname": "department",
                "insert_after": "healthcare_practitioner",
                "options": "Department",
                
            },
            {
                "fieldtype": "Link",
                "label": "Healthcare Practitioner",
                "fieldname": "healthcare_practitioner",
                "insert_after": "healthcare_service_unit",
                "options": "Healthcare Practitioner",
                
            },
            {
                "fieldtype": "Link",
                "label": "Healthcare Service Unit",
                "fieldname": "healthcare_service_unit",
                "insert_after": "accounting_dimensions_section",
                "options": "Healthcare Service Unit",
                
            },
            {
                "fieldtype": "Check",
                "label": "Is LRP Item Created",
                "fieldname": "hms_tz_is_lrp_item_created",
                "insert_after": "reference_dn",
                "depends_on": "eval: doc.reference_dt==\"Lab Prescription\" || doc.reference_dt==\"Radiology Procedure Prescription\" || doc.reference_dt==\"Procedure Prescription\" ",
                "read_only": 1,
                "allow_on_submit": 1,
                "bold": 1,
                
            },
        ],
        "Sales Order": [
            {
                "fieldtype": "Data",
                "label": "Patient Actual Name",
                "fieldname": "patient_actual_name",
                "insert_after": "customer_name",
                "depends_on": "eval: doc.customer == \"Cash Customer\"", "mandatory_depends_on": "eval: doc.customer == \"Cash Customer\"",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Patient Mobile Number",
                "fieldname": "patient_mobile_number",
                "insert_after": "patient_actual_name",
                "options": "Phone",  "depends_on": "eval: doc.customer == \"Cash Customer\"", "mandatory_depends_on": "eval: doc.customer == \"Cash Customer\"",
                "translatable": 1,
                
            },
        ],
        "Sample Collection": [
            {
                "fieldtype": "Link",
                "label": "Ref DocType",
                "fieldname": "ref_doctype",
                "insert_after": "section_break_20",
                "options": "DocType",
                "read_only": 1,
                "print_hide": 1,
                
            },
            {
                "fieldtype": "Dynamic Link",
                "label": "Ref DocName",
                "fieldname": "ref_docname",
                "insert_after": "ref_doctype",
                "options": "ref_doctype",
                "read_only": 1,
                "print_hide": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_20",
                "insert_after": "sample_details",
                
            },
        ],
        "Therapy Plan Detail": [
            {
                "fieldtype": "Float",
                "label": "Amount",
                "fieldname": "amount",
                "insert_after": "is_not_available_inhouse",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Cancelled",
                "fieldname": "cancelled",
                "insert_after": "reference_journal_entry",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_22",
                "insert_after": "delivered_quantity",
                
            },
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_6",
                "insert_after": "sessions_completed",
                
            },
            {
                "fieldtype": "Small Text",
                "label": "Comment",
                "fieldname": "comment",
                "insert_after": "column_break_6",
                "mandatory_depends_on": "eval:doc.override_subscription == 1 && doc.prescribe != 1;",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Float",
                "label": "Delivered Quantity",
                "fieldname": "delivered_quantity",
                "insert_after": "section_break_20",
                "default": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Discount Applied",
                "fieldname": "hms_tz_is_discount_applied",
                "insert_after": "amount",
                "read_only": 1,
                "description": "Discount is applied only if the discount percent is defined on Healthcare Insurance Company",
                
            },
            {
                "fieldtype": "Check",
                "label": "Invoiced",
                "fieldname": "invoiced",
                "insert_after": "cancelled",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Cancelled",
                "fieldname": "is_cancelled",
                "insert_after": "reference_journal_entry",
                "read_only": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Is Not Available Inhouse",
                "fieldname": "is_not_available_inhouse",
                "insert_after": "prescribe",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Medical Code",
                "fieldname": "medical_code",
                "insert_after": "therapy_type",
                "mandatory_depends_on": "eval:doc.parent == \"Patient Encounter\"",
                "in_list_view": 1,  "translatable": 1,
                
            },
            {
                "fieldtype": "Check",
                "label": "Override Healthcare Insurance Subscription",
                "fieldname": "override_subscription",
                "insert_after": "medical_code",
                "permlevel": 2,
                
            },
            {
                "fieldtype": "Check",
                "label": "Prescribe",
                "fieldname": "prescribe",
                "insert_after": "override_subscription",
                
            },
            {
                "fieldtype": "Data",
                "label": "Reference Journal Entry",
                "fieldname": "reference_journal_entry",
                "insert_after": "sales_invoice_number",
                "read_only": 1,    "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Sales Invoice Number",
                "fieldname": "sales_invoice_number",
                "insert_after": "column_break_22",
                "allow_on_submit": 1, "translatable": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_20",
                "insert_after": "note",
                
            },
        ],
        "Therapy Plan Template": [
            {
                'fieldtype': 'Check',
                'label': 'Is Not Available Inhouse',
                'fieldname': 'is_not_available_inhouse',
                'insert_after': 'plan_name',
            }
        ],
        "Therapy Plan": [
            {
                "fieldtype": "Link",
                "label": "Ref DocType",
                "fieldname": "ref_doctype",
                "insert_after": "total_sessions_completed",
                "options": "DocType",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Dynamic Link",
                "label": "Ref DocName",
                "fieldname": "ref_docname",
                "insert_after": "ref_doctype",
                "options": "ref_doctype",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Link",
                "label": "Workflow State",
                "fieldname": "workflow_state",
                "options": "Workflow State",
                "hidden": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                
            },
            {
                "fieldname": "hms_tz_appointment",
                "fieldtype": "Link",
                "label": "Appointment",
                "options": "Patient Appointment",
                "insert_after": "naming_series",
                "fetch_from ":  "ref_docname.appointment",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
            {
                "fieldname": "hms_tz_patient_age",
                "fieldtype": "Data",
                "label": "Age",
                "insert_after": "patient_name",
                "fetch_from ":  "ref_docname.patient_age",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
            {
                "fieldname": "hms_tz_patient_sex",
                "fieldtype": "Link",
                "label": "Gender",
                "options": "Gender",
                "insert_after": "hms_tz_patient_age",
                "fetch_from ":  "ref_docname.patient_sex",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
            {
                "fieldname": "hms_tz_insurance_coverage_plan",
                "fieldtype": "Data",
                "label": "Insurance Coverage Plan",
                "insert_after": "hms_tz_patient_sex",
                "fetch_from ":  "ref_docname.insurance_coverage_plan",
                "fetch_if_empty": 1,
                "read_only": 1,
                
            },
        ],
        "Vital Signs": [
            {
                "fieldtype": "Column Break",
                "label": "",
                "fieldname": "column_break_29",
                "insert_after": "verbal_response",
                
            },
            {
                "fieldtype": "Select",
                "label": "Eye Opening",
                "fieldname": "eye_opening",
                "insert_after": "glasgow_coma_scale",
                "options": "\n4 - Spontaneous--open with blinking at baseline\n3 - To verbal stimuli, command, speech\n2 - To pain only (not applied to face)\n1 - No response",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Glasgow Coma Scale",
                "fieldname": "glasgow_coma_scale",
                "insert_after": "intraocular_pressure_le",
                "collapsible": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Healthcare Practitioner",
                "fieldname": "healthcare_practitioner",
                "insert_after": "medical_department",
                "fetch_from": "appointment.practitioner_name",
                "read_only": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Int",
                "label": "Height (in cm)",
                "fieldname": "height_in_cm",
                "insert_after": "weight",
                
            },
            {
                "fieldtype": "Attach Image",
                "label": "Image", "fieldname": "image",
                "insert_after": "patient_name",
                "fetch_from": "patient.image",
                "fetch_if_empty": 1,
                "read_only": 1,
                "hidden": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Intraocular Pressure LE",
                "fieldname": "intraocular_pressure_le",
                "insert_after": "intraocular_pressure_re",
                "depends_on": "eval:doc.medical_department=='Eye'",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Intraocular Pressure RE",
                "fieldname": "intraocular_pressure_re",
                "insert_after": "visual_acuity_le",
                "depends_on": "eval:doc.medical_department=='Eye'",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Medical Department",
                "fieldname": "medical_department",
                "insert_after": "practitioner",
                "fetch_from": "appointment.department",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Mode of Payment",
                "fieldname": "mode_of_payment",
                "insert_after": "appointment",
                "fetch_from": "appointment.mode_of_payment",
                "read_only": 1,
                "hidden": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Motor Response",
                "fieldname": "motor_response",
                "insert_after": "column_break_29",
                "options": "\n6 - Obeys commands for movement\n5 - Purposeful movement to painful stimulus\n4 - Withdraws in response to pain\n3 - Flexion in response to pain (decorticate posturing)\n2 - Extension response in response to pain (decerebrate posturing)\n1 - No response",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Oxygen saturation SpO2",
                "fieldname": "oxygen_saturation_spo2",
                "insert_after": "respiratory_rate",
                "translatable": 1,
                "description": "For a healthy individual, the normal SpO2 should be between 96% to 99%.",
                
            },
            {
                "fieldtype": "Select",
                "label": "Patient Progress",
                "fieldname": "patient_progress",
                "insert_after": "signs_time",
                "options": "To Doctor\nEmergency",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "HTML",
                "label": "Patient Vitals",
                "fieldname": "patient_vitals",
                "insert_after": "patient_vitals_summary",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "Patient Vitals Summary",
                "fieldname": "patient_vitals_summary",
                
            },
            {
                "fieldtype": "Link",
                "label": "Practitioner",
                "fieldname": "practitioner",
                "insert_after": "mode_of_payment",
                "options": "Healthcare Practitioner",
                "fetch_from": "appointment.practitioner",
                "read_only": 1,
                
            },
            {
                "fieldtype": "Float",
                "label": "Random blood glucose (rbg)",
                "fieldname": "rbg",
                "insert_after": "oxygen_saturation_spo2",
                "description": "Value in mmol/l: The reference values for a \"normal\" random glucose test in an average adult are 4.4\u9225?.8 mmol/l, between 7.8\u9225?1.1 mmol/l is considered pre-diabetes, and > 11.1 mmol/l is considered diabetes according to ADA guidelines",
                
            },
            {
                "fieldtype": "Section Break",
                "label": "",
                "fieldname": "section_break_2",
                "insert_after": "patient_vitals",
                
            },
            {
                "fieldtype": "Data",
                "label": "Coverage Plan Name",
                "fieldname": "shm_coverage_plan_name",
                "insert_after": "company",
                "fetch_from": "appointment.coverage_plan_name",
                "read_only": 1,
                "translatable": 1,
                
            },
            {
                "fieldtype": "Select",
                "label": "Verbal Response",
                "fieldname": "verbal_response",
                "insert_after": "eye_opening",
                "options": "\n5 - Oriented\n4 - Confused conversation, but able to answer questions\n3 - Inappropriate words\n2 - Incomprehensible speech\n1 - No response",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Visual Acuity LE",
                "fieldname": "visual_acuity_le",
                "insert_after": "visual_acuity_re",
                "depends_on": "eval:doc.medical_department=='Eye'",
                "translatable": 1,
                
            },
            {
                "fieldtype": "Data",
                "label": "Visual Acuity RE",
                "fieldname": "visual_acuity_re",
                "insert_after": "vital_signs_note",
                "depends_on": "eval:doc.medical_department=='Eye'",
                "translatable": 1,
                
            },
        ]
    }

    create_custom_fields(fields, update=True)
