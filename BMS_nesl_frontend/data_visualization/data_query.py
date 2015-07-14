import sqlite3

def get_conn():
	conn = sqlite3.dbapi2.connect("/home/ray/sources/Django_frontend/BMS_nesl_frontend/dashboard.db")
	return conn

def get_db_query(uuid, length, db):
	conn = get_conn()
	curs = conn.cursor()
	if db == "hours":
		curs.execute("SELECT (hour_time+0.5)*60*60*1000, hour_total/3600 FROM (SELECT * FROM week_hourly_totals WHERE uuid=? ORDER BY hour_time DESC LIMIT ?) ORDER BY hour_time ASC", (uuid, length))
	elif db == "days":
		curs.execute("SELECT (day_num+0.5)*24*60*60*1000, day_total/86400 FROM (SELECT * FROM day_totals WHERE uuid=? ORDER BY day_num DESC LIMIT ?) ORDER BY day_num ASC", (uuid, length))
	else:
		print "ERROR: no db", db
		raise Exception
	res = curs.fetchall()
	print res
	return res

#def get_all_hour_query(uuid=None):
#	conn = get_conn()
#	curs = conn.get_cursor()
#	if uuid is None:
#		curs.execute("SELECT * FROM week_hourly_totals")
#	else:
#		curs.execute("SELECT * FROM week_hourly_totals WHERE uuid=?", uuid)
#	return curs.fetchall()
#
#def get_hour_query(uuid, num_hours):
#	conn = get_conn()
#	curs = conn.get_cursor()
#	if num_hours > 7*24:
#		print "ERROR: We only have 1 week worth of hours"
#		raise Exception
#	curs.execute("SELECT * FROM week_hourly_totals ORDER BY hour_time DESC WHERE uuid = ? LIMIT ?", (uuid, num_hours))
#	return curs.fetchall()
#	
#
#def get_day_query(uuid, num_days):
#	pass
	
