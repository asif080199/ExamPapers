from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from searchc import views
import views

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.searchc.views',
	url	('homeFormula/$', views.homeFormula),
		('homeTag/$', views.homeTag),
		('homeText/$', views.homeText),
		('cluster/$', views.cluster),
		('resultFormula/',views.resultFormula),
		('resultTag/',views.resultTag),
		('resultText/(?P<type>\d*)(?P<cluster>\d*)(?P<query>\d*)',views.resultText),
)
