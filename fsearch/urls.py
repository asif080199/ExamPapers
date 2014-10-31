from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from fsearch import views
import views

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.practice.views',
	url('home/$', views.home),
	('result/$', views.result),
	('reindex/$', views.reindex),
)
