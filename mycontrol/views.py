# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
from DBManagement.models import *
from ExamPapers.views import current, getViewQuestion
import datetime

''' Question Management'''
def qHome(request,subj_id):
	param = {}
	param.update(current(subj_id))
	
	#get paper
	papers = Paper.objects.filter(subject_id = subj_id)
	param['papers'] = papers
	
	#get topic
	topics = Topic.objects.filter(block__subject_id = subj_id)
	param['topics'] = topics
	
	#get concept
	concepts = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type = "C")
	param['concepts'] = concepts
	formulas = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type = "F")
	param['formulas'] = formulas
	# for nicer display
	for c in concepts:
		c.title = c.title.replace("_"," ")
	for c in formulas:
		c.title = c.title.replace("_"," ")
	param['mes'] = ""
	return render_to_response('mycontrol/qHome.html',param,context_instance=RequestContext(request))

def qList(request,subj_id):
	"""View result from browse by"""
	param = {}
	param.update(current(subj_id))
	if request.GET.get("paper"):
		# for practice question
		if request.GET.get("paper") == '-1':
			questions = Question.objects.filter(type = "Practice").filter(topic__block__subject_id = subj_id)
			for question in questions:
				question = previewQuestion(question)
			param['questions'] = questions
			param['title'] = "Practice Question"

		else:
			#for paper
			param.update(paperList(request.GET.get("paper")))
			
	if request.GET.get("topic"):
		param.update(topicList(request.GET.get("topic")))
	if request.GET.get("concept"):
		param.update(concepList(request.GET.get("concept"),"Concept"))
	if request.GET.get("formula"):
		param.update(concepList(request.GET.get("formula"),"Formula"))
	return render_to_response('mycontrol/qList.html',param,context_instance=RequestContext(request))

def paperList(id):
	param = {}
	paper = Paper.objects.get(id = id)
	papers = Paper.objects.filter(subject_id = paper.subject_id)
	questions = Question.objects.filter(paper_id = id)
	for q in questions:
		q = previewQuestion(q)
	param['paper'] = paper
	param['papers'] = papers
	param['questions'] = questions
	param['cat'] = "Paper"
	return param

def topicList(id):
	param = {}
	topic = Topic.objects.get(id = id)
	blocks = Block.objects.filter(subject_id = topic.block.subject_id)
	for block in blocks:
		block.topics = Topic.objects.filter(block_id = block.id)
	questions = Question.objects.filter(topic_id = id)
	for q in questions:
		q = previewQuestion(q)
	param['topic'] = topic
	param['blocks'] = blocks
	param['questions'] = questions
	param['cat'] = "Topic"
	return param

def concepList(id,type):
	param = {}
	concept = TagDefinition.objects.get(id = id)
	concept.title = concept.title.replace("_"," ")
	concepts = TagDefinition.objects.filter(topic__block = concept.topic.block.id)
	questionId = Tag.objects.filter(tagdefinition = id)
	print questionId
	questions = []
	for i in questionId:
		questions.append(Question.objects.get(id=i.question_id))
	for q in questions:
		q = previewQuestion(q)
	param['concept'] = concept
	param['concepts'] = toNiceTagList(concepts)
	param['questions'] = questions
	param['cat'] = type
	return param

def toNiceTagList(lists):
	for item in lists:
		item.title = item.title.replace("_"," ")
		item.count = Tag.objects.filter(tagdefinition_id  = item.id).count()
		if len(item.title) > 30:
			item.title = item.title[0:30]+"..."
			
	return lists
def previewQuestion(q):
	# Process question for preview
	q.title = q.subtopic.title+" #"+str(q.question_no)	#tochange
	q.display = q.content[:100]
	q.noTag = Tag.objects.filter(question_id = q.id).count()
	return q

