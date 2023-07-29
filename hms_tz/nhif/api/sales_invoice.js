frappe.ui.form.on('Sales Invoice', {
	onload: function (frm) {
		frm.trigger('add_get_info_btn');
	},
	// patient: function (frm) {
	// 	frm.clear_table("items")
	// },
	refresh: function (frm) {
		if (frappe.boot.active_domains.includes("Healthcare")) {
			frm.set_df_property("patient", "hidden", 0);
			frm.set_df_property("patient_name", "hidden", 0);
			frm.set_df_property("ref_practitioner", "hidden", 0);
			frm.remove_custom_button('Healthcare Services', 'Get Items From');
			frm.remove_custom_button('Prescriptions', 'Get Items From');
			if (cint(frm.doc.docstatus == 0) && cur_frm.page.current_view_name !== "pos" && !frm.doc.is_return) {
				frm.add_custom_button(__('Get Healthcare Services'), function () {
					get_healthcare_services_to_invoice(frm);
				});
				frm.add_custom_button(__('Get Sales Order'),
					function () {
						erpnext.utils.map_current_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
							source_doctype: "Sales Order",
							target: me.frm,
							setters: {
								customer: me.frm.doc.customer || undefined,
							},
							get_query_filters: {
								docstatus: 1,
								status: ["not in", ["Closed", "On Hold"]],
								per_billed: ["<", 99.99],
								company: me.frm.doc.company
							}
						});
					});
				frm.add_custom_button(__('Healthcare Services'), function () {
					get_healthcare_services_to_invoice(frm);
				}, "Get Items From");
			}
			if (frm.doc.docstatus == 1) {
				frm.add_custom_button(__("Create Pending Healthcare Services"), function () {
					frappe.call({
						method: 'hms_tz.nhif.api.sales_invoice.create_pending_healthcare_docs',
						args: {
							doc_name: frm.doc.name,
						},
						callback: function (r) {
							// Any other code
						}
					});
				});
			};
		}
		else {
			frm.set_df_property("patient", "hidden", 1);
			frm.set_df_property("patient_name", "hidden", 1);
			frm.set_df_property("ref_practitioner", "hidden", 1);
		}
	},
	hms_tz_request_discount: (frm) => {
		show_disocunt_dialog(frm);
	}
});

var get_healthcare_services_to_invoice = function (frm) {
	var me = this;
	let selected_patient = '';
	var dialog = new frappe.ui.Dialog({
		title: __("Get Items From Healthcare Services"),
		fields: [
			{
				fieldtype: 'Link',
				options: 'Patient',
				label: 'Patient',
				fieldname: "patient",
				reqd: true,
			},
			{
				fieldtype: 'Link',
				options: 'Patient Encounter',
				label: 'Patient Encounter',
				fieldname: "encounter",
				reqd: true,
				get_query: function (doc) {
					return {
						filters: {
							patient: dialog.get_value("patient"),
							company: frm.doc.company,
							encounter_date: [">", frappe.datetime.add_days(frappe.datetime.now_date(true), -7)],
							is_not_billable: 0,
							duplicated: 0,
							docstatus: 1
						}
					};
				}
			},
			{
				fieldtype: 'Button',
				label: 'Get Items',
				fieldname: "get_items",
			},
			{ fieldtype: 'Section Break' },
			{ fieldtype: 'HTML', fieldname: 'results_area' }
		]
	});
	var $wrapper;
	var $results;
	var $placeholder;
	dialog.set_values({
		'patient': frm.doc.patient
	});
	dialog.fields_dict.get_items.input.onclick = function () {
		var patient = dialog.fields_dict.patient.input.value;
		var encounter = dialog.fields_dict.encounter.input.value;
		if (patient && encounter) {
			selected_patient = patient;
			var method = "hms_tz.nhif.api.healthcare_utils.get_healthcare_services_to_invoice";
			var args = {
				patient: patient,
				company: frm.doc.company,
				encounter: encounter,
				prescribed: 1,
			};
			var columns = (["service", "reference_name", "reference_type"]);
			get_healthcare_items(frm, true, $results, $placeholder, method, args, columns);
		}
		else if (!patient) {
			selected_patient = '';
			$results.empty();
			$results.append($placeholder);
		}
	};
	$wrapper = dialog.fields_dict.results_area.$wrapper.append(`<div class="results"
		style="border: 1px solid #d1d8dd; border-radius: 3px; height: 300px; overflow: auto;"></div>`);
	$results = $wrapper.find('.results');
	$placeholder = $(`<div class="multiselect-empty-state">
				<span class="text-center" style="margin-top: -40px;">
					<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
					<p class="text-extra-muted">No billable Healthcare Services found</p>
				</span>
			</div>`);
	$results.on('click', '.list-item--head :checkbox', (e) => {
		$results.find('.list-item-container .list-row-check')
			.prop("checked", ($(e.target).is(':checked')));
	});
	set_primary_action(frm, dialog, $results, true);
	dialog.show();
};


