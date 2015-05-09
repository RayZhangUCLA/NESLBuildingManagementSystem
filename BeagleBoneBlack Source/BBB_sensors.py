# Author: Tianrui Zhang, NESL, UCLA
# Created on: Sep 12, 2014
# References:
# https://github.com/IanHarvey/bluepy
# http://www.cs.berkeley.edu/~stevedh/smap2/index.html
# https://dev.netatmo.com/doc

import sys
import traceback
import bluetooth
import re
import os
import bluetooth._bluetooth as bluez
from time import sleep, time
from datetime import datetime
from smap.driver import SmapDriver
from smap.util import periodicSequentialCall
from smap.drivers.BBB_helper_class.BluetoothSensor import BluetoothSensor
from smap.drivers.BBB_helper_class.VerisE30A042 import VerisE30A042
from smap.drivers.BBB_helper_class.NetatmoWeatherStation import NetatmoWeatherStation
from smap.drivers.BBB_helper_class.EatonIQ260 import EatonIQ260
from smap.drivers.BBB_helper_class import blescan
from smap.drivers.BBB_helper_class.btle import Peripheral, BTLEException
from multiprocessing import Process, Queue
from subprocess import call
from struct import unpack
from httplib import BadStatusLine


def write_to_log(msg):
	path = os.path.expanduser('~/sources/conf/BBB_smap_Log.txt')
	with open(path, "a") as logfile:
		current_datetime = datetime.fromtimestamp(time()).strftime("%Y-%m-%d %H:%M:%S")
		logfile.write(str(current_datetime) + " " + msg +"\n")

#check validity of packet received, true for corrupted, false otherwise
#input should be bytearray
def check_packt_header(packet):
	if packet[0] != 0x02:
		return True
	else:
		return False
	leng = len(packet)
	if packet[leng-1] != 0x03:
		return True
	else:
		return False

#Looping until receive valid packet of connected sensor, return data packet
def loop_until_have_valid_pk(bt_device):
	while True:
		data = bt_device.get_readings()
		data_barray = bytearray(data)

		if check_packt_header(data_barray):
			print "Packet corrupted, discard the packet"
			continue
		else:
			return data_barray

#data byte array =>| | => list of (timestamp, value)
#input should be byte array
def process_raw_reading(data_packet):
	#print "DEBUG::process raw readings"
	readings = []
	type_fd_nor = data_packet[1]
	
	#determine float or double
	is_float = True
	fd_byte = type_fd_nor
	fd_mask = 0x40
	fd_value = (fd_byte & fd_mask) >> 6
	if fd_value == 1:
		is_float = False

	#determine number of tuples in packet
	nor_mask = 0x3F
	num_of_tuple = (type_fd_nor & nor_mask)

	#extract readings
	#NOTE: assume float/double in little endian
	tup_index = 2
	for i in range(num_of_tuple):
		#get timestamp
		ts = 0
		for j in range(8):
			current_byte = data_packet[tup_index]
			ts += current_byte << (8*(7-j))
			tup_index += 1

		#get float/double value
		value = 0
		if is_float:
			val_bytes = data_packet[tup_index+3:tup_index-1:-1]
			value = unpack('f', str(val_bytes))[0]
			tup_index += 4
		else:
			val_bytes = data_packet[tup_index+7:tup_index-1:-1]
			value = unpack('d', str(val_bytes))[0]
			tup_index += 8
		readings.append((ts, value))
	return readings

# Start an Bluetooth client connection for:
# 	1. establish connection with sensor
# 	2. always waiting for data reading in
# 	3. reconnects when connection is lost
# 	4. put data into Queue that will be read by main process		
def BT_client(q):
	bt_device = BluetoothSensor()
	address = bt_device.listen_for_connection()
	q.put(address)
	
	#always extracting data and put them into pipe, also reconnets if gets disconnects
	while True:
		try:
			# Extract data and put it into queue
			data_barray = loop_until_have_valid_pk(bt_device)
			if q.full(): #if queue is full, then discard the data
				print "Bluetooth Port%d Queue is full, current readings will be discarded" % address[1]
			else:
				q.put(process_raw_reading(data_barray), True, 2)
		except bluetooth.BluetoothError:
			#connection lost, try to reestablish connection
			print "Connection lost, reconneting from port%d" % address[1]
			bt_device.close_connection()
			new_address = bt_device.listen_for_connection()
			
			if new_address != address: #a new sensor establish connectoin with this port
				address = new_address
				q.put(address)
		except KeyboardInterrupt:
			print "Interrupt Signal Catched, closing port%d" % address[1]
			bt_device.close_connection()
			sys.exit(1)

#################################################################################################################
def BLE_handler(q, sample_interval):
	dev_id = 0
	try:
		hci_sock = bluez.hci_open_dev(dev_id)
	except:
		print "Cannot accesse bluetooth adaptor..."
		sys.exit(1)
	blescan.hci_le_set_scan_parameters(hci_sock)
	blescan.hci_enable_le_scan(hci_sock)
	try:
		while True:
			bt_addr_List = blescan.get_BT_addr_around(hci_sock, 10)
			if q.full(): #if queue is full, then discard the data
				print "Bluetooth Low Energy Queue is full, current readings will be discarded"
			else:
				q.put(bt_addr_List, True, 2)
			sleep(sample_interval)
	except KeyboardInterrupt:
		print "Interrupt Signal Catched, Closing BLE scanner"
		sys.exit(1)

