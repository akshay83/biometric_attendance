import frappe
import datetime
from frappe.utils import cint,  get_time, split_emails

def get_time_difference_in_minutes(timeA, timeB):
	dateTimeA = datetime.datetime.combine(datetime.date.today(), timeA)
	dateTimeB = datetime.datetime.combine(datetime.date.today(), timeB)
	return (dateTimeA-dateTimeB).total_seconds() / 60

@frappe.whitelist()
def auto_import(manual_import=0, machine_name=None):
	if not machine_name:
		machines = frappe.get_all("Biometric Machine")
		for m_name in machines:
			auto_import_for_machine(machine_name=m_name, manual_import=manual_import)
	else:
		auto_import_for_machine(machine_name=machine_name, manual_import=manual_import)

def auto_import_for_machine(machine_name=None, manual_import=0):
	if not machine_name:
		return

	now_time = datetime.datetime.now().time()
	today_date = datetime.date.today()

	m = frappe.get_doc("Biometric Machine", machine_name)

	minute_diff = get_time_difference_in_minutes(get_time(now_time), get_time(m.import_at))
	if (cint(m.auto_import_enabled) and m.last_import_on != today_date \
		and abs(minute_diff) <=10) or cint(manual_import):
		do_auto_import(m, manual_import)

def do_auto_import(machine, manual_import=0):
	from utils import import_attendance, clear_machine_attendance
	try:
		import_attendance(machine.name)
		if cint(machine.clear_after_import):
			clear_machine_attendance(machine.name)
		machine.last_import_on = datetime.date.today()
		machine.save()
		if not cint(manual_import):
			send_email(success=True, machine=machine)
	except Exception as e:
		if not cint(manual_import):
			send_email(success=False, machine=machine, error_status=e)
		else:
			frappe.throw(e)

def send_email(success, machine, error_status=None):
	if not cint(machine.send_notification):
		return

	if success:
		subject = "Attendance Import Successful - {0}".format(machine.name)
		message ="""<h3>Attendance Imported Successfully</h3><p>Hi there, this is just to inform you
		that your attendance have been successfully imported.</p>"""
	else:
		subject = "[Warning] Attendance Import Failed - {0}".format(machine.name)
		message ="""<h3>Attendance Import has Failed</h3><p>Oops, your automated attendance Import has Failed</p>
		<p>Error message: <br>
		<pre><code>%s</code></pre>
		</p>
		<p>Please contact your system manager for more information.</p>
		""" % (error_status)

	recipients = split_emails(machine.notification_mail_address)
	frappe.sendmail(recipients=recipients, subject=subject, message=message)
