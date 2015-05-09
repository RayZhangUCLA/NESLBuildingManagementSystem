from django.conf.urls import patterns, url
from data_visualization import views

urlpatterns = patterns('',
    url(r'^$', views.index),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^dashboard/nav_bar/$', views.nav_bar_loader, name='nav_bar_loader'),
    url(r'^dashboard/load_data/$', views.load_data, name='data_loader'),
    url(r'^dashboard/current_val/$', views.current_val, name='current_val'),
    url(r'^dashboard/data_statistics/$', views.data_statistics, name='statistics'),
)