var get_healthcare_items = function (frm, invoice_healthcare_services, $results, $placeholder, method, args, columns) {
	var me = this;
	$results.empty();
	frappe.call({
		method: method,
		args: args,
		callback: function (data) {
			if (data.message) {
				$results.append(make_list_row(columns, invoice_healthcare_services));
				for (let i = 0; i < data.message.length; i++) {
					$results.append(make_list_row(columns, invoice_healthcare_services, data.message[i]));
				}
			} else {
				$results.append($placeholder);
			}
		}
	});
};

var make_list_row = function (columns, invoice_healthcare_services, result = {}) {
	var me = this;
	// Make a head row by default (if result not passed)
	let head = Object.keys(result).length === 0;
	let contents = ``;
	columns.forEach(function (column) {
		contents += `<div class="list-item__content ellipsis">
			${head ? `<span class="ellipsis">${__(frappe.model.unscrub(column))}</span>`

				: (column !== "name" ? `<span class="ellipsis">${__(result[column])}</span>`
					: `<a class="list-id ellipsis">
						${__(result[column])}</a>`)
			}
		</div>`;
	});

	let $row = $(`<div class="list-item">
		<div class="list-item__content" style="flex: 0 0 10px;">
			<input type="checkbox" class="list-row-check" ${result.checked ? 'checked' : ''}>
		</div>
		${contents}
	</div>`);

	$row = list_row_data_items(head, $row, result, invoice_healthcare_services);
	return $row;
};

var set_primary_action = function (frm, dialog, $results, invoice_healthcare_services) {
	var me = this;
	dialog.set_primary_action(__('Add'), function () {
		let checked_values = get_checked_values($results);
		if (checked_values.length > 0) {
			if (invoice_healthcare_services) {
				frm.set_value("patient", dialog.fields_dict.patient.input.value);
			}
			add_to_item_line(frm, checked_values, invoice_healthcare_services);
			dialog.hide();
		}
		else {
			if (invoice_healthcare_services) {
				frappe.msgprint(__("Please select Healthcare Service"));
			}
			else {
				frappe.msgprint(__("Please select Drug"));
			}
		}
	});
};