#################################################################################################################
def connect_to_RFduino(device_addr, addrType):
	for i in range(5):
		try:
			rfduino = Peripheral(deviceAddr=device_addr, addrType=addrType)
			return rfduino
		except BTLEException:
			pass
	return None

def RFduino_client(q, device_addr, sample_interval):
	if not device_addr:
		print "RFduino device address should not be none. Please check and restart program"
		sys.exit(1)
	while True:
		rfduino = connect_to_RFduino(device_addr, "random")
		if rfduino:
			break
	print "RFduino connected..."
	characteristic = rfduino.getCharacteristics(uuid="2221")[0]
	while True:
		try:
			reading = characteristic.read()
			if reading:
				reading = unpack('f', reading)[0]
				if q.full():
					print "RFduino Queue is full, current readings will be discarded"
				else:
					q.put(reading, True, 2)
			sleep(sample_interval)
		except BTLEException:
			rfduino = connect_to_RFduino(device_addr, "random")
			if rfduino:
				characteristic = rfduino.getCharacteristics(uuid="2221")[0]
		except KeyboardInterrupt:
			print ("Interrupt Signal received, RFduino client shuts down")
			rfduino.disconnect()
			sys.exit(1)
		except:
			print ("Unkown error happend. Please check with logfile.")
			exc_type, exc_value, exc_traceback = sys.exc_info()
			lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
			write_to_log(''.join(line for line in lines))
			rfduino.disconnect()
			sys.exit(1)			

#################################################################################################################
def SEM_client(q, params, sample_interval):
	Smart_Meter_Device = VerisE30A042('10086', params)

	#always try to extract data from the smart electric meter. Reconnects when Internect connection is lost
	try:
		while True:
			connection_status = Smart_Meter_Device.connect()
			if connection_status:
				print "Veris Smart Meter connected successfully"
				break
			else:
				print "Cannot establish connectoin with Veris smart meter. Retrying..."

		while True:
			sleep(sample_interval)
			reply = Smart_Meter_Device.get_sample()
			if reply == None:
				print "Veris Smart Meter Connection Lost. Trying to reconnects"
				Smart_Meter_Device.connect()
				continue
			else:
				if q.full(): #if queue is full, then discard the data
					print "Veris Smart Meter Queue is full, current readings will be discarded"
				else:
					q.put(reply, True, 2)			
	except KeyboardInterrupt:
		print "Interrupt Signal Catched, Veris SEM client shuts down"
		Smart_Meter_Device.disconnect()
		sys.exit(1)

#################################################################################################################
def Eaton_SEM_handler(q, params, sample_interval):
	Eaton_Device = EatonIQ260('10000', params)

	#always try to extract data from the smart electric meter. Reconnects when Internect connection is lost
	try:
		while True:
			connection_status = Eaton_Device.connect()
			if connection_status:
				print "EatonIQ260 Smart Meter connected successfully"
				break
			else:
				print "Cannot establish connectoin with EatonIQ260 smart meter. Retrying..."

		while True:
			sleep(sample_interval)
			reply = Eaton_Device.get_sample()
			if reply == None:
				print "EatonIQ260 Smart Meter Connection Lost. Trying to reconnects"
				Eaton_Device.connect()
				continue
			else:
				if q.full(): #if queue is full, then discard the data
					print "EatonIQ260 Smart Meter Queue is full, current readings will be discarded"
				else:
					q.put(reply, True, 2)			
	except KeyboardInterrupt:
		print "Interrupt Signal Catched, Eaton SEM client shuts down"
		Eaton_Device.disconnect()
		sys.exit(1)


###############################################################################################################
def Netatmo_client(q, client_id, client_secret, username, password, scope, grant_type, sample_interval, first_retrive_time, measurement_type, outdoor_measurement_type):
	Netatmo_weather_station = NetatmoWeatherStation(client_id, client_secret, username, password, scope, grant_type)

	try:
		#Authenticate before using RESTful APIs
		while not Netatmo_weather_station.authentication():
			write_to_log("authentication failure")
			pass
		write_to_log("authentication successfully")

		while True: #Netatmo Server may return empty HTTP response
			try:
				info = Netatmo_weather_station.get_devicelist()
				break
			except BadStatusLine:
				write_to_log("Netatmo Server return BadStatusLine while getting device list")
				Netatmo_weather_station.close_http_conn()

		device_id = info['body']['modules'][0]['main_device']
		outdoor_module_id = info['body']['modules'][0]['_id']
		last_retrive_time = first_retrive_time
		
		#Get the data
		while True:
			if Netatmo_weather_station.reauthenticate_if_needed():
				current_retrive_time = time()
				http_response = None
				outdoor_http_response = None
				indoor_readings = []
				outdoor_readings = []
				http_response = Netatmo_weather_station.get_measure(device_id, "max", 
					measurement_type, date_begin=last_retrive_time, date_end=current_retrive_time)
				outdoor_http_response = Netatmo_weather_station.get_measure(device_id, "max", 
					outdoor_measurement_type, module_id= outdoor_module_id, date_begin=last_retrive_time, date_end=current_retrive_time)
				if http_response:
					indoor_readings = http_response['body']
				if outdoor_http_response:
					outdoor_readings = outdoor_http_response['body']
				output = {}
				output['indoor'] = indoor_readings
				output['outdoor'] = outdoor_readings
				if q.full(): 
					print("Netatmo weather station Queue is full, current readings will be discarded")
					write_to_log("queue is full")
				elif indoor_readings and outdoor_readings:
					last_retrive_time = current_retrive_time
					print("Output in the queue")
					q.put(output, True, 2)
				else:
					pass
			sleep(sample_interval)
				
	except KeyboardInterrupt:
		print ("Interrupt Signal received, Netatmo client shuts down")
		write_to_log("User preserd Ctrl + C")
		Netatmo_weather_station.close_http_conn()
		sys.exit(1)

	except:
		print ("Unkown error happend. Please check with logfile.")
		exc_type, exc_value, exc_traceback = sys.exc_info()
		lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
		write_to_log(''.join(line for line in lines))
		Netatmo_weather_station.close_http_conn()
		sys.exit(1)
		

