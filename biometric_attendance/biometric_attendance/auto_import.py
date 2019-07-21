import frappe
import datetime
from frappe.utils import cint,  get_time, split_emails

machine_names = None

def get_time_difference_in_minutes(timeA, timeB):
	dateTimeA = datetime.datetime.combine(datetime.date.today(), timeA)
	dateTimeB = datetime.datetime.combine(datetime.date.today(), timeB)
	return (dateTimeA-dateTimeB).total_seconds() / 60

def put_machine_name_and_time():
	global machine_names
	machine_names = []
	machines = frappe.get_all("Biometric Machine")
	for m_name in machines:
		machine_doc = frappe.get_doc("Biometric Machine", m_name.name)
		machine_names.append({
					'name': m_name.name,
					'import_at': machine_doc.import_at,
					'last_import_on': machine_doc.last_import_on,
					'import_enabled': machine_doc.auto_import_enabled,
					'retries': 0
				})
	return machine_names


def check_time_and_get_machine(machine_name):
	now_time = datetime.datetime.now().time()
	today_date = datetime.date.today()

	for m_name in machine_names:
		minute_diff = get_time_difference_in_minutes(get_time(now_time), get_time(m_name["import_at"]))
		if machine_name == m_name["name"]:
			if (cint(m_name["import_enabled"]) and m_name["last_import_on"] != today_date \
				and abs(minute_diff) <=50 and m_name["retries"] <= 3):
				return frappe.get_doc("Biometric Machine", m_name["name"])

	return None

def was_last_retry(machine):
	for m_name in machine_names:
		if m_name["name"] == machine.name:
			m_name["retries"] += 1
			if m_name["retries"] > 3:
				return True
			return False


@frappe.whitelist()
def auto_import(manual_import=0, machine_name=None):

	if not machine_names:
		put_machine_name_and_time()

	if not machine_name:
		for m_name in machine_names:
			auto_import_for_machine(machine_name=m_name["name"], manual_import=manual_import)
	else:
		auto_import_for_machine(machine_name=machine_name, manual_import=manual_import)

def auto_import_for_machine(machine_name, manual_import=0):
	if not machine_name:
		return

	if cint(manual_import):
		do_auto_import(machine=frappe.get_doc("Biometric Machine", machine_name), manual_import=1)
	else:
		do_auto_import(machine=check_time_and_get_machine(machine_name), manual_import=0)

def do_auto_import(machine, manual_import=0):
	from utils import import_attendance, clear_machine_attendance

	if not machine:
		return

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
			if was_last_retry(machine):
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
