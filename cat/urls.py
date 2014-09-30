from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from cat import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.cat.views',
	url('home/', views.trialtest),
	('generate/$', views.trialtest_generate),
	('go/(?P<test_id>\w+)/$', views.trialtest_go),
)
