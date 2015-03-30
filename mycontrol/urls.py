from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from mycontrol import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.mycontrol.views',
	url('qHome', views.qHome),
	('qList/$', views.qList),
	('qForm/$', views.qForm),
	('qUpdate/$', views.qUpdate),
	('qDelete/$', views.qDelete),
	
	('tHome/$', views.tHome),
	('tUpdate/$', views.tUpdate),
	('tForm/$', views.tForm),
	
	('sHome/$', views.sHome),
)