###############################################################################################################

# Smap driver for BeagleBone Black
class BBBDriver(SmapDriver):

	###########################################################################################################
	# Packets for Bluetooth Connection:
	#	Data_packet:
	# 	 _____________________________________
	# 	|_STX_|_TYPE_|_F/D_|_NOR_|_DATA_|_ETX_|	 (Length: 15 - 1027 bytes)	
	#	
	# 	STX: Start of text denote the start of message. It's ASCII character 0x02. (1 byte) 
	# 	TYPE: Indicate whether this packet is data packet or metada packet. '1' for data, '0' for metadata (1 bit)
	# 	F/D: Float or double. '0' for float and '1' for double (1 bit)
	# 	NOR: Number of readings in data section. Maximum number is 63 (6 bits)
	# 	DATA: (Timestamp, reading) pairs. Timestamp is unix timestamp, and reading is expressed in float or double. 
	# 		Number of pairs are specified in NOR field (12 or 16 bytes per tuple)
	# 	ETX: End of text. It's ASCII character 0x03 (1 byte)
	#
	# Data Packet for Smart Electrical Meters:
	# 	See Modbus protocol for reference.
	#	
	# Data Packet for Wifi Connection:
	#	Coming soon...
	#
	# Data Structure Kept in Main Process:
	# 	For Bluetooth sensors, one process for each sensor. We also need address(btaddr, port number), 
	#		sensor info(type, unit), sampling interval(current_count is a helping variable) for each sensor:
	# 					 
	# 					{sensor1 btaddr: [address, (sensor_name, sensor_type, sensor_unit), interval, current_count, Queue, Process],
	# 					 sensor2 btaddr: [address, (sensor_name, sensor_type, sensor_unit), interval, current_count, Queue, Process],
	# 	bt_sensor_dict = .
	# 					 .
	# 					}
	#
	#
	# 	ble_dict = {sensor1 btaddr: (anything)
	# 				sensor2 btaddr: (anything)
	# 				...}
	#
	#	For Smart Electric Meter(Both VerisE30A042 and EatonIQ260):
	#	sem_sensor = [sem_sensor_dict, sem_meter_type, sem_max_meter_count, Queue, Process]
	#	sem_sensor_dict = {'host': IPaddr, 
	# 					  'port': port number, 
	# 					  'timeout': time out interval
	#					  'sample_interval':sample interval
	#					 }
	#	
	#	For Netatmo weather station:
	#	 nws_dict = { 'type': Netatmo measurement type and corrosponging unit
	#				  'type_to_measure': The type user specifies to measure	for indoor module				
	#				  'type_to_measure_outdoor': The type user specifies to measure	for outdoor module	
	# 				  'process' : Process
	# 				  'queue': Queue
	#	 			}
	#
	# 	For Wifi sensors, 
	# 		currently unavailable
	###########################################################################################################

	bt_sensor_dict = {} #Bletooth Classic
	ble_dict = {} #BLE
	ble_queue = None
	ble_proc = None
	sem_sensor = [] #Veris TCP Modbus
	Eaton_Device = [] #Eaton TCP Modbus
	nws_dict = {} #Netatmo
	ibeacon_started = False

	def setup(self, opts):
		#Add matadata of BeagleBone Black
		print "Setting metadata..."
		self.set_metadata('/', {
			'Extra/Driver' : 'smap.drivers.BeagleBoneBlack.BBBDriver',
			'Instrument/Model' : 'BeagleBone Black',
			'Instrument/Manufacturer' : 'Circuitco',
			'Location/Building' : 'Boelter NESL',
			'Location/State' : 'CA',
			'Location/City' : 'Los Angeles'
			})

		#grab needed readings from configure file
		# self.num_BT_sensor = int(opts.get('BT_sensor_number', '0'))

		# #constructing bluetooth sensor data structure
		# for i in range(self.num_BT_sensor): 
		# 	sensor_name = opts.get('BT_sensor_%d_name' % (i+1), None)
		# 	sensor_type = opts.get('BT_sensor_%d_type' % (i+1), None)
		# 	sensor_unit = opts.get('BT_sensor_%d_unit' % (i+1), None)
		# 	sensor_btaddr = opts.get('BT_sensor_%d_btaddr' % (i+1), None)
		# 	sensor_interval = opts.get('BT_sensor_%d_interval' % (i+1), None)

		# 	if sensor_btaddr==None or sensor_name==None or sensor_type==None or sensor_unit==None:
		# 		print "Error on reading bluetooth sensor %d name, type, unit or address. Program exits." % i
		# 		sys.exit()
			
		# 	sensor_info = (sensor_name, sensor_type, sensor_unit)
		# 	bt_address = (sensor_btaddr, -1) # port number -1 means unknown yet
		# 	self.bt_sensor_dict[sensor_btaddr] = [bt_address, sensor_info, int(sensor_interval), 1]

		#constructing bluetooth sensor data structure
		self.rfduino_addr = opts.get('RFduino_btaddr', None)
		self.rfduino_sample_interval = int(opts.get('RFduino_sample_interval', 10))
		self.rfduino_counter = 1

		#constructing Veris smart meter data structure
		sem_ipaddr = opts.get('Veris_Smart_Meter_ipaddr', None) 
		sem_port = 4660
		split = sem_ipaddr.split(":")
		if len(split) == 1:
			sem_ipaddr = split[0]
		else:
			sem_ipaddr = split[0]
			sem_port = split[1]
		sem_sensor_dict = {}
		sem_sensor_dict['host'] = sem_ipaddr
		sem_sensor_dict['port'] = sem_port
		sem_sensor_dict['timeout'] = opts.get('Veris_Smart_Meter_timeout', 2)
		sem_sample_interval = int(opts.get('Veris_Smart_Meter_sample_interval', 5)) #defalut sample interval for smart electric meter is 5
		sem_sensor_dict['sample_interval'] = sem_sample_interval
		self.sem_sensor.append(sem_sensor_dict)
		
		sem_meter_type =  [("RealPower", "kW"), ("PowerFactor", "%"),("Current", "A")]
		self.sem_sensor.append(sem_meter_type)
		
		self.sem_sensor.append(42) #specification for Veris meter
		self.sem_sample_interval = sem_sample_interval
		self.sem_counter = 1

		#constructing EatonIQ smart meter data structure
		sem_ipaddr = opts.get('Eaton_Smart_Meter_ipaddr', None) 
		sem_port = 4660
		split = sem_ipaddr.split(":")
		if len(split) == 1:
			sem_ipaddr = split[0]
		else:
			sem_ipaddr = split[0]
			sem_port = split[1]
		Eaton_params = {}
		Eaton_params['host'] = sem_ipaddr
		Eaton_params['port'] = sem_port
		Eaton_params['timeout'] = opts.get('Eaton_Smart_Meter_timeout', 2)
		Eaton_sample_interval = int(opts.get('Eaton_Smart_Meter_sample_interval', 5)) #defalut sample interval for smart electric meter is 5
		Eaton_params['sample_interval'] = Eaton_sample_interval
		self.Eaton_Device.append(sem_sensor_dict)
		Eaton_meter_type =  [
			("Voltage[AN]", "V"), ("Voltage[BN]", "V"), ("Voltage[CN]", "V"),
			("Voltage[AB]", "V"), ("Voltage[BC]", "V"), ("Voltage[CA]", "V"),
			("Current[A]", "A"), ("Current[B]", "A"), ("Current[C]", "A"),
			("RealPower[Total]", "W"), ("ReactivePower[Total]", "VA"), ("ApparentPower[Total]"), ("PowerFactor[Total]", "%"), 
			("Frequency", "Hz"), ("Current[Neutral]", "A"),
			("RealPower[A]", "W"), ("RealPower[B]", "W"), ("RealPower[C]","W"), 
			("ReactivePower[A]", "VA"), ("ReactivePower[B]", "VA"), ("ReactivePower[C]", "VA"), 
			("ApparentPower[A]", "VA"), ("ApparentPower[B]", "VA"), ("ApparentPower[C]", "VA"), 
			("PowerFactor[A]", '%'), ("PowerFactor[B]", "%"), ("PowerFactor[C]", "%")
		]		
		self.Eaton_Device.append(Eaton_meter_type)
		self.Eaton_Device.append(1) #specification for Eaton meter
		self.Eaton_sample_interval = Eaton_sample_interval
		self.Eaton_counter = 1

		#Constructing Netatmo Weather Station Data Structure
		self.nws_sample_interval = int(opts.get('Netatmo_weather_station_sample_interval', "10")) #defalut sample interval for weather station is 10
		nws_client_id = opts.get('Netatmo_weather_station_client_id', "")
		nws_client_secret = opts.get('Netatmo_weather_station_client_secret', "")
		nws_username = opts.get('Netatmo_weather_station_username', "")
		nws_password = opts.get('Netatmo_weather_station_password', "")
		nws_scope = opts.get('Netatmo_weather_station_scope', "read_station")
		nws_grant_type = opts.get('Netatmo_weather_station_grant_type', "password")
		self.nws_dict['type'] = {"Temperature" : "Celsius", 
								 "Humidity" : "%", 
								 "Co2" : "ppm", 
								 "Pressure" : "mbar", 
								 "Noise" : "db"}
		first_retrive_time = int(opts.get('Netatmo_weather_station_initial_retrive_time', "0000000001")) #defalut begain data is epoch time
		nws_measurement_type = opts.get('Netatmo_weather_station_measurement_type', "Everything")
		if nws_measurement_type == "Everything":
			self.nws_dict['type_to_measure'] = ['Temperature','Co2','Pressure','Noise', 'Humidity']
		else:
			self.nws_dict['type_to_measure'] = nws_measurement_type
		nws_outdoor_measurement_type = opts.get('Netatmo_weather_station_outdoor_measurement_type', "Everything")
		if nws_outdoor_measurement_type == "Everything":
			self.nws_dict['type_to_measure_outdoor'] = ['Temperature','Humidity']
		else:
			self.nws_dict['type_to_measure_outdoor'] = nws_outdoor_measurement_type
		nws_measurement_type = self.nws_dict['type_to_measure'][0]
		for element in self.nws_dict['type_to_measure'][1:]:
			nws_measurement_type += "," + element
		nws_outdoor_measurement_type = self.nws_dict['type_to_measure_outdoor'][0]
		for element in self.nws_dict['type_to_measure_outdoor'][1:]:
			nws_outdoor_measurement_type += "," + element
		self.nws_counter = 1

		try:
			#ibeacon advertisment
			# NESL_UUID=" 46 A7 59 4F 67 2D 4B 6C 81 C1 78 5A EC DB A0 D5 "
			# uuid = opts.get("ibeacon_UUID", NESL_UUID)
			# print "Starting ibeacon advertisment..."
			# proc = Process(target=self.start_ibeacon, args=(uuid,))
			# proc.start()
			# proc.join()
			# print "ibeacon advertisment finished..."

			#Bluetooth Sensors
			# print ("Setting up %d bluetooth sensors..." % self.num_BT_sensor)
			# proc_array = []
			# queue_array = []

			# for i in range(0, self.num_BT_sensor):
			# 	queue = Queue(maxsize=5000)
			# 	queue_array.append(queue)

			# 	proc = Process(target=BT_client, args=(queue,))
			# 	proc_array.append(proc)
			# 	proc.start()

			# for i in range(0, self.num_BT_sensor):
			# 	queue = queue_array[i]
			# 	proc = proc_array[i]
			# 	address = queue.get()
			# 	bt_address = address[0]
			
			# 	if bt_address not in self.bt_sensor_dict:
			# 		print ("Bluetooth address not specified in smap configure file. Shutting down...")
			# 		self.close()
			# 		sys.exit()
			# 	else:
			# 		self.bt_sensor_dict[bt_address][0] = address
			# 		self.bt_sensor_dict[bt_address].append(queue)
			# 		self.bt_sensor_dict[bt_address].append(proc)

			#BLE scanner
			# print "Setting up Bluetooth Low Energy Scanner..."			
			# self.BLE_sample_interval = int(opts.get("BLE_sample_interval", 10))
			# self.ble_queue = Queue(maxsize=500)
			# self.ble_proc = Process(target=BLE_handler, args=(self.ble_queue, self.BLE_sample_interval,))				
			# self.ble_scanner_counter = 1
			# self.ble_proc.start()

			#RFduino BLE sensor
			print "Setting up RFduino BLE device..."			
			self.rfduino_queue = Queue(maxsize=100)
			self.rfduino_proc = Process(target=RFduino_client, args=(self.rfduino_queue, self.rfduino_addr, self.rfduino_sample_interval,))
			self.rfduino_proc.start()

			#Smart Electric Meter
			print ("Setting up Smart Electric Meter...")
			queue = Queue(maxsize=500)
			self.sem_sensor.append(queue)
			proc = Process(target=SEM_client, args=(queue, self.sem_sensor[0],sem_sample_interval,))
			self.sem_sensor.append(proc)
			proc.start()

			queue = Queue(maxsize=500)
			self.Eaton_Device.append(queue)
			proc = Process(target=Eaton_SEM_handler, args=(queue, Eaton_params, self.Eaton_sample_interval,))
			self.Eaton_Device.append(proc)
			proc.start()

			#Netatmo Weather Station
			print ("Setting up Netatmo weather station...")
			queue = Queue(maxsize=500)
			self.nws_dict['queue'] = queue
			proc = Process(target=Netatmo_client, args=(queue, 
				nws_client_id, nws_client_secret, nws_username, 
				nws_password, nws_scope, nws_grant_type, 
				self.nws_sample_interval, first_retrive_time, nws_measurement_type, nws_outdoor_measurement_type))
			self.nws_dict['proc'] = proc
			proc.start()

			#Listening to Wifi Sensors
			#Comming soon

			#Add timesereies
			print "Adding timesereies to server..."
			# for key in self.bt_sensor_dict.keys(): #bluetooth sensors
			# 	sensor_info = self.bt_sensor_dict[key][1]
			# 	path = '/NESL lab/%s/%s' % (sensor_info[0], sensor_info[1])
			# 	self.add_timeseries(path, sensor_info[2], data_type='double')

			path = '/NESL lab/%s/%s' % ("RFduino", "Temperature Sensor")
			self.add_timeseries(path, "Celsius", data_type='double')
			print("Path %s has been added" % path)

			sem_max_meter_count = self.sem_sensor[2] #Veris smart electric meter
			for meter in sem_meter_type:
				sem_type = meter[0]
				sem_unit = meter[1]
				for i in range(sem_max_meter_count):
					path = '/NESL lab/Smart Electric Meter/VerisE30A042/%s/sensor%d' % (sem_type, i+1)
					self.add_timeseries(path, sem_unit, data_type='double')

			for meter in Eaton_meter_type:#Eaton smart electric meter
				sem_type = meter[0]
				sem_unit = meter[1]
				if "[A]" in sem_type:
					sensor_name = "Sensor A/%s" % sem_type
				elif "[B]" in sem_type:
					sensor_name = "Sensor B/%s" % sem_type
				elif "[C]" in sem_type:
					sensor_name = "Sensor C/%s" % sem_type
				elif "[Total]" in sem_type:
					sensor_name = "Total/%s" % sem_type
				elif "Voltage" in sem_type:
					sensor_name = "Voltage/%s" % sem_type
				else:
					sensor_name = sem_type
				path = '/NESL lab/Smart Electric Meter/EatonIQ260/%s' % sensor_name
				self.add_timeseries(path, sem_unit, data_type='double')

			for measurement in self.nws_dict['type_to_measure']: #Netatmo Weather Station
				if self.nws_dict['type'][measurement] != None:
					nws_unit = self.nws_dict['type'][measurement]
				else:
					print "Please type valid measurement types for Netatmo_weather_station_measurement_type(Temperature, Humidity, Co2, Presure, Noise) Program exits"
					self.close()
					self.exit()
				path = '/NESL lab/Netatmo weather station/Indoor Module/%s' % measurement
				self.add_timeseries(path, nws_unit, data_type='double')
			for measurement in self.nws_dict['type_to_measure_outdoor']: #Netatmo Weather Station outdoor module
				if self.nws_dict['type'][measurement] != None:
					nws_unit = self.nws_dict['type'][measurement]
				else:
					print "Please type valid measurement types for Netatmo_weather_station_outdoor_measurement_type(Temperature, Humidity) Program exits"
					self.close()
					self.exit()
				path = '/NESL lab/Netatmo weather station/Outdoor Module/%s' % measurement
				self.add_timeseries(path, nws_unit, data_type='double')
		except KeyboardInterrupt:
			print "Inturrput signal received"
			self.close()
			sys.exit()


	def start(self):
		periodicSequentialCall(self.update_readings).start(1)

	def close(self):
		#close ibeacon advertisment
		self.stop_ibeacon()
		#Join Bluetooth process
		for key in self.bt_sensor_dict.keys():
			sensor_list = self.bt_sensor_dict[key]
			if len(sensor_list) == 6:
				proc = self.bt_sensor_dict[key][5]
				proc.join()
		if self.ble_proc != None:
			self.ble_proc.join()
		if self.rfduino_proc != None:
			self.rfduino_proc.join()
		#Join smart meter process
		if len(self.sem_sensor) == 5:
			proc = self.sem_sensor[4]
			proc.join()
		if len(self.Eaton_Device) == 5:
			proc = self.Eaton_Device[4]
			proc.join()
		#Join Netatmo process
		if 'proc' in self.nws_dict:
			sel.nws_dict['proc'].join()
	#ibeacon managment
	def start_ibeacon(self, UUID=None):
		NUM_OCTETS=" 1F "
		IBEACON_PREFIX=" 01 04 1C FF 4C 00 02 15 "
		MAJOR=" 00 04 "
		MINOR=" 03 E7 "
		POWER=" C5 "
		if UUID == None:
			print "No UUID recieved, cannot start ibeacon broadcasting"
		else:
			#ibeacon data field
			btle_data = NUM_OCTETS + IBEACON_PREFIX + UUID + MAJOR + MINOR + POWER
		        adver_cmd = "sudo hcitool -i hci0 cmd 0x08 0x0008" + btle_data
			#bring up bt adaptor
			call(["sudo hciconfig hci0 up"], shell=True)
			#ibeacon broadcasting
			call([adver_cmd], shell=True)
			# set rate to 100 ms
			call(["sudo hcitool -i hci0 cmd 0x08 0x0006 A0 00 A0 00 03 00 00 00 00 00 00 00 00 07 00"], shell=True)
			# enable adv. through tool (hciconfig overrites rate to make slower)
			call(["sudo hcitool -i hci0 cmd 0x08 0x000a 01"], shell=True)
			self.ibeacon_started = True

	def stop_ibeacon(self):
		print "Bring down ibeacon..."
		if self.ibeacon_started:
			call(["sudo hciconfig hci0 noleadv"], shell=True)
			call(["sudo hciconfig hci0 down"], shell=True)

	#check if reconnection happens, given reading
	def reconnection_happens(self, raw_reading):
		#print "DEBUG::checking reconnection"
		if type(raw_reading) is tuple:
			return True
		else:
			return False

	def modify_bt_dict_on_necessary(self, key, new_address):
	# 	case 1:	current process accept reconnection from original sensor
	# 	case 2: two process and sensor pair switched
	# 		We just swap the queue and Process argument of these two
	# 	case 3: more than two get swaped
	# 		We perform the same thing above. If initially assigned wrong process, 
	# 			it will be switched back to right one later. (Greedy Algorithm)
		#print "DEBUG::modify_bt_dict_on_necessary"
		current_address = self.bt_sensor_dict[key][0]
		#case 1
		if current_address == new_address:
			pass
		else:
			#case 2 and 3
			new_btaddr = new_address[0]
			if new_btaddr != key:
				old_queue = self.bt_sensor_dict[new_btaddr][4]
				old_proc = self.bt_sensor_dict[new_btaddr][5]
				current_queue = self.bt_sensor_dict[key][4]
				current_proc = self.bt_sensor_dict[key][5]
				self.bt_sensor_dict[new_btaddr][4] = current_queue
				self.bt_sensor_dict[new_btaddr][5] = current_proc
				self.bt_sensor_dict[key][4] = old_queue
				self.bt_sensor_dict[key][5] = old_proc
			self.bt_sensor_dict[new_btaddr][0] = new_address #port number may change for this btaddr

	#Extract readings from each bluetooth process
	def extract_bt_readings(self, key):
		#print "DEBUG::extract_bt_readings"
		readings = []
		if self.bt_sensor_dict[key] != None:
			queue = self.bt_sensor_dict[key][4]
			for i in range(0, 10):
				if queue.empty():
					break
				else:
					raw_reading = queue.get(True, 2) #raw_reading will be in the format of data packet in description section
					#Reconnection may happen, so check for sensor info tuple
					if self.reconnection_happens(raw_reading): #raw_reading is new sensor address in this case
						print "Reconnetion happens. "
						self.modify_bt_dict_on_necessary(key, raw_reading)
					else:	
						#print "DEBUG:: raw_reading in hex = ", raw_reading.encode("hex")
						readings = readings + raw_reading
		else:
			print "Dictionary key does not exits. Contents might already been deleted"
		return readings

	#upload bluetooth readings
	def upload_bt_readings(self, key, readings):
		#print "DEBUG::upload_bt_readings"
		sensor_name = self.bt_sensor_dict[key][1][0]
		sensor_type = self.bt_sensor_dict[key][1][1]
		localpath = '/NESL lab/%s/%s' % (sensor_name, sensor_type)
		for i in range(len(readings)):
			self.add(localpath, float(readings[i][0]), readings[i][1])
