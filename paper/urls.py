from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from paper import views


urlpatterns = patterns('ExamPapers.paper.views',
	url('home/$', views.papertest),
	url('papertest/(?P<test_id>\w+)/$', views.papertest),
	url('solution/(?P<test_id>\w+)/$', views.solution),
	url('question/(?P<test_id>\w+)/$', views.question),
)