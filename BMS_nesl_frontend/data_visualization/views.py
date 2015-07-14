from django.shortcuts import render
from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext
from data_visualization.models import Menu_Tree, Path_UUID
import urllib, urllib2, json, time, sqlite3

import smap_query
import data_query

smap_server_ip=''

# Create your views here.
def index(request):
	try:
		template = loader.get_template('data_visualization/index.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def dashboard(request):
	try:
		template = loader.get_template('data_visualization/dashboard.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_resp_from_server(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	resp = json.loads(resp)
	return resp

def get_resp_from_server_wo_load_json(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	return resp

def get_history_data_from_smap(starttime, endtime, uuid):
	request_url = "http://"+smap_server_ip+"/api/data/uuid/" + str(uuid) + "?starttime=" + str(starttime) + "&endtime=" + str(endtime)
	#get data
	#print "request_url", request_url
	resp = get_resp_from_server(request_url)
	#print "resp", resp
	data = resp[0]["Readings"]    
	return data

def get_current_data_from_smap(uuid): #returned type is float
	url = "http://"+smap_server_ip+"/api/prev/uuid/"+str(uuid) 
	#get data
	resp = get_resp_from_server(url)
	if len(resp) == 0:
		return [] 
	data = resp[0]["Readings"]    
	return data

def get_data_unit_from_smap(uuid): #returned type is float
	url = "http://"+smap_server_ip+"/api/query/uuid/"+str(uuid)+ "/Properties__UnitofMeasure"
	resp = get_resp_from_server(url)
	unit = resp[0]
	return unit

def get_house_layout_data(request):
	with sqlite3.connect("/home/ray/sources/Django_frontend/BMS_nesl_frontend/dashboard.db") as conn:
		curs = conn.cursor()
		curs.execute("SELECT description, x_coord, y_coord, tab_type, channel_units, uuid, heat_map_enable FROM house_layout WHERE heat_map_enable = 'TRUE'")
		house_layout_data = curs.fetchall()
		stream_json_arr = []
		for stream in house_layout_data:
			val = get_current_data_from_smap(stream[5])
			if len(val) == 0:
				continue
			stream_json = {"description": stream[0],
						  "x_coord": stream[1], 
						  "y_coord": stream[2],
						  "tab_type": stream[3],
						  "channel_units": stream[4],
						  "value": val[0][1],
						  "heat_map_enable": stream[6]}
			stream_json_arr.append(stream_json)
		response = HttpResponse(json.dumps(stream_json_arr))
		return response
			
def get_history_data(request):
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
	elif 'path' in request.GET:
		path = request.GET['path']
		try:
			p_u = Path_UUID.objects.get(path=path)
			uuid = p_u.uuid
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(path=reading_path).values()
			total_data = []
			p_u = p_us[-1]
			uuid = p_u['uuid']
		except:
			raise Http404
	else:
		raise Http404
	try:
		if 'endtime' not in request.GET:
			endtime = str(int(time.time()*1000))
		else:
			endtime = request.GET['endtime']
		if 'starttime' not in request.GET:
			starttime = str(int(endtime) - 24*60*60*1000)
		else:
			starttime = request.GET['starttime']
		returned_info= {}
		returned_info['data'] = get_history_data_from_smap(starttime, endtime, uuid)
		#get unit
		returned_info['unit'] = get_data_unit_from_smap(uuid)
		returned_info = json.dumps(returned_info)
	except:
		raise Http404
	return HttpResponse(returned_info)

def get_current_data(request):
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
	elif 'path' in request.GET:
		path = request.GET['path']
		try:
			p_u = Path_UUID.objects.get(path=path)
			uuid = p_u.uuid
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(path=reading_path).values()
			total_data = []
			p_u = p_us[-1]
			uuid = p_u['uuid']
		except:
			raise Http404
	else:
		raise Http404
	try:
		returned_info = {}
		returned_info['data'] = get_current_data_from_smap(uuid)
		#get unit
		returned_info['unit'] = get_data_unit_from_smap(uuid)
		returned_info = json.dumps(returned_info)
	except:
		raise Http404
	return HttpResponse(returned_info)

def calculate_proportions(readings): #[reading for uuid1, reading for uuid2,...]
	sums = 0
	for reading in readings:
		sums += reading
	if sums == 0:
		return []
	proportions = []
	for reading in readings:
		proportions.append(float(reading/sums))
	return proportions

def get_proportions(request): #assume parameters are an array of uuids [uuid1,uuid2,...], and time duration
	if 'uuids' in request.GET:
		uuids = request.GET['uuids']
		print uuids
		uuids = uuids.split(',')
		print uuids
	else:
		raise Http404
	prop_now = True
	if 'endtime' in request.GET or 'starttime' in request.GET:
		prop_now = False
		if 'endtime' not in request.GET:
			endtime = str(int(time.time()*1000))
		else:
			endtime = request.GET['endtime']
		if 'starttime' not in request.GET:
			starttime = str(int(endtime) - 24*60*60*1000)
		else:
			starttime = request.GET['starttime']
	else:
		pass

	if prop_now:
		readings = []
		for uuid in uuids:
			readings.append(get_current_data_from_smap(uuid)[0][1])
		return HttpResponse(json.dumps(calculate_proportions(readings)))
	else:
		readings = []
		for uuid in uuids:
			data = get_history_data_from_smap(starttime, endtime, uuid)
			sum = 0
			for datum in data:
				sum += datum[1]
			readings.append(sum)
		return HttpResponse(json.dumps(calculate_proportions(readings)))
	
def get_energy(request):
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
	elif 'path' in request.GET:
		path = request.GET['path']
		try:
			p_u = Path_UUID.objects.get(path=path)
			uuid = p_u.uuid
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(path=reading_path).values()
			total_data = []
			p_u = p_us[-1]
			uuid = p_u['uuid']
		except:
			raise Http404
	else:
		raise Http404

	try:
		if 'endtime' not in request.GET:
			endtime = str(int(time.time()*1000))
		else:
			endtime = request.GET['endtime']
		if 'starttime' not in request.GET:
			starttime = str(int(endtime) - 24*60*60*1000)
		else:
			starttime = request.GET['starttime']
		power_readings = get_history_data_from_smap(starttime, endtime, uuid)
		energy = 0
		for i in range(len(power_readings)-1):
			power1 = power_readings[i]
			power2 = power_readings[i+1]
			energy += (power2[0]-power1[0])/1000*power1[1]
	except:
		raise Http404
	return HttpResponse(json.dumps([energy]))

#### home dashboard added 6/14/15
def get_homeview(request):
	try:
		template = loader.get_template('data_visualization/overview_template.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_mapview(request):
	try:
		template = loader.get_template('data_visualization/mapview_template.html')
		template
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_powerTab(request):
	try:
		template = loader.get_template('data_visualization/power_template.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_waterTab(request):
	try:
		template = loader.get_template('data_visualization/water_template.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_controlTab(request):
	try:
		template = loader.get_template('data_visualization/control_template.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_control_schedulerTab(request):
	try:
		template = loader.get_template('data_visualization/control_scheduler_template.html')
		context = RequestContext(request, {})
	except:
		raise Http404
	return HttpResponse(template.render(context))

def get_smap_query(request):
	try:
		if "uuid" in request.GET and "starttime" in request.GET:
			uuid = request.GET["uuid"]
			starttime = int(request.GET["starttime"])
			endtime = int(time.time()*1000)
			if "window_unit" in request.GET:
				querytype = request.GET["window_unit"]
			else:
				querytype = "minute"
			if "window_size" in request.GET:
				width = request.GET["window_size"]
			else: 
				width = 1
			res = smap_query.get_smap_query(uuid, querytype, starttime, endtime, width)
			resp = {"data": res}
			resp = json.dumps(resp)
			return HttpResponse(resp)
		else:
			raise Http404
	except Exception as e:
		print e
		raise Http404

def get_db_query(request):
	try:
		if "uuid" in request.GET and "length" in request.GET and "db" in request.GET:
			uuid = request.GET["uuid"]
			length = int(request.GET["length"])
			db = request.GET["db"]
			print "got uuid", uuid, "length", length, "db", db
			res = data_query.get_db_query(uuid, length, db)
			print "db query returned"
			resp = {"data": res}
			resp = json.dumps(resp)
			return HttpResponse(resp)
		else:
			print "not formatted correctly"
			raise Http404
	except:
		raise Http404
		

def get_hourTotal(request):
	data_length = 0
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
		print "uuid in url: " + str(uuid)
	elif 'path' in request.GET:
		path = request.GET['path']
		try:
			p_u = Path_UUID.objects.get(path=path)
			uuid = p_u.uuid
		except MultipleObjectsReturned:
			p_us = Path_UUID.objects.filter(path=reading_path).values()
			total_data = []
			p_u = p_us[-1]
			uuid = p_u['uuid']
		except:
			print "unable to match path" + str(path)
			raise Http404
	else:
		print "invalid uuid" + uuid
		raise Http404
	try:
		cur_hr = 0
		#print cur_hr
		if 'endtime' not in request.GET:
			endtime = str(int(time.time()*1000))
			#print endtime
			cur_hr = int(time.time()/3600)
			#print "current hours: "+str(cur_hr)
		else:
			endtime = request.GET['endtime']

		if 'starttime' not in request.GET:
			starttime = str(int(cur_hr*3600*1000))
			#starttime = str(int(endtime) - 24*60*60*1000)
		else:
			starttime = request.GET['starttime']
		returned_info= {}
		returned_info['data'] = get_history_data_from_smap(starttime, endtime, uuid)
		#get unit
		returned_info['unit'] = get_data_unit_from_smap(uuid)
		#print "returned data: "
		#print returned_info['data'][0][1]
		returned_info['hourTotal']=0
		#print len(returned_info['data'])
		for x in range(len(returned_info['data'])):
			#print "value : \n"
			#print returned_info['data'][x][1]
			#print returned_info['data'][1]
			returned_info['hourTotal'] = returned_info['hourTotal'] + returned_info['data'][x][1]
		print returned_info['hourTotal']
		returned_info['hourTotal'] = returned_info['hourTotal']/1000
		#returned_info['unit_4total'] = 'kW'
		returned_info = json.dumps(returned_info)
	except:
		print "Is there live data?"
		raise Http404
	return HttpResponse(returned_info)
