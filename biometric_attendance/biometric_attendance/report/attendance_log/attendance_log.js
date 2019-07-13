frappe.query_reports["Attendance Log"] = {
	"filters": [
		{
		  "fieldname": "from_date",
		  "fieldtype": "Date",
		  "label": "From Date",
		  "default": get_today()
		},
		{
		  "fieldname": "to_date",
		  "fieldtype": "Date",
		  "label": "To Date",
		  "default": get_today()
		},
		{
		  "fieldname": "user",
		  "fieldtype": "Link",
		  "label": "User",
		  "options": "Biometric Users",
		  "reqd": 1,
		  "on_change": function() {
			var user = frappe.query_report_filters_by_name.user.get_value();
			if (user) {
				frappe.db.get_value("Biometric Users", user, "user_name", function(value) {
					frappe.query_report_filters_by_name.user_name.set_value(value["user_name"]);
				});
			}
		  }
		},
		{
		  "fieldname": "user_name",
		  "fieldtype": "Data",
		  "label": "User Name",
		  "read_only": 1
		}
	]
}
