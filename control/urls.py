from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from control import views


from django.conf import settings



urlpatterns = patterns('ExamPapers.control.views',
	url
	('home/',views.AddMaths_Admin),
	('math_admin/$',views.AddMaths_Admin),
	('math_admin_list/(?P<list_type>.*)/(?P<page_no>\d*)/$',views.AddMaths_Admin_ModifyQuestion),
	('math_admin_form/(?P<list_type>.*)/(?P<page_no>\d*)/(?P<list_id>.*)/(?P<question_id>-?\d*)/$',views.AddMaths_Admin_QuestionForm),
	#('math_admin_preview/$',views.AddMaths_qPreview),
	('math_admin_modify/(?P<list_type>.*)/(?P<page_no>\d*)/$',views.AddMaths_qChange),
	('math_admin_delete/(?P<list_type>.*)/(?P<page_no>\d*)/$',views.AddMaths_qDelete),
	('math_admin_taglist/$',views.AddMaths_Admin_TagList),
	#('math_admin_regenkeyword/$',views.AddMaths_Admin_RegenKeyword),
	#('math_admin_regenformula/$',views.AddMaths_Admin_ReindexFormulae),
	#('math_admin_formula/$',views.AddMaths_Admin_Formula),
	('math_admin_tag_delete/$',views.AddMaths_Admin_DeleteTag),
	('math_admin_tag_form/$',views.AddMaths_Admin_TagForm),
	('math_admin_tag_save/$',views.AddMaths_Admin_SaveTag),
)
