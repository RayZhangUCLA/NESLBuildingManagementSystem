from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from data_visualization.models import Path_UUID, Menu_Tree
from influxdb.influxdb08 import InfluxDBClient
from time import time
import urllib, urllib2, json
import datetime
import os

def get_resp_from_server(url):
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req).read()
    return json.loads(resp)

def get_resp_from_server_wo_load_json(url):
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req).read()
    return resp

def check_if_TSDB_exists(client, dbname):
    db_list = client.get_list_database()
    for db in db_list:
        if 'name' in db and db['name'] == dbname:
            return True
    return False

def check_if_TimeSeries_exists(tsname):
    ts_list = get_list_series()
    for ts in ts_list:
        if ts == tsname:
            return True
    return False

def write_to_log(msg):
    path = os.path.expanduser('~/sources/Django_frontend/BMS_nesl_frontend/calc_stats_Log.txt')
    with open(path, "a") as logfile:
        current_datetime = datetime.datetime.fromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S")
        logfile.write(str(current_datetime) + " " + msg +"\n")

class Command(BaseCommand):
    args = '<addr:port>'
    help = 'Find average and sum values for each data stream in the sMAP server'

    def handle(self, *args, **options):
        write_to_log("Start to updating smap statistics...")
        addr = "localhost:8079"
        if len(args) > 0:
            self.stdout.write('Use default address and port -- localhost:8079')
            addr = args[0]

        #get access to Timeseries database(influxDB)
        timeDB = InfluxDBClient('ip address', 'port', 'username', 'password', 'database name')
        if not check_if_TSDB_exists(timeDB, 'smap_statistics'):
            print("Create InfluxDB Database smap_statistics")
            timeDB.create_database('smap_statistics')

        #find time range of data we want to calculate the statistics for
        yesterday = datetime.date.today() - datetime.timedelta(1)
        starttime = float(yesterday.strftime("%s") + "000") #1425970800000  #timestamp should be in milliseconds
        endtime = float(datetime.date.today().strftime("%s") + "000") #1426057200000 

        #find statistics for all uuid
        url = "http://"+addr+"/api/query/uuid" #TODO: old netatmo uuids are deprecated
        uuids = get_resp_from_server_wo_load_json(url)
        uuids = uuids[1:-1]
        uuids = [uuid.strip().replace('"', '') for uuid in uuids.split(',')]
        # uuid = "1622c46d-c0f9-58d0-a241-9c47e2a94afe"
        # uuid = "782c5441-331a-5ed7-9575-65aa726c165a"
        try:
            for uuid in uuids:
                p_u = Path_UUID.objects.get(uuid=uuid)
                data_type = p_u.data_type #0 for continous, 1 for discrete
                url = "http://"+addr+"/api/data/uuid/"+uuid+"?starttime="+ str(int(starttime)) +"&endtime=" + str(int(endtime+60*1000))
                readings = get_resp_from_server(url)[0]['Readings'] 
                #time series in influxDB corrosponds to this uuid
                summation = 0
                counter = 0
                if data_type == 1: #discrete
                    time_iterator = starttime + 15*60*1000
                    event_marker=0
                    for reading in readings:
                        timestamp = reading[0]
                        data = reading[1]
                        if timestamp <= time_iterator:
                            pass
                        else:
                            #upload statistics and increment time_iterator
                            post = [
                                {
                                    "points": [[time_iterator, summation]],
                                    "name": uuid,
                                    "columns":["time", "sum"]  
                                }
                            ]
                            timeDB.write_points(post, time_precision='ms')
                            time_iterator += 15*60*1000
                            summation = 0
                            event_marker = 0               
                        if data != 0:
                            if event_marker == 0:
                                event_marker = 1
                            else:
                                pass
                        else:
                            if event_marker == 0:
                                pass
                            else:
                                summation += 1
                                event_marker = 0
                else:
                    time_iterator = starttime + 15*60*1000
                    for reading in readings:
                        timestamp = reading[0]
                        data = reading[1]
                        if timestamp <= time_iterator:
                            #calculate statistics
                            summation += data
                            counter += 1
                        else:
                            #upload statistics and increment time_iterator
                            post = [
                                {
                                    "points": [[time_iterator, counter, summation]],
                                    "name": uuid,
                                    "columns":["time", "counter", "sum"]  
                                }
                            ]
                            timeDB.write_points(post, time_precision='ms')
                            time_iterator += 15*60*1000
                            summation = data
                            counter = 1
        except Exception, e:
            print ("Unkown error happend. Please check with logfile.")
            msg = str(e)
            write_to_log(msg)
            sys.exit(1)

        write_to_log("Program finishes without encountering problems")

        