#########################################################################################################
	#extract BLE scanner reading
	def extract_BLE_scanner_readings(self):
		#print "DEBUG::extract_BLE_readings"
		readings = []
		if self.ble_queue.empty():
			pass
		else:
			readings = self.ble_queue.get(True, 2)
		return readings

	#upload BLE_scanner readings
	def upload_BLE_scanner_readings(self, readings):
		#print "DEBUG::upload_ble_readings"
		timestamp = time()
		for btaddr in self.ble_dict.keys():
			path = '/NESL lab/BLE devices List/%s' % btaddr
			if btaddr in readings:
				self.add(path, timestamp, 1)
				readings.remove(btaddr)
			else:
				self.add(path, timestamp, 0)
		for btaddr in readings:
			path = '/NESL lab/BLE devices List/%s' % btaddr
			if btaddr not in self.ble_dict:
				self.ble_dict[btaddr] = '1'
				self.add_timeseries(path, 'Present/Absent', data_type='long')
			self.add(path, timestamp, 1)
#########################################################################################################
	#extract RFduino BLE sensor reading
	def extract_rfduino_readings(self):
		# print "DEBUG::extract_BLE_readings"
		readings = []
		if self.rfduino_queue.empty():
			pass
		else:
			readings = self.rfduino_queue.get(True, 2)
		return readings

	#upload BLE_scanner readings
	def upload_rfduino_readings(self, readings):
		print "DEBUG::upload_ble_readings"
		timestamp = time()
		path = '/NESL lab/%s/%s' % ("RFduino", "Temperature Sensor")
		self.add(path, timestamp, float(readings))

