# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class LabMachineMessage(Document):
    def validate(self):
        self.set_missing_fields()
        self.update_lab_test()

    def after_insert(self):
        self.update_lab_test()

    def set_missing_fields(self):
        if not self.message:
            return
        msg_lines = self.message.splitlines()
        self.machine_make = msg_lines[0].split('|')[2]
        self.machine_model = msg_lines[0].split('|')[3]
        self.sample_collection = msg_lines[3].split('|')[3]
        self.lab_test_name = self.get_lab_test_name(msg_lines)
    
    def get_lab_test_name(self, msg_lines):
        lab_test_name = ""
        for line in msg_lines:
            if line.startswith("OBR"):
                fields = line.split("|")
                if len(fields) > 3:
                    if fields[3] and "CBC+DIFF" in fields[3]:
                        lab_test_name = fields[3]
                        break
                    elif fields[4] and "CBC+DIFF" in fields[4]:
                        lab_test_name = fields[4]

        if lab_test_name:
            lab_test_name_exists = frappe.db.exists(
                "Lab Test", lab_test_name
            )
            if lab_test_name_exists:
                return lab_test_name

    
    def update_lab_test(self):
        if not self.message:
            return
        if not self.machine_model or not self.machine_make or not self.lab_test_name:
            return

        profile_name = self.machine_model + "-" + self.machine_make
        profile_exists = frappe.db.exists("Lab Machine Profile", profile_name)
        if not profile_exists:
            return
        profile = frappe.get_doc("Lab Machine Profile", profile_name)

        lab_test_name = profile.lab_test_prefix + self.lab_test_name
        lab_test_exists = frappe.db.exists("Lab Test", lab_test_name)
        if not lab_test_exists:
            return

        lab_test = frappe.get_doc("Lab Test", lab_test_name)
        if lab_test.docstatus != 0:
            return

        msg_lines = self.message.splitlines()
        for line in msg_lines[profile.obx_nm_start:profile.obx_nm_end]:
            test_name = line.split('|')[3].split('^')[1].replace("*", "")
            test_result = line.split('|')[5]
            lab_test_row = ""
            for row in lab_test.normal_test_items:
                if row.lab_test_name == test_name:
                    lab_test_row = row
                    break
            if lab_test_row:
                lab_test_row.result_value = test_result

        self.lab_test = lab_test_name
        lab_test.save(ignore_permissions=True)
        frappe.db.commit()
