from django.shortcuts import render
from django.template import loader, Context
from django.http import HttpResponse, Http404
from django.core.exceptions import MultipleObjectsReturned	
from data_visualization.models import Menu_Tree, Path_UUID
from django.views.decorators.clickjacking import xframe_options_exempt
import urllib, urllib2, json, time


def get_resp_from_server(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	return json.loads(resp)

def get_resp_from_server_wo_load_json(url):
	req = urllib2.Request(url)
	resp = urllib2.urlopen(req).read()
	return resp

def index(request):
	reply = {}
	reply['content'] = ["history", "realtime"]
	return HttpResponse(json.dumps(reply))

@xframe_options_exempt
def history_plot(request):
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
		p_u = Path_UUID.objects.get(uuid=uuid)
		path = p_u.path
	elif 'path' in request.GET:
		path = request.GET['path']
		p_u = Path_UUID.objects.get(path=path)
		uuid = p_u.uuid 
	else:
		pass

	if 'width' in request.GET:
		width = int(request.GET['width'])
	else:
		width = 800
	if 'height' in request.GET:
		height = int(request.GET['height'])
	else:
		height = 600


	chart_name = path.split("/")[-1]
	request_url = "http://localhost:8079/api/tags/uuid/" + uuid
	tags = get_resp_from_server(request_url)[0]
	unit = tags['Properties']['UnitofMeasure']
	request_url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+str(int(time.time())*1000)+"&limit=300000" 
	resp = get_resp_from_server(request_url)
	data = resp[0]["Readings"] 

	#output html
	template = loader.get_template('visual_widget/widget.html')
	context = Context({"data": data, "path":path.replace("/", ",")[1:], "unit":unit, "chart_name":chart_name, "is_realtime":False,"width":width, "height": height})
	return HttpResponse(template.render(context))

@xframe_options_exempt
def realtime_plot(request):
	if 'uuid' in request.GET:
		uuid = request.GET['uuid']
		p_u = Path_UUID.objects.get(uuid=uuid)
		path = p_u.path
	elif 'path' in request.GET:
		path = request.GET['path']
		p_u = Path_UUID.objects.get(path=path)
		uuid = p_u.uuid 
	else:
		pass

	if 'width' in request.GET:
		width = int(request.GET['width'])
	else:
		width = 527
	if 'height' in request.GET:
		height = int(request.GET['height'])
	else:
		height = 400

	#get data, path, unit, chart_name
	chart_name = path.split("/")[-1]
	request_url = "http://localhost:8079/api/tags/uuid/" + uuid
	tags = get_resp_from_server(request_url)[0]
	unit = tags['Properties']['UnitofMeasure']
	request_url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+str(int(time.time())*1000)+"&limit=20" 
	resp = get_resp_from_server(request_url)
	data = resp[0]["Readings"] 

	#output html
	template = loader.get_template('visual_widget/widget.html')
	context = Context({"data": data, "path":path, "unit":unit, "chart_name":chart_name, "is_realtime":True, "width":width, "height": height})
	return HttpResponse(template.render(context))

@xframe_options_exempt
def current_val(request):
    path = request.GET['path']
    # print "reading_path=",path
    try:
        p_u = Path_UUID.objects.get(path=path)
        uuid = p_u.uuid
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid) 
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"]
        returned_list = str(data)
    except MultipleObjectsReturned: #TODO
        p_us = Path_UUID.objects.filter(path=reading_path).values()
        returned_list = "["
        for p_u in p_us:
            uuid = p_u['uuid']
            url = "http://localhost:8079/api/prev/uuid/"+str(uuid)
            resp = get_resp_from_server(url)
            data = str(resp[0]["Readings"])[1:-1]+","
            returned_list = returned_list + data
        returned_list = returned_list[:-1]+"]"
            
    return HttpResponse(returned_list)