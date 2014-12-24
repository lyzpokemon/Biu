from django.conf.urls import patterns, include, url
from django.contrib import admin
from biuser import views as views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'Biu.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
	url(r'^register$', views.register),
	url(r'^login$', views.login),
	url(r'^logout$', views.logout),
	url(r'^add$', views.add),
	url(r'^heartbeat$', views.heartbeat),
	url(r'^search$', views.search),
	url(r'^friends$', views.friends),
	url(r'^send$', views.send),
)
