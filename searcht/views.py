from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from DBManagement.models import *
from haystack.query import SearchQuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
path = path = os.getcwd()
import json
import datetime
import operator
from ExamPapers.views import star
from django.contrib.auth.decorators import login_required, user_passes_test

def current(subj_id):
	param = {}
	param['cur'] = Subject.objects.get(id = subj_id)
	param['level'] = Subject.objects.all()
	return param

def reindex(request,subj_id):
	param = {}
	param.update(current(subj_id))
	tagAll = TagDefinition.objects.filter(type = "K")|TagDefinition.objects.filter(type = "C").filter(topic__block__subject_id = subj_id)|TagDefinition.objects.filter(type = "K").filter(topic__block__subject_id = subj_id)
	index = {}
	for tag in tagAll:
		title = str(tag.title)
		index[title] = []
		tags = Tag.objects.filter(tagdefinition_id = tag.id)
		for t in tags:
			index[title].append( str(t.question_id))
	with open(path+"/index/tagIndex"+str(subj_id)+".json", 'w') as outfile:
		json.dump(index, outfile)
	
	return render(request,'searcht/reindex.html', param)	
	
@login_required	
def home(request,subj_id):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = subj_id)
	param['type'] = "question"
	
	param['allTag'] = getTag(subj_id)
	
	return render(request,'searcht/home.html', param)

def getTag(subj_id):
	allTag = []
	tag1 = TagDefinition.objects.filter(type="K")
	tag2 = TagDefinition.objects.filter(type="C").filter(topic__block__subject_id = subj_id)
	tag3 = TagDefinition.objects.filter(type="F").filter(topic__block__subject_id = subj_id)
	for tag in tag1:
		allTag.append(str(tag.title))
	for tag in tag2:
		allTag.append(str(tag.title))
	for tag in tag3:
		allTag.append(str(tag.title))
	return allTag
	
@login_required			
def result(request,subj_id,type,tp,searchtext):
	total = 0
	param={}
	input = ""
	tp = -1
	if request.GET.get("searchtext") != None:
		input = request.GET.get("searchtext")
	if request.GET.get("type") != None:
		type = request.GET.get("type")		
	if request.GET.get("tp") != None:
		tp = request.GET.get("tp")	
	tags = input.split(",")
	#update cur and subj	
	param.update(current(subj_id))
	
	
	#get all block 
	blocks = Block.objects.filter(subject_id = subj_id)
		
	#get all topics
	for b in blocks:
		b.topics = Topic.objects.filter(block = b.id)
	
	#get all match question
	questions = tagSearch(input,subj_id)
	
	
	finalQuestions = []
	if type == "question":
	
		# question count
		for b in blocks:
			
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic.id == t.id:
						t.count = t.count + 1
						q.linkId = q.id
						q.stars = star(int(q.marks*5/16.0)+1)
						q.images = Image.objects.filter(qa_id = q.id)
						if q.title == None:
							q.title = str(q.subtopic.title)  +" #" + str(q.question_no)
						if q.images.count() > 0:
							q.image = q.images[0].imagepath
						q.content_short = q.content[0:250]
				total+=t.count
				
			
	elif type == "image":
		for question in questions:
			question.images = Image.objects.filter(qa_id = question.id)
			question.count = question.images.count()
			question.linkId = question.id
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic.id == t.id:
						t.count = t.count + q.count
			total+=t.count
	
	for question in questions:
		if str(question.topic.id) == str(tp) or tp == '-1':
			finalQuestions.append(question)
		
	if tp!= str(-1):
		param['topic'] = Topic.objects.get(id = tp).title
	else:
		param['topic'] = "All"

	param['blocks'] = blocks
	param['total'] = total
	param['type'] = type
	param['questions'] = finalQuestions
	param['tp'] = int(tp)
	
	param['searchtext'] = input
	for q in questions:
		formula = Formula.objects.filter(question = q.id)

	param['allTag'] = getTag(subj_id)	
	return render(request,'searcht/result.html',param)

def tagSearch(query,subj_id):
	questions = []
	tags = query.split(",")
	
	#read index
	file = open(path+"/index/tagIndex"+str(subj_id)+".json")
	for line in file:
		index = json.loads(line)
	
	#tag
	all = {}
	theTag = {}
	for tag in tags:
		questionList = index.get(tag,[])
		for question in questionList:
			all[question] = all.get(question,0)+1
			theTag[question] = theTag.get(question,[])+[str(tag)]
			
	allS = sorted(all.items(), key=lambda(k,v):(v,k), reverse = True)
	if len(allS) >50:
		allS = allS[:50]
	questions = []
	
	for question,value in allS:
		question = Question.objects.get(id = question)
		question.tags = []
		myTag = theTag.get(question.id,[])
		
		for tag in myTag:
			question.tags.append(TagDefinition.objects.get(title = tag))
		questions.append(question)
		
	return questions
	
	
	