frappe.listview_settings['Therapy Plan'] = {
	get_indicator: function(doc) {
		var colors = {
			'Completed': 'green',
			'In Progress': 'orange',
			'Not Started': 'red',
            'Not Serviced': 'grey',
			'Cancelled': 'red'
		};
		return [__(doc.status), colors[doc.status], 'status,=,' + doc.status];
	}
};