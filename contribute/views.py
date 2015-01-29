# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse

from DBManagement.models import Subject
from contribute.models import *
from contribute.forms import *
import datetime

def admin(request,subj_id):
	param = {}
	param.update(current(subj_id))
	questions = QuestionC.objects.filter(subject_id = subj_id)
	for q in questions:
		q.display = q.content[:200]
	param['questions'] = questions
	return render_to_response(
        'contribute/contribute.admin.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required	
def home(request,subj_id,tp):
	param = {}
	questions = QuestionC.objects.all()
	for q in questions:
		q.image = FileC.objects.filter(questionC = q).count()
		q.display = q.content[:300]
	param['questions'] = questions
	param.update(current(subj_id))
	
	
	
	return render_to_response(
        'contribute/contribute.home.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required		
def form(request,subj_id):
	param = {}
	param.update(current(subj_id))
	
	
	if request.method == "POST":
			form = ContributeForm(request.POST, request.FILES ,initial = {'subj_id_pass' : subj_id})	
	
			if form.is_valid():
				topic = request.POST['topic']
				subtopic = request.POST['subtopic']
				content = request.POST['content']
				solution = request.POST['solution']
				source = request.POST['source']
				title = request.POST['title']
				subject = request.POST['subject']
	
				
				newstory = QuestionC(created =datetime.datetime.now() ,solution = solution,content = content,author = request.user,title = title,subject_id = subject,topic_id = topic, subtopic_id = subtopic)
				newstory.save()
				if request.FILES.get("docfile")!=None:
					print "hahahah"
					newpic = FileC(docfile = request.FILES['docfile'])
					newpic.questionC = newstory
					newpic.save()
					print "_--------------------"
					print newpic
				return  HttpResponseRedirect('/'+str(subj_id)+'/contribute/view/'+str(newstory.id))
	else:	
			form = ContributeForm(initial = {'subj_id_pass' : subj_id}) 
	
	param['form'] = form
	return render_to_response(
				'contribute/contribute.form.html',
				param,
				context_instance=RequestContext(request)
	)

@login_required		
def edit(request,subj_id,QuestionCId):
	param = {}
	param.update(current(subj_id))
	
	
	QuestionC = QuestionC.objects.get(pk=int(QuestionCId)) #get current object
			
	if request.method == "POST":
		form = ContributeForm(request.POST, request.FILES ,initial = {'subj_id_pass' : subj_id})	
				
		if form.is_valid():
					sub = Subject.objects.get(id = subj_id)
					t = request.POST['topic']
					QuestionC.content =  request.POST['content']
					QuestionC.title = request.POST['title']
					QuestionC.topic_id = t
					QuestionC.save()
					if request.FILES.get("docfile")!=None:
						newpic = QuestionCfile(docfile = request.FILES['docfile'])
						oldpic = QuestionCfile.objects.filter(QuestionC = QuestionC)
						oldpic.delete()
						newpic.QuestionC = QuestionC
						newpic.save()
					return  HttpResponseRedirect('/'+str(subj_id)+'/contribute/view/'+str(QuestionC.id))
	else:	
				form = ContributeForm(instance = QuestionC, initial = {'subj_id_pass' : subj_id}) 
	param['form'] = form
	return render_to_response(
					'contribute/contribute.form.html',
					param,
					context_instance=RequestContext(request)
	)

@login_required	
def view(request,subj_id,cId):
	current_user = request.user.id
	param = {}
	
	param.update(current(subj_id))
	
	
	a = QuestionC.objects.get(id= cId)
	a.image = FileC.objects.filter(questionC = a)
	
	for i in a.image:
		i.imageurl = i.docfile.url.replace("resource/","")
	

		
	param['question'] = a
	return render_to_response(
        'contribute/contribute.view.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required	
def delete(request,subj_id,cId):
	current_user = request.user.id
	param = {}
	a = QuestionC.objects.get(id= cId)
	a.image = FileC.objects.filter(questionC = a)
	for i in a.image:
		i.imageurl = i.docfile.url.replace("resource/","")
	a.delete()
	return home(request,subj_id,1)


def contributeaccount(request,subj_id):
	current_user = request.user
	param  = {}
	
	mQuestionC = QuestionC.objects.filter(author = current_user)
	param["QuestionCs"] = mQuestionC
	param.update(current(subj_id))
	
	return render_to_response(
        'contribute/contribute.account.html',
        param,
        context_instance=RequestContext(request)
    )

	
def current(subj_id):
	param = {}
	param['cur'] = Subject.objects.get(id = subj_id)
	param['level'] = Subject.objects.all()
	return param


	