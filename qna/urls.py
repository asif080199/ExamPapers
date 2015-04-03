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
	url('home/(?P<tp>\d*)', views.qnahome),
	#('submit/$', views.submit),
	('popular/(?P<tp>\d*)$', views.qnapopular),
	('form/$', views.qnaform),
	('edit/(?P<askId>\d*)/$', views.qnaedit),
	('view/(?P<askId>\d*)/$', views.qnaview),
	('delete/(?P<askId>\d*)/$', views.qnadelete),
	('account/', views.qnaaccount),
	('admin/', views.qnaadmin),
)
