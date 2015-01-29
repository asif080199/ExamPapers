from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from qna import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('ExamPapers.qna.views',
	url('home/(?P<tp>\d*)', views.home),
	('form/$', views.form),
	('edit/(?P<cId>\d*)/$', views.edit),
	('view/(?P<cId>\d*)/$', views.view),
	('delete/(?P<cId>\d*)/$', views.delete),
	('admin/', views.admin),
)