var get_checked_values = function ($results) {
	return $results.find('.list-item-container').map(function () {
		let checked_values = {};
		if ($(this).find('.list-row-check:checkbox:checked').length > 0) {
			checked_values['dn'] = $(this).attr('data-dn');
			checked_values['dt'] = $(this).attr('data-dt');
			checked_values['item'] = $(this).attr('data-item');
			if ($(this).attr('data-rate') != 'undefined') {
				checked_values['rate'] = $(this).attr('data-rate');
			}
			else {
				checked_values['rate'] = false;
			}
			if ($(this).attr('data-income-account') != 'undefined') {
				checked_values['income_account'] = $(this).attr('data-income-account');
			}
			else {
				checked_values['income_account'] = false;
			}
			if ($(this).attr('data-qty') != 'undefined') {
				checked_values['qty'] = $(this).attr('data-qty');
			}
			else {
				checked_values['qty'] = false;
			}
			if ($(this).attr('data-description') != 'undefined') {
				checked_values['description'] = $(this).attr('data-description');
			}
			else {
				checked_values['description'] = false;
			}
			if ($(this).attr('data-discount-percentage') != 'undefined') {
				checked_values['discount_percentage'] = $(this).attr('data-discount-percentage');
			}
			else {
				checked_values['discount_percentage'] = false;
			}
			if ($(this).attr('data-insurance-claim-coverage') != 'undefined') {
				checked_values['insurance_claim_coverage'] = $(this).attr('data-insurance-claim-coverage');
			}
			else {
				checked_values['insurance_claim_coverage'] = false;
			}
			if ($(this).attr('data-insurance-claim') != 'undefined') {
				checked_values['insurance_claim'] = $(this).attr('data-insurance-claim');
			}
			else {
				checked_values['insurance_claim'] = false;
			}
			return checked_values;
		}
	}).get();
};

var get_drugs_to_invoice = function (frm) {
	var me = this;
	let selected_encounter = '';
	var dialog = new frappe.ui.Dialog({
		title: __("Get Items From Prescriptions"),
		fields: [
			{ fieldtype: 'Link', options: 'Patient', label: 'Patient', fieldname: "patient", reqd: true },
			{
				fieldtype: 'Link', options: 'Patient Encounter', label: 'Patient Encounter', fieldname: "encounter", reqd: true,
				description: 'Quantity will be calculated only for items which has "Nos" as UoM. You may change as required for each invoice item.',
				get_query: function (doc) {
					return {
						filters: {
							patient: dialog.get_value("patient"),
							company: frm.doc.company,
							docstatus: 1
						}
					};
				}
			},
			{ fieldtype: 'Section Break' },
			{ fieldtype: 'HTML', fieldname: 'results_area' }
		]
	});
	var $wrapper;
	var $results;
	var $placeholder;
	dialog.set_values({
		'patient': frm.doc.patient,
		'encounter': ""
	});
	dialog.fields_dict["encounter"].df.onchange = () => {
		var encounter = dialog.fields_dict.encounter.input.value;
		if (encounter && encounter != selected_encounter) {
			selected_encounter = encounter;
			var method = "hms_tz.hms_tz.utils.get_drugs_to_invoice";
			var args = { encounter: encounter };
			var columns = (["drug_code", "quantity", "description"]);
			get_healthcare_items(frm, false, $results, $placeholder, method, args, columns);
		}
		else if (!encounter) {
			selected_encounter = '';
			$results.empty();
			$results.append($placeholder);
		}
	};
	$wrapper = dialog.fields_dict.results_area.$wrapper.append(`<div class="results"
		style="border: 1px solid #d1d8dd; border-radius: 3px; height: 300px; overflow: auto;"></div>`);
	$results = $wrapper.find('.results');
	$placeholder = $(`<div class="multiselect-empty-state">
				<span class="text-center" style="margin-top: -40px;">
					<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
					<p class="text-extra-muted">No Drug Prescription found that are prescribed</p>
				</span>
			</div>`);
	$results.on('click', '.list-item--head :checkbox', (e) => {
		$results.find('.list-item-container .list-row-check')
			.prop("checked", ($(e.target).is(':checked')));
	});
	set_primary_action(frm, dialog, $results, false);
	dialog.show();
};

var list_row_data_items = function (head, $row, result, invoice_healthcare_services) {
	if (invoice_healthcare_services) {
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-dn= "${result.reference_name}" data-dt= "${result.reference_type}" data-item= "${result.service}"
				data-rate = ${result.rate}
				data-income-account = "${result.income_account}"
				data-qty = ${result.qty}
				data-description = "${result.description}"
				data-discount-percentage = ${result.discount_percentage}
				data-insurance-claim-coverage = ${result.insurance_claim_coverage}
				data-insurance-claim = ${result.insurance_claim}>
				</div>`).append($row);
	}
	else {
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-item= "${result.drug_code}"
				data-qty = ${result.quantity}
				data-description = "${result.description}">
				</div>`).append($row);
	}
	return $row;
};

