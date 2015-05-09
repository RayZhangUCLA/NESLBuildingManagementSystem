# Author: Tianrui Zhang, NESL, UCLA
# Created on: Sep 11, 2014

import httplib, json, time
from urllib import urlencode
from sys import exit
from datetime import datetime
import os

#Constants for Netatmo services
host_url = "api.netatmo.net"
token_path = "/oauth2/token"
user_path = "/api/getuser"
devicelist_path = "/api/devicelist"
get_measure_path = "/api/getmeasure"


def write_to_log(msg):
	path = os.path.expanduser('~/sources/conf/BBB_smap_Log.txt')
	with open(path, "a") as logfile:
		current_datetime = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
		logfile.write(str(current_datetime) + " " + msg +"\n")

class NetatmoWeatherStation():
	def __init__(self, 
				client_id="",
				client_secret="",
				username="",
				password="",
				scope="read_station",
				grant_type="password"):
		if client_id=="" or client_secret=="" or username=="" or password=="":
			# print ("Client id, Client secret, username and password are required to have Netatmo online services. Program exits")
			exit(1)
		self.params = {}
		self.params['grant_type'] = grant_type
		self.params['client_id'] = client_id
		self.params['client_secret'] = client_secret
		self.params['username'] = username
		self.params['password'] = password
		self.params['scope'] = scope
		self.httpconn = httplib.HTTPConnection(host_url)
		self.expiration_time = time.time()

	def __del__(self):
		self.httpconn.close()

	#Authenticate required before using netatmo APIs
	def authentication(self):
		header = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
					'Host': host_url}
		body = urlencode(self.params)
		json_response = self.HTTP_request_to_Host('POST', token_path, body, header)
		if json_response == None:
			# print ("Authentication failed. Unable to get access token.")
			return False
		else:
			self.access_token = json_response["access_token"]
			self.refresh_token = json_response["refresh_token"]
			self.expiration_time = int(json_response["expires_in"]) + time.time()
			# print ("Authentication successful. Ready to use Netatmo API services.")
			return True

	#Refresh access token if it expires
	def reauthenticate_if_needed(self):
		if time.time() > self.expiration_time:
			# print ("Access token expires. Reauthenticating...")
			write_to_log("Access token expires. Reauthenticating...")
			header = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
						'Host': host_url}
			body = {'grant_type': 'refresh_token', 
					'refresh_token': self.refresh_token,
					'client_id': self.params['client_id'],
					'client_secret': self.params['client_secret']}
			body = urlencode(body)
			json_response = self.HTTP_request_to_Host('POST', token_path, body, header)
			if json_response == None:
				# print ("Refreshing access token failed. Unable to get access token.")
				write_to_log("Refreshing access token failed. Unable to get access token.")
				return False
			else:
				self.access_token = json_response["access_token"]
				self.refresh_token = json_response["refresh_token"]
				self.expiration_time = int(json_response["expires_in"]) + time.time()
				# print ("Refreshing access token successful.")
				write_to_log("Refreshing access token successful.")
				return True
		return True

	#netatmo APIs related to weather station
	def get_user(self):
		if time.time() > self.expiration_time:
			# print ("Access token expired. Please refresh access token before using netatmo API services.")
			return None
		else:
			url = user_path + "?access_token=%s" % self.access_token
			header = {'Host': host_url}
			json_response = self.HTTP_request_to_Host('GET', url, "", header)
			return json_response

	def get_devicelist(self, app_type="", device_id=""):
		if time.time() > self.expiration_time:
			# print ("Access token expired. Please refresh access token before using netatmo API services.")
			return None
		else:
			url = devicelist_path + "?access_token=%s" % self.access_token
			if app_type != "":
				url = url + "&app_type=%s" % app_type
			if device_id != "":
				url = url + "&device_id=%s" % device_id
			header = {'Host': host_url}
			json_response = self.HTTP_request_to_Host('GET', url, None, header)
			return json_response

	def get_measure(self, device_id, scale, measurement_type, 
					module_id=None, date_begin=None, date_end=None, limit=None, optimize="False", real_time="False"):
		if time.time() > self.expiration_time:
			print ("Access token expired. Please refresh access token before using netatmo API services.")
			return None
		else:
			params = {
				'access_token': self.access_token,
				'device_id': device_id,
				'scale': scale,
				'type': measurement_type,
				'optimize': optimize,
				'real_time': real_time
			}
			if module_id != None: 
				params['module_id']= module_id
			if date_begin != None: 
				params['date_begin'] = date_begin
			if date_end != None:
				params['date_end'] = date_end
			if limit != None:
				params['limit'] =  limit
			body = urlencode(params)
			header = {'Host': host_url}
			json_response = self.HTTP_request_to_Host('POST', get_measure_path+"?"+body, None , header)
			return json_response

	def get_params(self):
		return self.params

	def close_http_conn(self):
		self.httpconn.close()

	#Helper functions
	def HTTP_request_to_Host(self, method, url, body, header):
		for i in range(5):
			try:
				self.httpconn.request(method, url, body, header)
				resp = self.httpconn.getresponse()
				if resp.status != httplib.OK:
					write_to_log("HTTP %s to %s returns error message:\n" % (method, host_url+url))
					write_to_log("HTTP%s" % resp.version + resp.status + resp.reason)
					# print "HTTP %s to %s returns error message:\n" % (method, host_url+url)
					# print "HTTP%s" % resp.version, resp.status, resp.reason
					# print resp.msg
					# print resp.read()
					return None
				else:
					return json.loads(resp.read())
			except httplib.BadStatusLine:
				# write_to_log("Netatmo Server return BadStatusLine")
				self.close_http_conn()
