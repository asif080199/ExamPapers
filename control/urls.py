from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from control import views


from django.conf import settings



urlpatterns = patterns('ExamPapers.control.views',
	url('home/(?P<tp>\d*)', views.home),
	('question/(?P<qid>\d*)/$', views.question),
	('edit/(?P<qid>\d*)/$', views.edit),
)