var add_to_item_line = function (frm, checked_values, invoice_healthcare_services) {
	if (invoice_healthcare_services) {
		frappe.call({
			method: "hms_tz.nhif.api.healthcare_utils.set_healthcare_services",
			args: {
				doc: frm.doc,
				checked_values: checked_values
			},
			callback: function (r) {
				frm.trigger("validate");
				frm.refresh_fields();
				if (frm.is_new()) {
					frappe.set_route('Form', 'Sales Invoice', r.message);
				} else {
					frm.reload_doc();
				}
			}
		});
	}
	else {
		for (let i = 0; i < checked_values.length; i++) {
			var si_item = frappe.model.add_child(frm.doc, 'Sales Invoice Item', 'items');
			frappe.model.set_value(si_item.doctype, si_item.name, 'item_code', checked_values[i]['item']);
			frappe.model.set_value(si_item.doctype, si_item.name, 'qty', 1);
			if (checked_values[i]['qty'] > 1) {
				frappe.model.set_value(si_item.doctype, si_item.name, 'qty', parseFloat(checked_values[i]['qty']));
			}
		}
		frm.refresh_fields();
	}
};

var show_disocunt_dialog = (frm) => {
	let dialog = new frappe.ui.Dialog({
		title: __("Patient Discount Request"),
		fields: [
			{
				fieldname: "apply_discount_on",
				label: __("Apply Discount On"),
				fieldtype: "Select",
				options: "\nGrand Total\nNet Total\nSingle Items", //\nGroup of Items
				reqd: 1,
			},
			{
				fieldname: "item_category",
				label: __("Item Category"),
				fieldtype: "Select",
				options: "\nAll Items\nAll OPD Consultations\nAll Lab Prescriptions\nAll Radiology Procedure Prescription\nAll Procedure Prescriptions\nAll Therapy Plan Details\nAll Drug Prescriptions\nAll Other Items",
				depends_on: "eval:doc.apply_discount_on == 'Group of Items'",
				mandatory_depends_on: "eval:doc.apply_discount_on == 'Group of Items'",
			},
			{
				fieldname: "grand_total",
				label: __("Grand Total"),
				fieldtype: "Float",
				read_only: 1,
				hidden: 1,
			},
			{
				fieldname: "net_total",
				label: __("Net Total"),
				fieldtype: "Float",
				read_only: 1,
				hidden: 1,
			},
			{
				fieldname: "dc_cb",
				label: "",
				fieldtype: "Column Break",
			},
			{
				fieldname: "discount_criteria",
				label: __("Discount Criteria"),
				fieldtype: "Select",
				options: "\nDiscount Based on Percentage\nDiscount Based on Actual Amount",
				reqd: 1,
			},
			{
				fieldname: "discount_percent",
				label: __("Discount (%)"),
				fieldtype: "Percent",
				depends_on: "eval:doc.discount_criteria == 'Discount Based on Percentage'",
				mandatory_depends_on: "eval:doc.discount_criteria == 'Discount Based on Percentage'",
			},
			{
				fieldname: "discount_amount",
				label: __("Discount Amount"),
				fieldtype: "Float",
				depends_on: "eval:doc.discount_criteria == 'Discount Based on Actual Amount'",
				mandatory_depends_on: "eval:doc.discount_criteria == 'Discount Based on Actual Amount'",
			},
			{
				fieldname: "reason_sec",
				label: "",
				fieldtype: "Section Break",
			},
			{
				fieldname: "discount_reason",
				label: __("Discount Reason"),
				fieldtype: "Small Text",
				reqd: 1,
				description: __("Reason to why patient is requesting for a discount"),
			},
			{
				fieldname: "items_sec",
				label: "",
				fieldtype: "Section Break",
			},
			{
				fieldname: "items",
				label: __("Items"),
				fieldtype: "HTML",
			}
		],
	});
	let wrapper = dialog.fields_dict.items.$wrapper;
	dialog.fields_dict.apply_discount_on.df.onchange = () => {
		if (dialog.fields_dict.apply_discount_on.get_value() == "Grand Total") {
			dialog.set_df_property("net_total", "hidden", 1);
			dialog.set_value("net_total", 0);
			dialog.set_value("grand_total", frm.doc.grand_total);
			dialog.set_df_property("grand_total", "hidden", 0);
		} else if (dialog.fields_dict.apply_discount_on.get_value() == "Net Total") {
			dialog.set_df_property("grand_total", "hidden", 1);
			dialog.set_value("grand_total", 0);

			dialog.set_value("net_total", frm.doc.net_total);
			dialog.set_df_property("net_total", "hidden", 0);
		} else if (dialog.fields_dict.apply_discount_on.get_value() == "Single Items") {
			dialog.set_values({
				"grand_total": 0,
				"net_total": 0
			});
			dialog.set_df_property("grand_total", "hidden", 1);
			dialog.set_df_property("net_total", "hidden", 1);

			if (dialog.get_value("discount_percent") > 0 || dialog.get_value("discount_amount") > 0) {
				get_discount_data(frm, dialog, wrapper);
			}

		} else if (dialog.fields_dict.apply_discount_on.get_value() == "Group of Items") {
			dialog.set_values({
				"grand_total": 0,
				"net_total": 0
			});
			dialog.set_df_property("grand_total", "hidden", 1);
			dialog.set_df_property("net_total", "hidden", 1);

			// get_discount_data(frm, dialog, wrapper);
		}
	}
	dialog.fields_dict.discount_percent.df.onchange = () => {
		if (dialog.fields_dict.discount_percent.get_value() > 0) {
			dialog.set_value("discount_amount", 0);
			if (dialog.fields_dict.apply_discount_on.get_value() == "Single Items") {
				get_discount_data(frm, dialog, wrapper);
			}
		}
	};
	dialog.fields_dict.discount_amount.df.onchange = () => {
		if (dialog.fields_dict.discount_amount.get_value() > 0) {
			dialog.set_value("discount_percent", 0);
			if (dialog.fields_dict.apply_discount_on.get_value() == "Single Items") {
				get_discount_data(frm, dialog, wrapper);
			}
		}
	};

	set_discount_action(frm, dialog, wrapper);
	dialog.$wrapper.find(".modal-dialog").css({
		"width": "800px",
		"max-height": "1600px",
		"overflow": "auto",
	});
	dialog.show();
};

