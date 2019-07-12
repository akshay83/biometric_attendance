// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Monthly Attendance"] = {
	"filters": [
		{
			"fieldname":"date_range",
			"label": __("Date Range"),
			"fieldtype": "DateRange",
			"default": [frappe.datetime.add_months(frappe.datetime.get_today(),-1), frappe.datetime.get_today()],
			"reqd": 1
		},
		{
			"fieldname":"machine",
			"label": "Machine",
			"fieldtype": "Link",
			"options": "Biometric Machine",
			"reqd": 1
		},
		{
			"fieldname":"detailed_view",
			"label": "Detailed View",
			"fieldtype": "Check",
			"default": 0
		}
	]
}
