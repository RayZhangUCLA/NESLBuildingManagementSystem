# Author: Tianrui Zhang, NESL, UCLA
# Created on: Oct 1, 2014
import json
from time import sleep, time, strftime
from datetime import datetime
from smap.driver import SmapDriver
from smap.util import periodicSequentialCall
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing import Process, Queue
from SocketServer import ThreadingMixIn
import threading

class My_HTTP_Handler(BaseHTTPRequestHandler):
	queue = None
	def transport_to_sMAP(self, data):
		if self.queue == None:
			print "Queue to Smap Driver has not been created" 
		elif self.queue.full(): #if queue is full, then discard the data
			print "Queue is full. Discard packets from SmartThings Server"
		else:
			self.queue.put(data, True, 2)

	def do_POST(self):
		self.rfile._sock.settimeout(60);			
		#print http message
		content_len = int(self.headers.getheader('content-length', 0))
		post_body = self.rfile.read(content_len)
		print self.request_version, self.command
		print self.headers
		print post_body

		#reply with HTTP OK
		reply = "Message received. Thanks!"
		self.send_response(200)
		self.send_header("Content-Length", str(len(reply)))
		self.end_headers()
		self.wfile.write(reply)

		#Push data to sMAP driver
		self.transport_to_sMAP(json.loads(post_body))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	#See details on posts http://stackoverflow.com/questions/8403857/python-basehttpserver-not-serving-requests-properly
	pass

def SmartThings_Handler(q, IPaddr, port):
	address = (IPaddr, int(port))
	My_HTTP_Handler.queue = q
	server = ThreadedHTTPServer(address, My_HTTP_Handler)
	while True:
		try:
			print ("Starting HTTP server to listen to messages from SmartThings Sensors")
			server.serve_forever()
		except KeyboardInterrupt:
			print "Keyboard Interupt received. Shutting down SmartThings Handler HTTP Server"
			msg = "User pressed Ctrl + C"
			write_to_log(msg)
			server.shutdown()
			break
		except Exception, e:
		 	print "Unkown error happend. Please check with logfile. Restarting SmartThings Handler HTTP Server"
		 	msg = str(e)
		 	write_to_log(msg)
			server.shutdown()
	

def write_to_log(msg):
	with open("Smartthings_Server_Log.txt", "a") as logfile:
		current_datetime = datetime.fromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S")
	    	logfile.write(str(current_datetime) + " " + msg +"\n")

class SmartThingsDriver(SmapDriver):
	building_dict = {}
	def setup(self, opts):
		print "Setting metadata..."
		self.set_metadata('/', {
			'Extra/Driver' : 'smap.drivers.SmartThingsDriver.SmartThingsDriver',
			'Location/Building' : 'Bolter Hall',
			'Location/State' : 'CA',
			'Location/City' : 'Los Angeles'
			})

		#SmartThing HTTP server data Structure
		server_ip = opts.get('SmartThing_HTTP_server_ipaddr', "128.97.93.240") 
		server_port = 9000
		split = server_ip.split(":")
		if len(split) == 1:
			server_ip = split[0]
		else:
			server_ip = split[0]
			server_port = split[1]

		self.queue = Queue(maxsize=20000)
		self.proc = Process(target=SmartThings_Handler, args=(self.queue, server_ip, server_port,))
		self.proc.start()

	def start(self):
		periodicSequentialCall(self.handle_HTTP_from_SmartThings).start(1)

	def handle_HTTP_from_SmartThings(self):
		for i in range(100):
			if self.queue.empty():
				break
			else:
				HTTP_post = self.queue.get(True, 2)
				room_name = str(HTTP_post['room'])
				if room_name == "Boelter Hall 1762":
					room_name = "NESL lab"
				#add timeseries if needed
				device_name = None
				if room_name not in self.building_dict or str(HTTP_post['device']) not in self.building_dict[room_name]:
					device_name = str(HTTP_post['device'])
					if "Multi" in device_name:
						device_unit = "Open/Close"
					elif "Motion" in device_name:
						device_unit = "Active/Inactive"
					path = "/%s/%s" % (room_name, device_name)
					print "Adding timeseries "+path
					self.add_timeseries(path, device_unit, data_type='long')
				if room_name not in self.building_dict:
					self.building_dict[room_name] = {}
					self.building_dict[room_name][device_name] = []
				elif str(HTTP_post['device']) not in self.building_dict[room_name]:
					self.building_dict[room_name][device_name] = []

				#add data to dict
				timestamp = HTTP_post['time']
				if len(timestamp) > 10:
					timestamp = int(timestamp)/1000
				else:
					timestamp = int(timestamp)
				device_name = str(HTTP_post['device'])
				device_value = str(HTTP_post['value'])
				if "close" in device_value or "inactive" in device_value:
					val = 0
				else:
					val = 1
				self.building_dict[room_name][device_name].append((timestamp, val))
			
		#upload readings between two consecutive 
		for room_name in self.building_dict.keys():
			for device_name in self.building_dict[room_name].keys():
				#when we have more than 2 readings for a sensor
				localpath ='/'+room_name+'/'+device_name
				ts_val_list = self.building_dict[room_name][device_name]
				ts_val1 = ts_val_list[0]
				timestamp1 = ts_val1[0]
				while len(ts_val_list) >= 2:
					ts_val2 = ts_val_list[1]
					timestamp2 = ts_val2[0]
					for i in range(timestamp1, timestamp2):
						self.add(localpath, i, ts_val1[1])
					ts_val_list=ts_val_list[1:]
				else:	
					#only one reading is present
					self.building_dict[room_name][device_name] = ts_val_list
					current_time = int(time())
					if current_time - timestamp1 >= 10:
						for i in range(timestamp1, current_time):
							self.add(localpath, i, ts_val1[1])
						self.building_dict[room_name][device_name][0] = (current_time, ts_val1[1])
												

	def shut_down_server(self):
		if self.proc != None:
			self.proc.join()

