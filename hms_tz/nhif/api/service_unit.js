frappe.ui.form.on('Healthcare Service Unit', {
    refresh: (frm) => {
        frm.set_query('warehouse', function () {
            return {
                filters: {
                    'company': frm.doc.company,
                }
            };
        });
    }
})