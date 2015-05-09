from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'BMS_nesl_frontend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', include('data_visualization.urls')),
    url(r'^data_visualization/', include('data_visualization.urls')),
    url(r'^api/', include('RESTful_api.urls')),
    url(r'^widget/', include('visual_widget.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