#########################################################################################################
	#extract smart meter readings, returns a list of readings with first elment as the timestamp
	def extract_sem_readings(self):
		# print "DEBUG::extract_sem_readings"
		queue = self.sem_sensor[3]
		readings = []
		if queue.empty():
			pass
		else:
			readings = queue.get(True, 2)
		return readings

	#upload smart meter readings
	def upload_sem_readings(self, readings):
		# print "DEBUG::upload_sem_readings"
		timestamp = float(readings[0])
		readings = readings[1:]
		num_regs = len(readings)/3
		sem_meter_type = self.sem_sensor[1]
		for index, meter in enumerate(sem_meter_type):
			sem_type = meter[0]
			#print "DEBUG::sem_type is %s, and sem_unit is %s" % (sem_type, sem_unit)
			for i in range(num_regs):
				localpath = '/NESL lab/Smart Electric Meter/VerisE30A042/%s/sensor%d' % (sem_type, i+1)
				self.add(localpath, timestamp, float(readings[i+index*num_regs]))

#########################################################################################################
	#extract eaton smart meter readings, returns a list of readings with first elment as the timestamp
	def extract_Eaton_readings(self):
		#print "DEBUG::extract_eatonreadings"
		queue = self.Eaton_Device[3]
		readings = []
		if queue.empty():
			pass
		else:
			readings = queue.get(True, 2)
		return readings

	#upload smart meter readings
	def upload_Eaton_readings(self, readings):
		#print "DEBUG::upload_sem_readings"
		timestamp = float(readings[0])
		readings = readings[1:]
		Eaton_meter_type = self.Eaton_Device[1]
		for index, meter in enumerate(Eaton_meter_type):#Eaton smart electric meter
			sem_type = meter[0]
			if "[A]" in sem_type:
				sensor_name = "Sensor A/%s" % sem_type
			elif "[B]" in sem_type:
				sensor_name = "Sensor B/%s" % sem_type
			elif "[C]" in sem_type:
				sensor_name = "Sensor C/%s" % sem_type
			elif "[Total]" in sem_type:
				sensor_name = "Total/%s" % sem_type
			elif "Voltage" in sem_type:
				sensor_name = "Voltage/%s" % sem_type
			else:
				sensor_name = sem_type
			localpath = '/NESL lab/Smart Electric Meter/EatonIQ260/%s' % sensor_name
			self.add(localpath, timestamp, float(readings[index]))

