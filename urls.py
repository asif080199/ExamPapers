from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from qna import views
import views

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover
dajaxice_autodiscover()
from django.conf import settings

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    (r'^$', views.home),
	(r'^(?P<subj_id>\d*)/$', views.level),

	#survey 
	(r'^(?P<subj_id>\d*)/survey',views.survey),
	
	#contribute
	url(r'^(?P<subj_id>\d*)/contribute/', include('ExamPapers.contribute.urls')),
	
	#search 
	(r'^(?P<subj_id>\d*)/search/(?P<type>\d*)(?P<tp>\d*)(?P<searchtext>\d*)',views.search),
	(r'^(?P<subj_id>\d*)/view/(?P<qid>\d*)/$', views.viewquestion),
	
	#search tag
	(r'^(?P<subj_id>\d*)/searchTag/$',views.searchTag),
	(r'^(?P<subj_id>\d*)/resultTag/(?P<type>\d*)(?P<tp>\d*)(?P<query>\d*)',views.resultTag),
	
	#study
	(r'^(?P<subj_id>\d*)/study/(?P<tp>\d*)', views.study),	
	(r'^(?P<subj_id>\d*)/concept/(?P<conceptId>\d*)', views.concept),	
	(r'^(?P<subj_id>\d*)/tag/(?P<tagId>\d*)', views.tag),	

	#statistics
	(r'^(?P<subj_id>\d*)/statistics/(?P<type>\d*)', views.statistics),	
	
	#account
    (r'^accounts/login/$', views.account_login),
    (r'^accounts/logout/$', views.account_logout),
    (r'^accounts/register/$', views.account_register),
    (r'^accounts/activate/$', views.account_activate),
    (r'^accounts/forgot/$', views.account_forgot),
    (r'^accounts/reset/$', views.account_reset),
	(r'^accounts/profile/$', views.profile),
	
	
	#comments
	url(r'^comments/', include('django.contrib.comments.urls')),
	
	#qna
	url(r'^(?P<subj_id>\d*)/qna/', include('ExamPapers.qna.urls')),

	#searchc
	url(r'^(?P<subj_id>\d*)/searchc/', include('ExamPapers.searchc.urls')),
		
	#control
	url(r'^(?P<subj_id>\d*)/control/', include('ExamPapers.control.urls')),

	#fsearch
	url(r'^(?P<subj_id>\d*)/fsearch/', include('ExamPapers.fsearch.urls')),
	
	#dajax
    (r'^%s/' % settings.DAJAXICE_MEDIA_PREFIX, include('dajaxice.urls')),
	
	url(r'^(?P<subj_id>\d*)/mycontrol/', include('ExamPapers.mycontrol.urls')),
)

# This is needed to serve static files like images and css
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()