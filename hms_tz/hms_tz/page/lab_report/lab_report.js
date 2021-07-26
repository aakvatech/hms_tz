frappe.pages['lab-report'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Lab Report',
		single_column: true
	});

	frappe.lab_report.make(page);
	frappe.lab_report.run();

	setInterval(function () {
		window.location.reload();
	}, 30000);
}

frappe.lab_report = {
	make: function (page) {
		var me = frappe.lab_report;
		me.page = page;
		me.body = $('<div></div>').appendTo(me.page.main);
	},
	run: function () {
		var me = frappe.lab_report;
		frappe.call({
			method: 'hms_tz.hms_tz.page.lab_report.lab_report.get_data',
			callback: function (r) {
				if (r.message) {
					let context = {}
					context.data = r.message
					$(frappe.render_template("my_html", context)).appendTo(me.body);

				}
			}
		});
	},
}