#########################################################################################################
	def extract_nws_readings(self):
		#print "DEBUG::extract_sem_readings"
		queue = self.nws_dict['queue']
		readings = []
		if queue.empty():
			pass
		else:
			readings = queue.get(True, 2)
		return readings

	def upload_nws_readings(self, readings):
		#print "DEBUG::upload_nws_readings"
		indoor_readings = readings['indoor']
		if indoor_readings:
			nws_type_measured = self.nws_dict['type_to_measure']
			for key in indoor_readings.keys():
				timestamp = float(key)
				reading = indoor_readings[key]
				for index, measurement in enumerate(nws_type_measured):
					if reading[index] != None:
						localpath = '/NESL lab/Netatmo weather station/Indoor Module/%s' % measurement
						self.add(localpath, timestamp, float(reading[index]))
			
		outdoor_readings = readings['outdoor']
		if outdoor_readings:
			nws_type_measured = self.nws_dict['type_to_measure_outdoor']
			for key in outdoor_readings.keys():
				timestamp = float(key)
				reading = outdoor_readings[key]
				for index, measurement in enumerate(nws_type_measured):
					if reading[index] != None:
						localpath = '/NESL lab/Netatmo weather station/Outdoor Module/%s' % measurement
						self.add(localpath, timestamp, float(reading[index]))		

