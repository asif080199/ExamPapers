from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from searchf import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.searchf.views',
	url('reindex/$', views.reindex),
	('home/$', views.home),
	('result/(?P<type>\d*)(?P<tp>\d*)(?P<query>\d*)',views.result),
)
