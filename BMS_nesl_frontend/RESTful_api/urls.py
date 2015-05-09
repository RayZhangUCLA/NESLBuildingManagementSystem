from django.conf.urls import patterns, url
from RESTful_api import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^path$', views.Path, name='path'),
    url(r'^uuid$', views.UUID, name='uuid'),
    url(r'^properties', views.Properties, name='properties'),
    url(r'^data$', views.Data, name='data'),
    url(r'^statistics', views.Statistics, name='statistics'),
)