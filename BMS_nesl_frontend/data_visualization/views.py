from django.shortcuts import render
from django.core.exceptions import MultipleObjectsReturned
from django.http import HttpResponse, Http404
from django.template import loader, RequestContext
from data_visualization.models import Menu_Tree, Path_UUID
import urllib, urllib2, json, time

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

def nav_bar_loader(request):
    nav_bar_path = ""
    if request.GET['path'] == "":
        nav_bar_path = "root"
    else:
        nav_bar_path = request.GET['path']
    
    print nav_bar_path
    #Get corrosponding content
    nav_tree_text = Menu_Tree.objects.get(tree_id=1).tree
    nav_tree = json.loads(nav_tree_text)
    layer_counter = 1
    returned_list = ""
    if nav_bar_path == "root":
        returned_list = "<ul class='layer_" + str(layer_counter) + " nav' style='margin-left: 10px; width:120%;'>"
        for key in nav_tree:
            returned_list = returned_list+"<li><a href='#'>"+key+"<span class='sr-only'></span></a></li>"
        returned_list = returned_list + "</ul>"
    else:
        path_list = [tag.strip() for tag in nav_bar_path.split(',')]
        target_tree = nav_tree
        for tag in path_list:
            target_tree = target_tree[tag]
            layer_counter += 1
        if target_tree:
            #generate nav bar
            returned_list = "<ul class='layer_"+ str(layer_counter) +" nav' style='margin-left: 10px; width:100%;'>"
            for key in target_tree:
                returned_list = returned_list+"<li><a href='#'>"+key+"<span class='sr-only'></span></a></li>"
            returned_list = returned_list + "</ul>"
        else:
            #return options menu string
            returned_list = {}
            reading_path = "/" + nav_bar_path.replace(",", "/")
            # print "debug::nav_bar_loader -> reading_path=",reading_path
            try:
                p_u = Path_UUID.objects.get(path=reading_path) #TODO:multiple objects returned
                uuid = p_u.uuid
            except MultipleObjectsReturned:
                p_us = Path_UUID.objects.filter(path=reading_path).values()
                uuid = p_us[0]['uuid']
            # print "debug::nav_bar_loader -> uuid=", uuid
            returned_list['uuid']=uuid    
            returned_list['html'] = \
            "<ul class='menu_option nav' style='margin-left:10px;width:105%;'>\
                <li><a href='#''><i>1. View Realtime Plot</i> <span class='sr-only'></span></a></li>\
                <li><a href='#'><i>2. View History Plot</i> <span class='sr-only'></span></a></li>\
                <li><a href='#'><i>3. View Data Statistics(Comming Soon)</i> <span class='sr-only'></span></a>\
                </li>\
            </ul>"
            returned_list = json.dumps(returned_list)    
    return HttpResponse(returned_list)

def load_data(request):
    reading_path = request.GET['path']
    reading_path = "/" + reading_path.replace(",", "/")
    # print "reading_path=",reading_path
    plot_type = request.GET['type']
    # print plot_type
    try:
        p_u = Path_UUID.objects.get(path=reading_path)
        uuid = p_u.uuid
        print "uuid=", uuid
        if plot_type == "history_plot":
            if 'button' not in request.GET:
                button_type = "older"
            else:
                button_type = request.GET['button']
            if button_type == "older":
                starttime = request.GET['starttime']
                url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+starttime+"&limit=300000"
            else:
                endtime = request.GET['endtime']
                url = "http://localhost:8079/api/data/uuid/"+str(uuid)+"?starttime="+endtime+"&limit=300000"
        if plot_type == "realtime_plot":
            now = int(time.time())
            url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+str(now*1000)+"&limit=20" 
        #get data
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"]    
        returned_info = {}
        returned_info['uuid'] = uuid
        returned_info['data'] = data
        #get unit
        url = "http://localhost:8079/api/query/uuid/"+str(uuid)+ "/Properties__UnitofMeasure"
        resp = get_resp_from_server(url)
        unit = resp[0]
        returned_info['unit'] = unit
        returned_info = json.dumps(returned_info)
    except MultipleObjectsReturned:  #TODO: multiple objects
        p_us = Path_UUID.objects.filter(path=reading_path).values()
        total_data = []
        p_u = p_us[-1]
        uuid = p_u['uuid']
        print "multiple",uuid
        if plot_type == "history_plot":
            if 'button' not in request.GET:
                button_type = "older"
            else:
                button_type = request.GET['button']
            if button_type == "older":
                starttime = request.GET['starttime']
                url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+starttime+"&limit=150000"
            else:
                endtime = request.GET['endtime']
                url = "http://localhost:8079/api/data/uuid/"+str(uuid)+"?starttime="+endtime+"&limit=150000"
        if plot_type == "realtime_plot":
            now = int(time.time())
            url = "http://localhost:8079/api/prev/uuid/"+str(uuid)+"?starttime="+str(now*1000)+"&limit=20"
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"]
        returned_info={}
        returned_info['data'] = data
        #get unit
        url = "http://localhost:8079/api/query/uuid/"+str(uuid)+ "/Properties__UnitofMeasure"
        resp = get_resp_from_server(url)
        unit = resp[0]
        returned_info['unit'] = unit
        returned_info = json.dumps(returned_info)
    return HttpResponse(returned_info)

