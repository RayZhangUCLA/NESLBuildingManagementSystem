from django.conf.urls import patterns, url
from data_visualization import views

urlpatterns = patterns('',
	url(r'^$', views.index),
	url(r'^dashboard/$', views.dashboard, name='dashboard'),
	url(r'^dashboard/history_data/$', views.get_history_data, name='history_data'),
	url(r'^dashboard/current_data/$', views.get_current_data, name='current_data'),
	url(r'^dashboard/proportions/$', views.get_proportions, name='proportions'),
	url(r'^dashboard/energy/$', views.get_energy, name='energy'),
	####Created for 202B class project
	url(r'^dashboard/homeview/$',views.get_homeview, name='home'),
	url(r'^dashboard/mapview/$',views.get_mapview, name='map'),
	url(r'^dashboard/power/$',views.get_powerTab, name='powerTab'),
	url(r'^dashboard/water/$',views.get_waterTab, name='waterTab'),
	url(r'^dashboard/control/$',views.get_controlTab, name='controlTab'),
	url(r'^dashboard/control_scheduler/$',views.get_control_schedulerTab, name='control_schedulerTab'),
	####API to get data for map
	url(r'^dashboard/layout_data/$', views.get_house_layout_data, name="layout_data"),
	####hour till now data
	url(r'^dashboard/running_total/$', views.get_hourTotal, name="hourly_data"),
	#### Get smap average data of a given window
	url(r'^dashboard/smap_query/$', views.get_smap_query, name="smap_query"),
	#### Get data from database by hours
	url(r'^dashboard/db_query/$', views.get_db_query, name="db_query")
)
