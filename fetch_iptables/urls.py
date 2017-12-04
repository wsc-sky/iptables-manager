from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^check_angent_status/(?P<ip>[0-9a-zA-Z\.]+)/(?P<plat_id>\w+)$', views.check_angent_status),
    # url(r'^fetch_ptables/(?P<ip>[0-9a-zA-Z\.]+)$', views.fetch_ptables),
    url(r'^search_by_ip', views.search_by_ip),
    url(r'^submit_iptables', views.submit_iptables),

]