def current_val(request):
    path = request.GET['path']

    #return data readings
    reading_path = "/" + path.replace(",", "/")
    # print "reading_path=",reading_path
    try:
        p_u = Path_UUID.objects.get(path=reading_path)
        uuid = p_u.uuid
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid) 
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"]
        returned_list = str(data)
    except MultipleObjectsReturned: #TODO
        p_us = Path_UUID.objects.filter(path=reading_path).values()
        p_u = p_us[-1]
        uuid = p_u['uuid']
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid)
        resp = get_resp_from_server(url)
        data = str(resp[0]["Readings"])
        returned_list = data
            
    return HttpResponse(returned_list)

def data_statistics(request):
    returned_list = {}
    #get current data
    path = "/Boelter Hall/NESL lab/Smart Electric Meter/VerisE30A042/Current/sensor"
    total_current_usage = 0
    current_usage_list=[]
    for i in range(42):
        query_path = path+str(i+1)
        p_u = Path_UUID.objects.get(path=query_path)
        uuid = p_u.uuid
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid)
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"][0]
        total_current_usage += data[1]
        current_usage_list.append(data[1])
    returned_list['current'] = []
    for i in range(42):
        if current_usage_list[i] != 0:
            returned_list['current'].append(['Sensor'+str(i+1), current_usage_list[i]/total_current_usage])

    #get powerfactor data
    path = "/Boelter Hall/NESL lab/Smart Electric Meter/VerisE30A042/PowerFactor/sensor"
    total_current_usage = 0
    current_usage_list=[]
    for i in range(42):
        query_path = path+str(i+1)
        p_u = Path_UUID.objects.get(path=query_path)
        uuid = p_u.uuid
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid)
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"][0]
        total_current_usage += data[1]
        current_usage_list.append(data[1])
    returned_list['PowerFactor'] = []
    for i in range(42):
        if current_usage_list[i] != 0:
            returned_list['PowerFactor'].append(['Sensor'+str(i+1), current_usage_list[i]/total_current_usage])
    
    #get real power data
    path = "/Boelter Hall/NESL lab/Smart Electric Meter/VerisE30A042/RealPower/sensor"
    total_current_usage = 0
    current_usage_list=[]
    for i in range(42):
        query_path = path+str(i+1)
        p_u = Path_UUID.objects.get(path=query_path)
        uuid = p_u.uuid
        url = "http://localhost:8079/api/prev/uuid/"+str(uuid)
        resp = get_resp_from_server(url)
        data = resp[0]["Readings"][0]
        total_current_usage += data[1]
        current_usage_list.append(data[1])
    returned_list['RealPower'] = []
    for i in range(42):
        if current_usage_list[i] != 0:
            returned_list['RealPower'].append(['Sensor'+str(i+1), current_usage_list[i]/total_current_usage])
    
    return HttpResponse(json.dumps(returned_list))