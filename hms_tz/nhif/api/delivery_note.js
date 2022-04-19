frappe.ui.form.on('Delivery Note', {
    refresh: (frm) => {
    }
});

frappe.ui.form.on('Original Delivery Note Item', {
    form_render: (frm, cdt, cdn) => {
        $('[data-fieldname="convert_to_in_stock_item"]')
            .addClass('align-middle font-weight-bold border-light').css({
                'font-size': '16px', 'background-color': 'green', 'color': '#FFF',
                'border': '7px', 'border-radius': '12px', 'cursor': 'pointer',
                'width': '220px', 'height': '30px'
            });
        frm.set_df_property('convert_to_in_stock_item', 'read_only', 0);
    },

    convert_to_in_stock_item: (frm, cdt, cdn) => {
        if (locals[cdt][cdn].hms_tz_is_out_of_stock == 1) {
            frappe.call('hms_tz.nhif.api.delivery_note.convert_to_instock_item', {
                name: frm.doc.name, row: locals[cdt][cdn]
            }).then(r => {
                if (r.message) {
                    frm.refresh();
                }
            });
        } else {
            frappe.msgprint('This Item is not out of stock');
        }
    }
});
