// Copyright (c) 2016, ESS LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on('Medical Department', {
    refresh: function(frm) {
        frm.set_query("main_department", function(){
            return {
                filters:[
                    ["Medical Department", "is_main", "=", 1]
                ]
            };
        });
    }
});