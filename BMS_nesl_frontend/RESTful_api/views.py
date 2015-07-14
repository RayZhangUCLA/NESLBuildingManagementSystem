from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.exceptions import MultipleObjectsReturned	
from data_visualization.models import Menu_Tree, Path_UUID
from influxdb.influxdb08 import InfluxDBClient
from datetime import datetime
import urllib, urllib2, json, time
import traceback

# RESTful API:
# 	Path
# 	UUID
# 	Properties: unit, location, timezone
# 	data
# 	statistics: avg, sum
# The usage is as follows: http://ip:port/api/(types,eg:Path,UUID,data,Properties)?uuid=''(&Path=''&starttme=''&endtime='')


def get_resp_from_server(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	return json.loads(resp)

def get_resp_from_server_wo_load_json(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	return resp

def get_sign(num):
	if num >= 0:
		return 1
	else:
		return -1

def get_nearest_timestamp(time): #finest granularity is 15 minutes(determined by influxDB)
	datetime_str = str(datetime.fromtimestamp(time))
	minute = int(datetime_str[14:16])
	seconds = int(datetime_str[17:19])
	time = time - seconds
	if minute <= 15:
		diff = get_sign(minute - 15/2) * min(minute, 15-minute)
	elif minute <= 30:
		diff = get_sign(minute - 45/2) * min(minute-15, 30-minute)
	elif minute <= 45:
		diff = get_sign(minute - 75/2) * min(minute-30, 45-minute)
	elif minute < 60:
		diff = get_sign(minute - 105/2) * min(minute-45, 60-minute)
	else:
		pass
	return time + diff*60

def index(request):
	reply = {}
	reply['content'] = ["path", "uuid", "properties", "data", "statistics"]
	return HttpResponse(json.dumps(reply))

def Path(request):
	reply = {}
	path = []
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
		try:
			p_u = Path_UUID.objects.get(uuid=uuid) 
			path.append(p_u.path)
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(uuid=uuid).values()
			for p_u in p_us:
				path.append(p_u['path'])
		reply['uuid'] = uuid
		reply['path'] = path
	else:
		p_us = Path_UUID.objects.all().values()
		for p_u in p_us:
			if not p_u['path'].startswith("/NE"): #paths starting with /NESL are deprecated
				path.append(p_u['path'])
				
		reply['path'] = path
	return HttpResponse(json.dumps(reply))

def UUID(request):
	reply = {}
	uuid = []
	if 'path' in request.GET:
		path = request.GET['path']
		try:
			p_u = Path_UUID.objects.get(path=path) 
			uuid.append(p_u.uuid)
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(path=path).values()
			for p_u in p_us:
				uuid.append(p_u['uuid'])
		reply['uuid'] = uuid
		reply['path'] = path
	else:
		p_us = Path_UUID.objects.all().values()
		for p_u in p_us:
			uuid.append(p_u['uuid'])
		reply['uuid'] = uuid
	return HttpResponse(json.dumps(reply))

def Properties(request):
	url =  request.path
	stream_property = url.split("/")[3:]
	if stream_property:
		stream_property = stream_property[0]
	resp = {}
	uuid = ""
	path = ""
	try:
		if 'uuid' in request.GET:
			uuid = request.GET['uuid']
			request_url = "http://localhost:8079/api/tags/uuid/" + uuid
			tags = get_resp_from_server(request_url)[0]
			if stream_property == "unit":
				resp['unit'] = tags['Properties']['UnitofMeasure']
			elif stream_property == "timezone":
				resp['timezone'] = tags['Properties']['Timezone']
			elif stream_property == "location":
				resp['location'] =tags['Metadata']['Location']
			else:
				resp['unit'] = tags['Properties']['UnitofMeasure']
				resp['timezone'] = tags['Properties']['Timezone']
				resp['location'] = tags['Metadata']['Location']
		elif 'path' in request.GET:
			path = request.GET['path']
			uuid = Path_UUID.objects.get(path=path).uuid
			request_url = "http://localhost:8079/api/tags/uuid/" + uuid
			tags = get_resp_from_server(request_url)[0]
			if stream_property == "unit":
				resp['unit'] = tags['Properties']['UnitofMeasure']
			elif stream_property == "timezone":
				resp['timezone'] = tags['Properties']['Timezone']
			elif stream_property == "location":
				resp['location'] = tags['Metadata']['Location']
			else:
				resp['unit'] = tags['Properties']['UnitofMeasure']
				resp['timezone'] = tags['Properties']['Timezone']
				resp['location'] = tags['Metadata']['Location']
		else:
			if stream_property == "unit":
				request_url = "http://localhost:8079/api/query/Properties__UnitofMeasure"
				resp = get_resp_from_server(request_url)
			elif stream_property == "timezone":
				request_url = "http://localhost:8079/api/query/Properties__Timezone"
				resp = get_resp_from_server(request_url)
			elif stream_property == "location":
				resp = {}
				request_url = "http://localhost:8079/api/query/Metadata__Location__Building"
				resp['Building'] = get_resp_from_server(request_url)
				request_url = "http://localhost:8079/api/query/Metadata__Location__City"
				resp['City'] = get_resp_from_server(request_url)
				request_url = "http://localhost:8079/api/query/Metadata__Location__State"
				resp['State'] = get_resp_from_server(request_url)
			else:
				resp['content'] = ["unit", "timezone", "location"]
	except:
		raise Http404
	return HttpResponse(json.dumps(resp))

def Data(request): 
	#timestamp should be in millionsecond
	if 'endtime' not in request.GET:
		endtime = str(int(time.time()*1000))
	else:
		endtime = request.GET['endtime']
	if 'starttime' not in request.GET:
		starttime = str(int(endtime) - 24*60*60*1000)
	else:
		starttime = request.GET['starttime']
	request_url = ""
	try:
		if 'uuid' in request.GET:
			uuid = request.GET['uuid']
			request_url = "http://localhost:8079/api/data/uuid/" + uuid + "?starttime=" + starttime + "&endtime=" + endtime
		elif 'path' in request.GET:
			path = request.GET['path']
			uuid = Path_UUID.objects.get(path=path).uuid
			request_url = "http://localhost:8079/api/data/uuid/" + uuid + "?starttime=" + starttime + "&endtime=" + endtime
		else:
			request_url = "http://localhost:8079/api/data?starttime=" + starttime + "&endtime=" + endtime
	except:
		raise Http404
	return HttpResponse(get_resp_from_server_wo_load_json(request_url))

def Statistics(request):
	#timestamp should be in millionsecond
	url =  request.path
	statistics_type = url.split("/")[3:]
	reply = {}
	if not statistics_type:
		reply['content'] = ["avg", "sum"]
		return HttpResponse(json.dumps(reply))
	else:
		statistics_type = statistics_type[0]

	print "in statistics"
	if 'endtime' not in request.GET: #in ms
		endtime = int(time.time()*1000)
	else:
		endtime = int(request.GET['endtime'])
	print endtime
	if 'starttime' not in request.GET: #in ms
		starttime = int(endtime) - 24*60*60*1000
	else:
		starttime = int(request.GET['starttime'])
	print starttime
	reply['starttime'] = starttime
	reply['endtime'] = endtime
	try:
		if 'uuid' in request.GET:
			uuid = request.GET['uuid']
			data_type = Path_UUID.objects.get(uuid=uuid).data_type
		elif 'path' in request.GET:
			path = request.GET['path']
			uuid = Path_UUID.objects.get(path=path).uuid
			data_type = Path_UUID.objects.get(uuid=uuid).data_type
		else:
			return HttpResponse("Please specify uuid or path for data stream you want")
		# uuid = "782c5441-331a-5ed7-9575-65aa726c165a"
		starttime = get_nearest_timestamp(starttime/1000) #in sec
		endtime = get_nearest_timestamp(endtime/1000) #in sec
		print starttime, endtime
		#query influxDB
		timeDB = InfluxDBClient('localhost', '8051', 'your username', 'your password', 'your influxdb stream')
		sql_query = "select * from \""+uuid+"\" where time > "+str(starttime-60) +"s and time < "+str(endtime+60)+"s"
		print sql_query
		result = timeDB.query(sql_query)
		# print result
		if result:
			points = result[0]['points']
		else:
			points = []
		print "influxDB data obtained"
		if data_type != 0:
			if 'interval' not in request.GET:
				interval = 15 #minute
			else:
				interval = float(request.GET['interval'])
			summation = 0
			for point in points:
				summation += point[2]
			if statistics_type == 'avg':
				num_time = float((endtime - starttime))/(interval*60)
				result = summation/num_time
			elif statistics_type == 'sum':
				result = summation
			else:
				pass
		else:
			summation = 0
			counter = 0
			for point in points:
				counter += point[2]
				summation += point[3]
			if statistics_type == 'avg':
				result = summation/counter
			elif statistics_type == 'sum':
				result = summation
			else:
				pass
	except Exception, err:
		print traceback.format_exc()
		raise Http404	
	reply['uuid'] = uuid
	reply[statistics_type] = result
	if statistics_type == 'avg' and data_type != 0:
		reply['time interval'] = int(interval)
	return HttpResponse(json.dumps(reply))