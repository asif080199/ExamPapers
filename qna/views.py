# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse

from DBManagement.models import Subject
from qna.models import *
from qna.forms import *
import datetime

def qnaadmin(request,subj_id):
	param = {}
	param.update(current(subj_id))
	questions = Ask.objects.filter(subject_id = subj_id)
	for q in questions:
		q.display = q.content[:200]
	param['questions'] = questions
	return render_to_response(
        'qna/qna.admin.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required	
def qnahome(request,subj_id,tp):
	param = {}
	tp = -1
	if request.GET.get("tp") != None:
		tp = int(request.GET.get("tp"))	
	if tp == -1:
		asks = Ask.objects.filter(subject_id = subj_id).order_by('-created')
	else:
		asks = Ask.objects.filter(topic_id = int(tp)).order_by('-created')
	print asks
	for s in asks:
		s.contentshort = s.content[0:200].replace("<p>","").replace("</p>","")
		s.image = Askfile.objects.filter(ask = s)
		
		for i in s.image:
			i.imageurl = i.docfile.url.replace("resource/","")
		
	#Do paging for asks entries
	paginator = Paginator(asks, 5)
	
	try: page = int(request.GET.get("page", '1'))
	except ValueError: page = 1

	try:
		asks = paginator.page(page)
	except (InvalidPage, EmptyPage):
		asks = paginator.page(paginator.num_pages)
		
	param['asks'] = asks
	
	param.update(current(subj_id))
	param.update(qna(subj_id))
	param.update(qnatopic(subj_id))
	
	return render_to_response(
        'qna/qna.home.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required	
def qnapopular(request,subj_id,tp):
	param = {}
	tp = -1
	if request.GET.get("tp") != None:
		tp = int(request.GET.get("tp"))	
	if tp == -1:
		asks = Ask.objects.filter(subject_id = subj_id).order_by('-view')
	else:
		asks = Ask.objects.filter(topic_id = int(tp)).order_by('-view')
	asks = asks[:10]
	for s in asks:
		s.contentshort = s.content[0:200].replace("<p>","").replace("</p>","")
		s.image = Askfile.objects.filter(ask = s)
		
		for i in s.image:
			i.imageurl = i.docfile.url.replace("resource/","")
		
	#Do paging for asks entries
	paginator = Paginator(asks, 5)
	
	try: page = int(request.GET.get("page", '1'))
	except ValueError: page = 1

	try:
		asks = paginator.page(page)
	except (InvalidPage, EmptyPage):
		asks = paginator.page(paginator.num_pages)
		
	param['asks'] = asks
	
	param.update(current(subj_id))
	param.update(qna(subj_id))
	param.update(qnatopic(subj_id))
	
	return render_to_response(
        'qna/qna.home.html',
        param,
        context_instance=RequestContext(request)
    )	
	
@login_required		
def qnaform(request,subj_id):
	param = {}
	param.update(current(subj_id))
	param.update(qna(subj_id))
	param.update(qnatopic(subj_id))
	if request.method == "POST":
			form = DocumentForm(request.POST, request.FILES ,initial = {'subj_id_pass' : subj_id})	
		
			if form.is_valid():
				sub = Subject.objects.get(id = subj_id)
				t = request.POST['topic']
				newstory = Ask(created =datetime.datetime.now() ,content = request.POST['content'],author = request.user,title = request.POST['title'],subject = sub,topic_id = t)
				newstory.save()
				if request.FILES.get("docfile")!=None:
					newpic = Askfile(docfile = request.FILES['docfile'])
					newpic.ask = newstory
					newpic.save()
				return  HttpResponseRedirect('/'+str(subj_id)+'/qna/view/'+str(newstory.id))
	else:	
			form = DocumentForm(initial = {'subj_id_pass' : subj_id}) 
			param['new'] = 1
	
	param['form'] = form
	return render_to_response(
				'qna/qna.form.html',
				param,
				context_instance=RequestContext(request)
	)

@login_required		
def qnaedit(request,subj_id,askId):
	param = {}
	param.update(current(subj_id))
	param.update(qna(subj_id))
	param.update(qnatopic(subj_id))
	ask = Ask.objects.get(pk=int(askId)) #get current object
			
	if request.method == "POST":
		form = DocumentForm(request.POST, request.FILES ,initial = {'subj_id_pass' : subj_id})	
				
		if form.is_valid():
					print "hey yo"
					sub = Subject.objects.get(id = subj_id)
					t = request.POST['topic']
					ask.content =  request.POST['content']
					ask.title = request.POST['title']
					ask.topic_id = t
					ask.save()
					if request.FILES.get("docfile")!=None:
						newpic = Askfile(docfile = request.FILES['docfile'])
						oldpic = Askfile.objects.filter(ask = ask)
						oldpic.delete()
						newpic.ask = ask
						newpic.save()
					return  HttpResponseRedirect('/'+str(subj_id)+'/qna/view/'+str(ask.id))
	else:	
				form = DocumentForm(instance = ask, initial = {'subj_id_pass' : subj_id}) 
	param['form'] = form
	return render_to_response(
					'qna/qna.form.html',
					param,
					context_instance=RequestContext(request)
	)

@login_required	
def qnaview(request,subj_id,askId):
	current_user = request.user.id
	param = {}
	param.update(qnatopic(subj_id))
	param.update(current(subj_id))
	param.update(qna(subj_id))
	
	a = Ask.objects.get(id= askId)
	a.image = Askfile.objects.filter(ask = a)
	
	for i in a.image:
		i.imageurl = i.docfile.url.replace("resource/","")
	
	"Vote"
	if request.POST.get("vote") != None:
		vote = request.POST.get("vote")
		if vote == "up":
			a.voteUp = a.voteUp+1
		elif vote == "down":
			a.voteDown = a.voteDown+1
		print a.voteUp
		a.save()
	else:
		a.view = a.view+1
		a.save()
		
	param['ask'] = a
	return render_to_response(
        'qna/qna.view.html',
        param,
        context_instance=RequestContext(request)
    )

@login_required	
def qnadelete(request,subj_id,askId):
	current_user = request.user.id
	param = {}
	a = Ask.objects.get(id= askId)
	a.image = Askfile.objects.filter(ask = a)
	for i in a.image:
		i.imageurl = i.docfile.url.replace("resource/","")
	a.view = a.view+1
	a.delete()
	return qnahome(request,subj_id,1)


def qnaaccount(request,subj_id):
	current_user = request.user
	param  = {}
	param.update(qnatopic(subj_id))
	mAsk = Ask.objects.filter(author = current_user)
	param["asks"] = mAsk
	param.update(current(subj_id))
	param.update(qna(subj_id))
	return render_to_response(
        'qna/qna.account.html',
        param,
        context_instance=RequestContext(request)
    )

	
def current(subj_id):
	param = {}
	param['cur'] = Subject.objects.get(id = subj_id)
	param['level'] = Subject.objects.all()
	return param


def qna(subj_id):
	param = {}
	populars = Ask.objects.filter(subject_id = subj_id).order_by('-view')[0:3]
	recents = Ask.objects.filter(subject_id = subj_id).order_by('-created')[0:3]
	param['populars'] = populars
	param['recents'] = recents
	return param
	
def qnatopic(subj_id):
	param = {}
	blocks = Block.objects.filter(subject_id = subj_id)
	for b in blocks:
		b.topics = Topic.objects.filter(block_id = b.id)
		for t in b.topics:
			t.count = Ask.objects.filter(topic_id = t.id).count()
	param['blocks'] = blocks
	return param