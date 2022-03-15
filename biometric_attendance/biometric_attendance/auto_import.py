import frappe
import datetime
import time
from frappe.utils import cint,  get_time, split_emails

def get_all_machine_autoimport_info():
	machines = frappe.get_all("Biometric Machine", filters=[{"auto_import_enabled":('=',1)}], \
								fields=["name","import_at","last_import_on"])	
	return machines

def was_last_retry(machine, retries):
	current_retry = retries.get(machine)
	if current_retry > 3:
		return True
	else:
		retries.update({machine:current_retry + 1})
		return False

@frappe.whitelist()
def auto_import(manual_import=0, machine_name=None):
	if not machine_name:
		retries = {}
		do_later = []
		machine_names = get_all_machine_autoimport_info()
		for m_name in machine_names:
			retries.update({m_name["name"]:retries.get(m_name["name"],0)})			
			success, error = do_auto_import(machine=frappe.get_doc("Biometric Machine",m_name["name"]), manual_import=manual_import)
			if not cint(manual_import) and not success:
				if m_name not in do_later:
					do_later.append(m_name["name"])
				retries.update({m_name["name"]:1})
		do_later_queue(do_later, retries)
	else:
		success, error = do_auto_import(machine=frappe.get_doc("Biometric Machine",machine_name), manual_import=manual_import)

def do_later_queue(do_later, retries):
	if not do_later or len(do_later)<=0:
		return
	for machinename in do_later:
		success, error = do_auto_import(machine=frappe.get_doc("Biometric Machine",machinename), manual_import=manual_import)
		if success:
			do_later.remove(machinename)
		elif was_last_retry(machinename, retries):
			send_email(success=False, machine=machine, error_status=error)
			do_later.remove(machinename)
	if do_later and len(do_later) > 0:
		time.sleep(300)
		do_later_queue(do_later)

def do_auto_import(machine, manual_import=0, verbose=True):
	from .utils import import_attendance, clear_machine_attendance

	if not machine:
		return False

	try:
		import_attendance(machine.name)
		if cint(machine.clear_after_import):
			clear_machine_attendance(machine.name)
		machine.last_import_on = datetime.date.today()
		machine.save()
		if not cint(manual_import):
			send_email(success=True, machine=machine)
		return True, None
	except Exception as e:
		if cint(manual_import) and verbose:
			frappe.throw(e)
		return False, e

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
