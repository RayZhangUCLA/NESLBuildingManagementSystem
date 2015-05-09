from django.conf.urls import patterns, url
from visual_widget import views
from data_visualization.views import load_data


urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^history', views.history_plot, name='history_plot'),
    url(r'^realtime', views.realtime_plot, name='realtime_plot'),
    url(r'^current_val/$', views.current_val, name='current_val'),
    url(r'^load_data/$', load_data, name='data_loader'),
)