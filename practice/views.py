from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
from DBManagement.models import *
import datetime
import operator

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
	#qid = "199703003008"
	param.update(check_qns_solution(qid,user_input))

	
	#Recommend questions in the same topic
	questions = Question.objects.filter(topic_id = tp)
	if request.GET.get("qid") != None:
		qid = request.GET.get("qid")	
	# if no question selected --> default do 1st question
	if int(qid) == 0 or qid == None:
		qid = questions[0].id

	
	#now write to history
	if Progress.objects.filter(question_id_id = qid).filter(user=u).count() == 0:
		history = Progress(user=u, question_id=Question.objects.get(id = qid))
		history.save()

	#Return param
	param['tp'] = tp	
	param['questions'] = questions
	param['question'] = getViewQuestion(qid)
	param['answers'] = getAnswer(qid)
	return render_to_response(
        'practice/practice.question.html', param, context_instance=RequestContext(request)
    )

def getAnswer(qid):
	answers = Answer.objects.filter(question_id = qid)
	return display_finalanswer(answers)

def submit(request,subj_id):
	param = {}
	param.update(current(subj_id))
	user_input_dict = {}
	
	""" Terrible walkaround. Please :( """
	if request.method == "POST":
		qid = request.POST['qid']
		for key in request.POST:
			value = request.POST[key]
			if key!= "csrfmiddlewaretoken":
				user_input_dict[(key[1:])] = value
	
	keys = []
	for key in user_input_dict:
		keys.append(key)
	keys.sort()
	
	user_input = []
	for key in keys:
		user_input.append(user_input_dict.get(key))
	""" ------------------------- """
	
	# Now check with given answer	
	param.update(check_qns_solution(qid,user_input))
	
	# Prepare for display result 
	results = []
	
	for i in range(len(user_input)-1):
		result = param['resultList'][i]
		tem = []
		if result == 'True':
			tem = [user_input[i],1]
		else:
			tem = [user_input[i],0]
		
		results.append(tem)
	
	param['question'] = getViewQuestion(qid)
	param['results']  = results
	param['answers'] = getAnswer(qid)
	param['lenuser_input'] = len(user_input)-1
	return render_to_response('practice/practice.submit.html', param, context_instance=RequestContext(request))