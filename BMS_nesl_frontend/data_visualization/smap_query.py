import urllib2
import json
import time

def get_minute_avg_query(uuid, starttime, endtime, width=1):
	# def dont call this (or any of these functions) with more than a 
	# couple hour difference between start time and end time. Smap will 
	# only look at about 10,000 samples.
	return get_smap_query(uuid, "minute", starttime, endtime, width)

def get_second_avg_query(uuid, starttime, endtime, width=3):
	return get_smap_query(uuid, "second", starttime, endtime, width)

def get_smap_query(uuid, field, starttime, endtime, width=1):
	base_url = "http://128.97.93.240:8079/api/query?"
	q = "apply window(mean, field='%s', width=%d, skip_empty='True') to data in (%d, %d) where uuid = '%s'" % (field, int(width), starttime, endtime, uuid)
	fp = urllib2.urlopen(base_url, data = q)
	return json.loads(fp.read())[0]["Readings"]

if __name__ == "__main__":
	ct = int(time.time() * 1000)
	pt = ct - 3600000
	print "starttime:", pt
	print "endttime:", ct
	uuid = "6a6e1be3-2315-f849-f02c-adea4fe29099"
	print get_minute_avg_query(uuid, pt, ct)