def qForm(request,subj_id):
	param = {}

	param['tagdefs'] = TagDefinition.objects.filter(type = "K")|TagDefinition.objects.filter(topic__block__subject_id = subj_id)
	param['topics'] = Topic.objects.filter(block__subject_id = subj_id)
	"""Update old"""
	if request.POST:
		question = Question.objects.get(id = request.POST['id'])
		if question.type == "Exam":
			paper = Paper.objects.get(id = question.paper_id)
			param['year'] = paper.year
			param['month'] = paper.month
			param['number'] = paper.number
		if question.type == "Practice":
			param['source'] = question.source
		param['content'] = question.content
		param['difficulty'] = question.difficulty
		param['marks'] = question.marks
		param['topic'] = question.topic
		param['subtopic'] = question.subtopic
		param['id'] = question.id
		param['solution'] = Solution.objects.get(question_id = question.id).content
		#Image
		images = Image.objects.filter(qa_id = question.id)
		param['images'] = images
		param['type'] = question.type
		param['new'] = 0
	else:
		"""Create new"""
		param['new'] = 1
		if request.GET['topic']:
			# pre define data for topic
			param['topic'] = int(request.GET['topic'])
		
		param['year'] = -1
		if request.GET['paper']:
			# pre define data for paper
			paper = Paper.objects.get(id = request.GET['paper'])
			param['year'] = paper.year
			param['month'] = paper.month
			param['number'] = paper.number
		
	
	param['subtopics'] = Subtopic.objects.filter(topic__block__subject_id = subj_id)
	param.update(current(subj_id))
	"""Tags"""
	if question:
		tags = Tag.objects.filter(question_id = question.id)
		c = ""
		f = ""
		k = ""
		for t in tags:
			tdef = TagDefinition.objects.get(id = t.tagdefinition_id)
			if tdef.type == "C":
				c+=str(tdef.title)+","
			elif tdef.type == "F":
				f+=str(tdef.title)+","
			else:
				k+=str(tdef.title)+","
		param['tagC'] =  c
		param['tagF'] = f
		param['tagK'] = k
	
	new = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type="C")
	allC = []
	for i in new:
		allC.append(str(i.title))
	param['allTagC'] = allC
	
	new = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type="F")
	allF = []
	for i in new:
		allF.append(str(i.title))
	param['allTagF'] = allF
	
	new = TagDefinition.objects.filter(type="K")
	allF = []
	for i in new:
		allF.append(str(i.title))
	param['allTagK'] = allF
	return render_to_response('mycontrol/qForm.html',param,context_instance=RequestContext(request))