var set_discount_action = (frm, dialog, wrapper) => {
	dialog.set_primary_action(__("Request Discount"), () => {
		let data = dialog.get_values();
		console.log(data);

		if (dialog.get_value("apply_discount_on") == "Single Items") {
			let items = [];

			wrapper.find('tr:has(input:checked)').each(function () {
				if ($(this).find("#th").is(":checked")) {
					return;
				}
				items.push({
					reference_dt: $(this).find("#reference_dt").attr("data-reference_dt"),
					item_code: $(this).find("#item_code").attr("data-item_code"),
					actual_price: $(this).find("#amount").attr("data-amount"),
					discount_amount: $(this).find("#discounted_amount").attr("data-discounted_amount"),
					amount_after_discount: $(this).find("#amount_after_discount").attr("data-amount_after_discount"),
					sales_invoice: frm.doc.name,
					si_detail: $(this).find("#si_detail").attr("data-si_detail"),
				});
			});

			if (items.length > 0) {
				get_patient_discount_request(frm, data, items);
				dialog.hide();

			} else {
				frappe.msgprint({
					title: __('Message'),
					indicator: 'red',
					message: __(
						'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
								No any Item selected<h4>'
					)
				});
			}
		} else {
			get_patient_discount_request(frm, data);
			dialog.hide();
		}
	});
};

