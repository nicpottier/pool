from . import views
from django.conf.urls import url

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^player/(?P<player_id>[0-9]+)/$', views.player, name='player'),
]
