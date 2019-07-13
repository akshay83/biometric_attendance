import frappe

@frappe.whitelist()
def get_biometric_user_name(user):
	return frappe.db.get_value("Biometric Users", { "name": user }, "user_name")

@frappe.whitelist()
def import_attendance(machine_name=None):
	if not machine_name:
		return

	from zk import ZK

	machine_doc = frappe.get_doc("Biometric Machine", machine_name)

	conn = None

	try:
		zk = ZK(machine_doc.ip_domain_address, machine_doc.port)
		conn = zk.connect()

		conn.read_sizes()
		i = 0

		attendance = conn.get_attendance()
		for a in attendance:
			attendance_doc = frappe.new_doc("Biometric Attendance")
			attendance_doc.uid = a.uid
			attendance_doc.user_id = a.user_id
			attendance_doc.timestamp = a.timestamp
			attendance_doc.punch = a.punch
			attendance_doc.status = a.status
			frappe.publish_realtime('import_biometric_attendance', dict(
						progress=i,
						total=conn.records
					))
			attendance_doc.save()
			i = i + 1

	except Exception as e:
		print e
	finally:
		if conn:
			conn.disconnect()

@frappe.whitelist()
def clear_machine_attendance(machine_name=None):
	if not machine_name:
		return

	from zk import ZK

	conn = None

	machine_doc = frappe.get_doc("Biometric Machine", machine_name)

	try:
		zk = ZK(machine_doc.ip_domain_address, machine_doc.port)

		conn = zk.connect()

		conn.clear_attendance()

	except Exception as e:
		print e
	finally:
		if conn:
			conn.disconnect()

@frappe.whitelist()
def sync_users(machine_name=None):
	if not machine_name:
		return

	from zk import ZK

	conn = None

	machine_doc = frappe.get_doc("Biometric Machine", machine_name)

	try:
		zk = ZK(machine_doc.ip_domain_address, machine_doc.port)

		conn = zk.connect()

		conn.read_sizes()

		if conn.records == 0:
			machine_users = conn.get_users()
			machine_user_ids = []
			system_user_ids = []
			for m in machine_users:
				machine_user_ids.append(m.user_id)

			for u in machine_doc.users:
				uid = unicode(int(u.user[2:]))
				system_user_ids.append(uid)

			for u in machine_doc.users:
				uid = unicode(int(u.user[2:]))
				if uid not in machine_user_ids:
					print '-------NOT FOUND IN MACHINE ------'
					print uid
					print u.user_name
					#conn.set_user(uid=uid, name=u.user_name)

			for m in machine_users:
				if m.user_id not in system_user_ids:
					print '-------NOT FOUND IN SYSTEM ------'
					print m.user_id
					print m.name
					#conn.delete_user(uid=m.user_id)

	except Exception as e:
		print e
	finally:
		if conn:
			if conn.records > 0:
				print "Attendance Records Exists"
			conn.disconnect()

@frappe.whitelist()
def delete_duplicate_rows_from_attendance():
	query = """
			delete t1 
			from 	`tabBiometric Attendance` t1 
				inner join 
				`tabBiometric Attendance` t2 
			where 
				t1.name < t2.name 
				and (t1.user_id = t2.user_id and t1.timestamp = t2.timestamp)
		"""

	return frappe.db.sql(query)