def qUpdate(request,subj_id):
	"""Update and create use same function"""
	param = {}
	param.update(current(subj_id))
	param['mes'] = ""
	
	
	
	#get value
	conceptTag = request.POST['conceptTag']
	formulaTag = request.POST['formulaTag']
	keywordTag = request.POST['keywordTag']
	cTag = conceptTag.split(",")
	fTag =  formulaTag.split(",")
	kTag =  keywordTag.split(",")

	delCon = request.POST['delCon']
	delSol = request.POST['delSol']
	id = request.POST['id']
	topic = request.POST['topic']
	subtopic = request.POST['subtopic']
	content = request.POST['content']
	solution = request.POST['solution']
	difficulty = request.POST['difficulty']
	mark = request.POST['mark']
	type = request.POST['type']
	title = request.POST['title']
	if type == "Exam":
		year = request.POST['year']
		month = request.POST['month']
		number = request.POST['number']
	if type == "Practice":
		source = request.POST['source']
	if request.FILES.get("questionFile")!=None:
		qImage = request.FILES.get("questionFile")
	if request.FILES.get("solutionFile")!=None:
		sImage = request.FILES.get("solutionFile")
	
	#create object
	'''Paper'''
	if type == "Exam":
		#old paper
		papers = Paper.objects.filter(year = year).filter(month=month).filter(number=number).filter(subject_id = subj_id)
		print "Old Paper"
		#newpaper
		if len(papers) == 0:
			#create new paper
			
			"Weight name convention"
			paperId = str(year)
			print month
			if month == "June" and number == '1':
				paperId+="0100"
			if month == "November" and number == '1':
				paperId+="0200"
			if month == "June" and number == '2':
				paperId+="0300"
			if month == "November" and number == '2':
				paperId+="0400"
			paperId+=str(subj_id)
			""
			paper = Paper(id = paperId, year = year, month = month, number = number, subject_id = subj_id)
			paper.save()
			param['mes']+="New paper "+str(paper.id)+" has been created successfully<br/>"
		else:
			paper = papers[0]
			
	'''Question'''	
	if id!= "":
		print "Old Question"
		#old question
		question = Question.objects.get(id = id)
		solution = Solution.objects.get(question_id = id)
		solution.content = solution
		solution.save()
		param['mes']+="Question "+str(question.id)+" has been updated successfully<br/>"
	else:
		#new question
		question = Question()
		param['mes']+="New question has been created successfully<br/>"
		if type == "Practice": 
			#id 
			lastId = Question.objects.all().order_by('-id')[0].id
			if int(lastId) < 30000000000:
				question.id = 30000000000
			else:
				question.id = int(lastId)+1
				
			question.source = source
			
		if type == "Exam":
			questionSamePaper = Question.objects.filter(paper_id = paper.id).order_by('-id')
			
			if len(questionSamePaper) == 0:
				no = 1
			if len(questionSamePaper) > 0:
				lastQuestion = questionSamePaper[0]
				no = int(lastQuestion.id[-3:])+1
		
			while len(str(no))<3:
				no = "0"+str(no)
			question.id = paper.id+no
			#exam question
			question.paper = paper
			question.question_no = no
		
		
		
	question.type = type
	question.content = content
	question.topic = Topic.objects.get(id = topic)
	question.subtopic = Subtopic.objects.get(id = subtopic)
	question.marks = mark
	question.title = title
	question.difficulty = difficulty
	question.save()
	
	if id == "":
		solution = Solution(question = question,content = solution)
		solution.save()
	
	'''Image'''	
	#Remove
	if delCon == "on":
		images = Image.objects.filter(qa_id_id = question.id).filter(qa = "Question")
		for i in images:
			i.delete()
	if delSol == "on":	
		images = Image.objects.filter(qa_id_id = question.id).filter(qa = "Solution")
		for i in images:
			i.delete()
		
	#add 
	if request.FILES:
		folder = ""
		f1 = request.FILES['questionFile']
		f2 = request.FILES['solutionFile']
		
		if question.topic.block.subject.id == 0:
			path = "/static/image/amath/extra/"
		elif question.topic.block.subject.id == 1:
			path = "/static/image/emath/extra/"
		elif question.topic.block.subject.id == 2:
			path = "/static/image/h2math/extra/"
		elif question.topic.block.subject.id == 3:
			path = "/static/image/psle/extra/"
		
		#f1
		tail = f1.name.split(".")[-1]
		des = 'resource'+path+question.id+"q."+tail
		savePath = path[1:]+question.id+"q."+tail
		destination = open(des, 'wb+')
		for chunk in f1.chunks():
			destination.write(chunk)
		destination.close()
		
		new = Image()
		new.qa="Question"
		new.qa_id = question
		new.imagepath = savePath
		new.save()
		
		#f2
		tail = f2.name.split(".")[-1]
		des = 'resource'+path+question.id+"q."+tail
		savePath = path[1:]+question.id+"q."+tail
		destination = open(des, 'wb+')
		for chunk in f2.chunks():
			destination.write(chunk)
		destination.close()
		
		new = Image()
		new.qa="Solution"
		new.qa_id = question
		new.imagepath = savePath
		new.save()
	if question.title == "":
		question.title = question.subtopic.title 
	if question.question_no != None:
		question.title += " #" + str(question.question_no)
	param['question'] = getViewQuestion(question.id)		
	
	
	"""Tag"""
	oldTags = Tag.objects.filter(question_id = question.id)
	for tag in oldTags:
		tag.delete()
	for tag in cTag:
		if tag!="":
			theTag = TagDefinition.objects.filter(title = tag)[0]
			newTag = Tag()
			newTag.tagdefinition = theTag
			newTag.question = question
			newTag.save()
	for tag in fTag:
		if tag!="":
			theTag = TagDefinition.objects.filter(title = tag)[0]
			newTag = Tag()
			newTag.tagdefinition = theTag
			newTag.question = question
			newTag.save()
	for tag in kTag:
		if tag!="":
			theTag = TagDefinition.objects.filter(title = tag)[0]
			newTag = Tag()
			newTag.tagdefinition = theTag
			newTag.question = question
			newTag.save()
	return render_to_response('mycontrol/qView.html',param,context_instance=RequestContext(request))

