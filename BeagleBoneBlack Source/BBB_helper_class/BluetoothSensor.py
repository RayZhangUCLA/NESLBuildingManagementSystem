#Author: Tianrui Zhang, NESL, UCLA
#Created on Sep 4th, 2014

import bluetooth
import sys

class BluetoothSensor():
	def __init__(self):
		pass

	# Establish bluetooth connection, return address of connected bluetooth device
	def listen_for_connection(self):
		try:
			server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

			#NOTE: bluetooth.PORT_ANY is port 0. It works previously with Angstrom version, but not BBB debian. I suspect it is a bug of pybluez.
			port = bluetooth.PORT_ANY 
			server_sock.bind(("", port))
			server_sock.listen(1)
			print "Listening for SPP connection on port %d" % port

			uuid = "00001101-0000-1000-8000-00805F9B34FB"
			bluetooth.advertise_service(server_sock, "Serial Port", uuid)

			client_sock, address = server_sock.accept()
			print "Accepted connection from ", address
			server_sock.close()
			self.bt_sock = client_sock
			self.bt_address = address

			return address
		except KeyboardInterrupt:
			print "Keyboard singal received. Terminate bluetooth connection"
			self.close_connection()
			sys.exit()

	def initiate_connection(self, params={}, attempt=1, attempt_interval=5):
		for i in range(attempt):
			try:
				port = ""
				name = ""
				host = ""
				if len(params) == 0:
					uuid = "00001101-0000-1000-8000-00805F9B34FB"
					service_matches = bluetooth.find_service(uuid = uuid)

					if len(service_matches) == 0:
						print "No SPP device available arround"
						sys.exit()

					first_match = service_matches[0]
					port = first_match["port"]
					name = first_match["name"]
					host = first_match["host"]
				else:
					host = params["host"]
					port = params["port"]
					if "name" in params:
						name = params["name"]
					else:
						name = "Unknown Bluetooth Sensor"
				print "Connecting to %s on %s" % (name, host)

				client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
				client_sock.connect((host, port))
				print "connection succesfull"
			except bluetooth.BluetoothError:
				print "Cannot create connection to device %s" % name
				if attempt>0:
					print "Retrying in %d seconds..." % attempt_interval
					time.sleep(attempt_interval)
			except KeyboardInterrupt:
				print "Interrupt singal received. Terminate bluetooth connection."
				sys.exit()

	def change_socket(self, new_socket):
		self.bt_sock = new_socket

	def get_bt_socket(self):
		return self.bt_sock

	def get_bt_address(self):
		return self.bt_address

	def close_connection(self):
		self.bt_sock.close()

	#refer to BBB_sensors.py for current data packet format
	def get_readings(self, size=1027):
		data = self.bt_sock.recv(size)
		return data

	def send_readings(self, data):
		self.bt_sock.send(data)


