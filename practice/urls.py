from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from practice import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.practice.views',
	url('home/$', views.home),
	('question/(?P<tp>\d*)/(?P<qid>\d*)/$', views.question),
	('submit/$', views.submit),
)