var get_discount_data = (frm, dialog, wrapper) => {
	wrapper.html("");

	return frappe.call({
		method: "hms_tz.nhif.api.sales_invoice.get_discount_items",
		args: {
			invoice_no: frm.doc.name,
		}
	}).then(r => {
		const results = r.message;
		if (results.length > 0) {
			let html = show_disocunt_details(dialog, results);
			wrapper.html(html);

			$("#th").on("click", function () {
				if ($(this).is(":checked")) {
					wrapper.find("input[type='checkbox']").prop("checked", true);
				} else {
					wrapper.find("input[type='checkbox']").prop("checked", false);
				}
			});
		} else {
			wrapper.append(`<div class="multiselect-empty-state"
				style="border: 1px solid #d1d8dd; border-radius: 3px; height: 200px; overflow: auto;">
				<span class="text-center" style="margin-top: -40px;">
					<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
					<p class="text-extra-muted text-center" style="font-size: 16px; font-weight: bold;">
					No Item(s) requested</p>
				</span>
			</div>`);
		}
	});
};

var show_disocunt_details = (dialog, data) => {
	let html = `<table class="table table-hover" style="width:100%;">
		<colgroup>
			<col width="5%">
			<col width="25%">
			<col width="30%">
			<col width="10%">
			<col width="10%">
			<col width="15%">
			<col width="5%">
		</colgroup>
		<tr>
			<th><input type="checkbox" id="th" /></th>
			<th style="background-color: #D3D3D3;">Ref Doctype</th>
			<th style="background-color: #D3D3D3;">Item Code</th>
			<th style="background-color: #D3D3D3;">Amount</th>
			<th style="background-color: #D3D3D3;">Discount Amount</th>
			<th style="background-color: #D3D3D3;">Amount After Discount</th>
			<th style="background-color: #D3D3D3;"></th>
		</tr>`;

	data.forEach(row => {
		let discount_amount = 0
		if (dialog.get_value("discount_percent") > 0) {
			discount_amount = row.amount * (dialog.get_value("discount_percent") / 100);
		} else if (dialog.get_value("discount_amount") > 0) {
			discount_amount = dialog.get_value("discount_amount");

		}
		let amount_after_discount = row.amount - discount_amount;
		let reference_dt = row.reference_dt ? row.reference_dt : "";

		html += `<tr>
			<td><input type="checkbox"/></td>
			<td id="reference_dt" data-reference_dt="${reference_dt}">${reference_dt}</td>
			<td id="item_code" data-item_code="${row.item_code}">${row.item_code}</td>
			<td id="amount" data-amount="${parseFloat(row.amount).toFixed(2)}">${parseFloat(row.amount).toFixed(2)}</td>
			<td id="discounted_amount" data-discounted_amount="${parseFloat(discount_amount).toFixed(2)}">${parseFloat(discount_amount).toFixed(2)}</td>
			<td id="amount_after_discount" data-amount_after_discount="${parseFloat(amount_after_discount).toFixed(2)}">${parseFloat(amount_after_discount).toFixed(2)}</td>
			<td class="d-none" id="si_detail" data-si_detail="${row.name}">${row.name}</td>
		</tr>`;
	});
	html += `</table>`;
	return html;
};

var get_patient_discount_request = (frm, data, items = null) => {
	data["patient"] = frm.doc.patient;
	data["patient_name"] = frm.doc.patient_name;
	data["customer"] = frm.doc.customer;
	data["company"] = frm.doc.company;
	data["items"] = items;
	data["sales_invoice"] = frm.doc.name;
	data["payment_type"] = "Cash";

	frappe.dom.freeze(__("Please wait..."));
	return frappe.call({
		method: "hms_tz.nhif.doctype.patient_discount_request.patient_discount_request.get_patient_discount_request",
		args: {
			data: data,
		}
	}).then(r => {
		if (r.message) {
			frappe.dom.unfreeze();
			frappe.msgprint({
				title: __("Message"),
				indicator: "green",
				message: __(
					"<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
						Discount Request created successfully<h4>"
				)
			});
		} else {
			frappe.dom.unfreeze();
			frappe.msgprint({
				title: __("Message"),
				indicator: "red",
				message: __(
					"<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
						Discount Request failed to create<h4>"
				)
			});
		}
	});
};