# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import timedelta
from frappe.utils import getdate, cint

def execute(filters=None):
	columns, data = [], []

	if filters.get("date_range"):
		filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	else:
		return

	columns = get_columns(filters)

	return columns, data

def get_columns(filters):
	columns = [
			{
			  "fieldname": "user_code",
			  "fieldtype": "Link",
			  "options": "Biometric Users",
			  "label": "User Code",
			  "width": 100
			},
			{
			  "fieldname": "user_name",
			  "fieldtype": "Data",
			  "label": "User Name",
			  "width": 100
			},
			{
			  "fieldname": "branch",
			  "fieldtype": "Data",
			  "label": "Branch",
			  "width": 100
			}
	]

	days = getdate(filters.get("to_date")) - getdate(filters.get("from_date"))
	current_date = getdate(filters.get("from_date"))
	for n in range(0, days.days+1):
		build_key = current_date.strftime('%d-%m-%Y')
		if cint(filters.get("detailed_view")):
			ext_col = [
				{
				"fieldtype": "Int",
				"fieldname": build_key+"punch",
				"label": "Punch Count "+build_key
				},
				{
				"fieldtype": "Time",
				"fieldname": build_key+"entry",
				"label": "Entry Time "+build_key
				},
				{
				"fieldtype": "Time",
				"fieldname": build_key+"exit",
				"label": "Exit Time "+build_key
				}
			]
			columns.extend(ext_col)
		ext_col = [
			{
			"fieldtype": "Data",
			"fieldname": build_key+"attendance",
			"label": build_key
			}
		]
		columns.extend(ext_col)
		current_date += timedelta(days=1)
	return columns

def get_data(filters):
	query = """
		select
		  *,
		  case 
		     when (dump.`On Time Entry`=1 and dump.`On Time Exit`=1) then 'P'
		     when (dump.`On Time Entry`=0 and dump.`On Time Exit`=0) then 'A'
		     when (dump.`On Time Entry`=0 or dump.`On Time Exit`=0) then 'H'
		  end as `Attendance`
		from
		(select 
		  users.name as `User Code`,
		  users.user_name as `User Name`, 
		  machine.branch as `Branch`,
		  branch.opening_time as `Opening Time`,
		  branch.closing_time as `Closing Time`,
		  cast(att.timestamp as Date) as `Date`,
		  cast(min(att.timestamp) as time) as `Entry Time`,  
		  cast(max(att.timestamp) as time) as `Exit Time`,
		  count(*) as `Punch Count`,
		  if(abs(timestampdiff(MINUTE,cast(branch.opening_time as Time), cast(min(att.timestamp) as time)))<=60, 1, 0) as `On Time Entry`,
		  if(abs(timestampdiff(MINUTE,cast(branch.closing_time as Time), cast(max(att.timestamp) as time)))<=60, 1, 0) as `On Time Exit`
		from 
		  `tabBiometric Users` users, 
		  `tabBiometric Attendance` att,
		  `tabBranch Settings` branch,
		  `tabEnrolled Users` enrolled,
		  `tabBiometric Machine` machine
		where 
		  att.user_id = cast(substring(users.name,3) as Integer) 
		  and `Date` >= '{from_date}'
		  and `Date` <= '{to_date}'
		  and machine.name = '{machine_name}'
		  and machine.branch = branch.branch
		  and enrolled.parent = machine.name
		  and enrolled.user = users.name 
		group by 
		  `Date`,
		  users.name
		order by
		  `Date`,
		  users.name
		) dump
	"""

	query = query.format(**{
			"from_date":filters.get("from_date"),
			"to_date": filters.get("to_date"),
			"machine_name": filters.get("machine")
			})