def qDelete(request,subj_id):
	param = {}
	param.update(current(subj_id))
	
	id = request.POST['id']
	question = Question.objects.get(id = id)
	solution = Solution.objects.get(question_id = id)
	images = Image.objects.filter(qa_id_id = id)
	tag = Tag.objects.filter(question_id = id)
	for t in tag:
		t.delete()
	for i in images:
		i.delete()
	solution.delete()
	question.delete()
	
	
	#get paper
	papers = Paper.objects.filter(subject_id = subj_id)
	param['papers'] = papers
	
	#get topic
	topics = Topic.objects.filter(block__subject_id = subj_id)
	param['topics'] = topics
	
	#get concept
	concepts = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type = "C")
	param['concepts'] = concepts
	formulas = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type = "F")
	param['formulas'] = formulas
	# for nicer display
	for c in concepts:
		c.title = c.title.replace("_"," ")
	for c in formulas:
		c.title = c.title.replace("_"," ")
	param['mes'] = "Question " +id+" has been deleted successfully"
	return render_to_response('mycontrol/qHome.html',param,context_instance=RequestContext(request))


""""Tag"""
def tHome(request,subj_id):
	param = {}
	param.update(current(subj_id))
	tType = request.GET.get("tType")
	param['tType'] = tType
	if tType == None or tType== "concept":
		param['tags'] = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type="C")
	if tType== "formula":
		param['tags'] = TagDefinition.objects.filter(topic__block__subject_id = subj_id).filter(type="F")
	if tType== "keyword":
		param['tags'] = TagDefinition.objects.filter(type="K")
	param['mes'] = ""
	return render_to_response('mycontrol/tHome.html',param,context_instance=RequestContext(request))
	
def tUpdate(request,subj_id):
	param = {}
	param.update(current(subj_id))
	param['mes'] = ""
	if request.POST:
		id  = request.POST['id']
		title = request.POST['title']
		content = request.POST['content']
		type = request.POST['type']
		topic = request.POST['topic']

	if id !="":
		tag = TagDefinition.objects.get(id = id)
		param["mes"] = "Tag is updated successfully"
		tag.title = title
		tag.content = content
		tag.type = type
		tag.topic = Topic.objects.get(id = topic)
		if tag.type == "K":
			tag.topic = None
	else :
		tag = TagDefinition(title = title, content = content, type = type)
		tag.save()
		param["mes"] = "Tag is created successfully"
	param['title'] = tag.title
	param['content'] = tag.content
	param['type'] = tag.type
	param['id'] = tag.id
	param['topics'] = Topic.objects.filter(block__subject_id = subj_id)
	
	return render_to_response('mycontrol/tForm.html',param,context_instance=RequestContext(request))

def tForm(request,subj_id):
	param = {}
	param.update(current(subj_id))
	param['mes'] = ""
	id = request.GET.get("id")
	param['topics'] = Topic.objects.filter(block__subject_id = subj_id)
	if id!= None:
		tag = TagDefinition.objects.get(id = id)
		param['title'] = tag.title
		param['content'] = tag.content
		param['type'] = tag.type
		param['id'] = tag.id
	return render_to_response('mycontrol/tForm.html',param,context_instance=RequestContext(request))
	
def sHome(request,subj_id):
	param = {}
	param.update(current(subj_id))
	param['mes'] = ""
	return render_to_response('mycontrol/sHome.html',param,context_instance=RequestContext(request))