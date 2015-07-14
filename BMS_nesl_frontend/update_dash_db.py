import sqlite3
import time
import urllib2
import json
import sys

daily_uuids = ["6a6e1be3-2315-f849-f02c-adea4fe29099",
	"09bb4086-0335-26b2-1749-a489e7718337" ]

def get_day_data(uuid, day):
	endtime = (day+1) * 24 * 60 * 60 * 1000
	starttime = day * 24 * 60 * 60 * 1000
	url = "http://128.97.93.240:7000/data_visualization/dashboard/history_data?uuid=" + uuid + "&starttime=" + str(starttime) + "&endtime=" + str(endtime)
	print "querying",  url
	res = urllib2.urlopen(url)
	day_data = json.load(res)["data"]
	return day_data
	
def add_single_day(conn, uuid, day_num):
	print "adding day", day_num, "to", uuid
	curs = conn.cursor()
	day_data = get_day_data(uuid, day_num)
	total = 0
	for dp in day_data:
		total += dp[1]
	if total > 10000000:
		print "!!!!!!!"
		print "TOTAL IS ", total
		print "!!!!!!!"
	curs.execute("INSERT OR REPLACE INTO day_totals \
		(uuid, day_num, day_total) VALUES (?, ?, ?)",
		(uuid, day_num, total))
	conn.commit()	
	

def add_year_days(conn):
	curs = conn.cursor()
	cur_day = int(time.time() / 60 / 60 / 24)
	for uuid in daily_uuids:
		for day in range(cur_day - 365, cur_day):
			#day_data = get_day_data(uuid, day)
			#day_data_arr = np.array(day_data)
			#day_sum = np.sum(day_data_arr, 1)
			#curs.execute("INSERT INTO day_totals \
			#	(uuid, day_num, day_total)")
			add_single_day(conn, uuid, day)
			#print day

def add_yesterday(conn):
	yesterday_num = int(time.time() / 60 / 60 / 24) -1
	for uuid in daily_uuids:
		add_single_day(conn, uuid, yesterday_num)
		

def add_day_table(conn):
	curs = conn.cursor()
	curs.execute("CREATE TABLE IF NOT EXISTS day_totals ( \
		uuid VARCHAR(255) NOT NULL, \
		day_num INTEGER NOT NULL, \
		day_total FLOAT NOT NULL, \
		FOREIGN KEY (uuid) REFERENCES house_layout(uuid), \
		CONSTRAINT day_uuid_key PRIMARY KEY (uuid, day_num))")

def fill_dummy(conn):
	curs = conn.cursor()
	today_num = int(time.time() / 60 / 60 / 24)
	for uuid in daily_uuids:
		for i in range(365):
			print i
			curs.execute("INSERT INTO day_totals \
				(uuid, day_num, day_total) \
				VALUES (?, ?, ?)", (uuid, today_num - i, i*10))
	conn.commit()

def add_hour_data(conn, starthour):
	curs = conn.cursor()
	endhour = starthour + 1
	
	endtime = endhour * 3600000
	starttime = starthour * 3600000

	hour_num = starthour % (7 * 24)
	device_list = curs.execute("SELECT path, uuid FROM house_layout").fetchall()
	print "len(device_list)", len(device_list)
	print "starttime", starttime
	print "endtime", endtime
	print "starthour", starthour
	print "endhour", endhour
	for path, uuid in device_list: 
		url = "http://128.97.93.240:7000/data_visualization/dashboard/history_data?uuid=" + uuid + "&starttime=" + str(starttime) + "&endtime=" + str(endtime)
		#print "url", url
		hour_data = json.load(urllib2.urlopen(url))["data"]
		hour_total = 0
		for d in hour_data:
			hour_total += d[1] 
		# add the hour data to the database
		curs.execute("INSERT OR REPLACE INTO week_hourly_totals \
			(uuid, hour_num, hour_time, hour_total) \
			VALUES (?, ?, ?, ?)", 
			(uuid, hour_num, starthour, hour_total))

	conn.commit()

# only call this after the last full hour has passed
def add_last_hour(conn):
	curs = conn.cursor()
	# get current hour time
	endhour = int(time.time() / 3600)
	starthour = endhour - 1
	add_hour_data(conn, starthour)

def add_week_hours(conn):
	curs = conn.cursor()
	num_hours = 7 * 24
	this_hour = int(time.time() / 3600) - 1
	for i in range(num_hours):
		hour_num = this_hour - i
		print "adding hour", hour_num
		print "i", i
		add_hour_data(conn, hour_num)

def add_hour_table(conn):
	curs = conn.cursor()
	curs.execute("CREATE TABLE IF NOT EXISTS week_hourly_totals ( \
		uuid VARCHAR(255) NOT NULL, \
		hour_num INTEGER NOT NULL, \
		hour_time INTEGER NOT NULL, \
		hour_total FLOAT NOT NULL, \
		FOREIGN KEY (uuid) REFERENCES house_layout(uuid), \
		CONSTRAINT hour_uuid_key PRIMARY KEY (uuid, hour_num))")
	

if __name__ == "__main__":
	conn = sqlite3.dbapi2.connect("/home/ray/sources/Django_frontend/BMS_nesl_frontend/dashboard.db")
	try:
		for i in range(1, len(sys.argv)):
			if sys.argv[i] == "fd":
				add_day_table(conn)
				add_year_days(conn)
			elif sys.argv[i] == "pd":
				add_day_table(conn)
				add_yesterday(conn)
			elif sys.argv[i] == "fh":
				add_hour_table(conn)
				add_week_hours(conn)
			elif sys.argv[i] == "ph":
				add_hour_table(conn)
				add_last_hour(conn)
			elif sys.argv[i] == "smartp":
				add_hour_table(conn)
				add_last_hour(conn)
				h = round(time.time() / 60 / 60)
				if h % 24 == 0:
					add_day_table(conn)
					add_yesterday(conn)
			else:
				print "ERROR: command not found ", sys.argv[i]
	finally:
		conn.close()
