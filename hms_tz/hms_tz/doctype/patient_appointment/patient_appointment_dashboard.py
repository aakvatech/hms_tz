from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'appointment',
		'non_standard_fieldnames': {
			'AV Patient Medical Record': 'reference_name'
		},
		'transactions': [
			{
				'label': _('Consultations'),
				'items': ['Patient Encounter', 'Vital Signs', 'AV Patient Medical Record']
			}
		]
	}