#########################################################################################################
	def update_readings(self):
		try:
			#Ask each bluetooth process for readings
			# for key in self.bt_sensor_dict.keys():
			# 	interval = self.bt_sensor_dict[key][2]
			# 	current_count = self.bt_sensor_dict[key][3]
			# 	if interval == current_count:
			# 		current_count = 1
			# 		self.bt_sensor_dict[key][3] = current_count
			# 		readings = self.extract_bt_readings(key)
			# 		#print "DEBUG:: readings for %s = " % key, readings
			# 		if readings:
			# 			self.upload_bt_readings(key, readings)
			# 	else:
			# 		current_count += 1
			# 		self.bt_sensor_dict[key][3] = current_count

			# #Ask for BLE device around
			# if self.BLE_sample_interval == self.ble_scanner_counter:
			# 	self.ble_scanner_counter = 1
			# 	readings = self.extract_BLE_scanner_readings()
			# 	#print "DEBUG::readings for BLE scanner = ", readings
			# 	if readings:
			# 		self.upload_BLE_scanner_readings(readings)
			# else:
			# 	self.ble_scanner_counter += 1

			#Ask for BLE device around
			if self.rfduino_sample_interval == self.rfduino_counter:
				self.rfduino_counter = 1
				readings = self.extract_rfduino_readings()
				# print "DEBUG::readings for rfduino BLE= ", readings
				if readings:
					self.upload_rfduino_readings(readings)
			else:
				self.rfduino_counter += 1

			# Ask smart meter process for readings
			# VerisE30A042
			if self.sem_sample_interval == self.sem_counter:
				self.sem_counter = 1
				readings = self.extract_sem_readings()
				#print "DEBUG:: readings for Veris smart meter = ", readings
				if readings:
					self.upload_sem_readings(readings)
			else:
				self.sem_counter += 1

			#EatonIQ260
			if self.Eaton_sample_interval == self.Eaton_counter:
				self.Eaton_counter = 1
				readings = self.extract_Eaton_readings()
				#print "DEBUG:: readings for Eaton smart meter = ", readings
				if readings:
					self.upload_Eaton_readings(readings)
			else:
			 	self.Eaton_counter += 1

			#Ask Netatmo Station for readings
			if self.nws_sample_interval == self.nws_counter:
				self.nws_counter = 1
				readings = self.extract_nws_readings()
				# print "DEBUG:: readings for Netatmo_weather_station = ", readings
				if readings:
					self.upload_nws_readings(readings)
			else:
				self.nws_counter += 1

		except KeyboardInterrupt:
			print ("Inturrput signal received, joining all process")
			self.close()
			sys.exit()

		except:
			print ("Unkown error happend. Please check with logfile.")
			exc_type, exc_value, exc_traceback = sys.exc_info()
			lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
			write_to_log(''.join(line for line in lines))
			self.close()
			sys.exit(1)	