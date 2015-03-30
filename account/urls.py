from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from account import views

urlpatterns = patterns('ExamPapers.account.views',
	url('login/$', views.account_login),
	('logout/$', views.account_logout),
    ('register/$', views.account_register),
    ('activate/$', views.account_activate),
    ('forgot/$', views.account_forgot),
    ('reset/$', views.account_reset),
	('profile/$', views.profile),
)

