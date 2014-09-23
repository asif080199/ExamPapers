from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
from DBManagement.models import *
import datetime


from ExamPapers.logic.common import *
from ExamPapers.logic.question_processing import *
from ExamPapers.logic.ans_check import *


@login_required	
def home(request,subj_id):
	param = {}
	param.update(current(subj_id))
	subjects = Subject.objects.get(id = subj_id)
	subjects.topics = Topic.objects.filter(block__subject__id = subjects.id)
	for t in subjects.topics:
		t.allquestion = Question.objects.filter(topic__id = t.id)
		all = t.allquestion.count()
		t.history = 0
		for p in t.allquestion:
			if Progress.objects.filter(user_id = request.user).filter(question_id = p.id).count() != 0 :
				t.history = t.history + 1
		if all!= 0:
			t.progress = t.history*100/all
		else:
			t.progress = 0
		t.all = all
	param['s'] = subjects
	return render_to_response( 'practice/practice.home.html',param,context_instance=RequestContext(request)
    )

@login_required	
def question(request, subj_id, tp, qid):
	u = request.user
	
	param  = {}
	param.update(current(subj_id))
	
	user_input = ["n\\pi\\pm \\frac{4}{24}\\pi"]
	qid = "199703003008"
	param.update(check_qns_solution(qid,user_input))
	
	answer = Answer.objects.filter(question_id = qid)
	a = display_finalanswer(answer)
	print "_________"
	for b  in a:
		print b
	
	
	if request.GET.get("qid") != None:
		qid = request.GET.get("qid")	
	# if no question selected --> default do 1st question
	if int(qid) == 0 or qid == None:
		qid = questions[0]

	
	#now write to history
	if Progress.objects.filter(question_id_id = qid).filter(user=u).count() == 0:
		history = Progress(user=u, question_id=Question.objects.get(id = qid))
		history.save()
	
	#Recommend questions in the same topic
	questions = Question.objects.filter(topic_id = tp)
	
	#Return param
	param['tp'] = tp	
	param['questions'] = questions
	param['question'] = getViewQuestion(qid)
	#param['answer'] = getAnswer(qid)
	return render_to_response(
        'practice/practice.question.html', param, context_instance=RequestContext(request)
    )
	