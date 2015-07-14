# NESLBuilingManagementSystem

# Overview

This is my undergraduate research project in NESL lab. It is a building management system that is supposed to have three parts: sensor data collections, data visualizations, and data analysis. 

For data collection, ideally, it is achieved through an embedded computer extracting readings from different types of sensors in a room and uploading them to servers. It can also be achieved through third party platforms directly sending data to lab servers. In practice, in NESL lab, we have a Beaglebone Black(BBB) in the lab reading data from smart power panels, Netatmo Weather Station, RFduino. We also have motion sensor readings directly from Smartthings(http://www.smartthings.com/) servers. The software achitecture used for data collection is sMAP.(Please refer to http://www.cs.berkeley.edu/~stevedh/smap2/ for details) In this case, our lab servers function as a sMAP Archiver(sMAP server) and the Beaglebone Black function as a sMAP source(sMAP client) under this achitecture. Once installed, one only needs to write Python codes to implement the sMAP client part. Please refer to Data Collection parts for details.

For data visualzation, it is a web-based dashboard showing running status of all sensors in a paticular room. It can also be used for acutations of sensors in that room.(sMAP supports sensor actuations) Currently, the web-based platform is implemented through Django 1.7.(https://www.djangoproject.com/) We choose Django because it is scalable and easy to use. Please refer to Data Visualization parts for detail.

The data analysis part has not been implemented yet. Hopefully, it will be done by students in NESL lab after me. 

# Data Collection

As mentioned, under sMAP achitecture, one only needs to implement the sMAP client parts. In the case of NESL lab sonsors, we have two sMAP clients running: the BBB and the lab server. (Yes, the lab server is used as sMAP server and client at the same time) The sMAP client on BBB is used to read data from smart power panels, Netatmo Weather Station, Bluetooth 3.0 and 4.0 sensors, and the sMAP client on lab server is to receive data from Smartthings motion sensors. We choose to directly send data from Smartthings servers to lab servers because, otherwise, we have to send them to Beaglebone Black and then redirect them to lab servers. 

For sMAP client on Beaglebone Black, you can find them at 'NESLBuildingManagementSystem/BeagleBoneBlack Source'. On BBB, the sMAP driver codes is located at '/usr/local/lib/python2.7/dist-packages/smap/drivers/BBB_sensors.py' and the sMAP configuration file is located at '/root/sources/conf/Beaglebone.ini'. (Please read sMAP documentations if you do not know what they are) The codes consist of serveral parts, each corrosponds to one of the few sensors it reads from:
1.'BT_client' function is for Bluetooth 3.0 sensors. For some reasons, I did not get actual Bluetooth 3.0 sensors, so I wrote an Android App for testing purposes. You can find it at https://github.com/RayZhangUCLA/BluetoothSensorSimulator. So, 'BT_client' is mainly for communicating to this Android App in this case.
2.'RFduino_client' is for Bluetooth 4.0 sensors. In this case, we use RFduino, but the codes can easily be modified to be compatible with other BLE sensors. The RFduino sketch can be found at 'NESLBuildingManagementSystem/RFduino Sketch'. 
3.'SEM_client' and 'Eaton_SEM_handler' are for two smart power meters we use:VerisE30A042 and EatonIQ260. There are some helper codes at a subfoder called 'BBB_helper_class' in the same folder where BBB_sensor.py is located, both in github and BBB. They are named 'VerisE30A042.py' and 'EatonIQ260.py'.
4.'Netatmo_client' is for Netatmo weather station. Its helper codes are also located at 'BBB_helper_class' with name 'NetatmoWeatherStation.py'. The codes will write error message to '~/sources/conf/BBB_smap_Log.txt'.

For sMAP client on lab server, you can find them at 'NESLBuildingManagementSystem/Smartthings Source' or '/usr/local/lib/python2.7/dist-packages/smap/drivers/SmartThings.py' for codes and '/home/ray/sources/samp-data-read-only/python/conf/SmartThings.ini' on lab server.

# Data Visualization

The web-based dashboard uses Django as backend support with sqlite3 databases and Bootstrap(http://getbootstrap.com/) as frontend frameworks. The frontend also uses serveral css and javascript libraries as support for graphical functionalities:front-awesome(http://fortawesome.github.io/Font-Awesome/), raphael(http://raphaeljs.com/), morris(http://morrisjs.github.io/morris.js/), and highcharts(http://www.highcharts.com/). 

For this part, I worked with three other students from Prof Mani's class. Please go to this README page(NESLBuildingManagementSystem/BMS_nesl_frontend/data_visualization/README.md) for more details. The codes can be found at BMS_nesl_frontend folder or '~/source/Django_frontend/'.

Beside this dashboard, I also implemented an RESTful api and an iframe widget under the same port. The codes can be found at 'RESTful_API' and 'visual_widget' folder respectively. 
For RESTful API, please goto view.py to see its usage. In order to speed up the query for statistic, I decide to calculate key statistics in advance and save them to time-series database influxDB(https://influxdb.com/) every day. I used 'cron' command to schecule this activity. To modify, one only need to run 'sudo crontab -e' command. The command will output error message to ''~/source/Django_frontend/BMS_nesl_frontend/calc_stats_log.txt'
FOr visual widget, the idea is that it should allow you to insert the realtime plot or history plot of any data stream to any html page through iframe. The usage is as follows:
  <iframe src="http://ip:port/widget/realtime(or history)?uuid=&width=&height="  width="" height="" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" align="left" vspace="0" hspace="0"></iframe>

# Data Analysis

Comming soon

# Known issues
1. Netatmo Weather Station reading on BBB seems to have authentication problem in my recent check. Look like the Netatmo server returns HTTP301 'service moved permanently' error. I do notice that Netatmo servers change their servers from time to time. One may need to check their latest documentations for further instructions. 
2. calc_stats command(located at 'NESLBuildingManagementSystem/BMS_nesl_frontend/data_visualization/management/commands/calc_stats.py') for RESTful API seems to stop working now. I suspect that the reason is that when we updated the sMAP server with data streams for hometype, something is messed up.