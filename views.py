from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from DBManagement.models import *
from haystack.query import SearchQuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ExamPapers.views import *
from django.contrib.auth.decorators import login_required, user_passes_test
from ExamPapers.searchf.views import *
from haystack.utils import Highlighter
import os
import json
path = path = os.getcwd()

def current(subj_id):
	param = {}
	param['cur'] = Subject.objects.get(id = subj_id)
	param['level'] = Subject.objects.all()
	return param

	
@login_required		
def profile(request):
	param = {}
	param['cur'] = Subject.objects.get(id = 1)
	param['level'] = Subject.objects.all()
	
	#get subscription - TODO
	subjects = Subject.objects.all()
	
	param['subjects'] = subjects
	return render(request,'account/account.profile.html',param)

	
@login_required	
def level(request,subj_id):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = subj_id)
	return render(request,'level.html', param)
	
@login_required	
def home(request):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = ''
	return render(request,'index.html', param)

"""
-------------------------------------
Study
-------------------------------------
"""		
@login_required		
def study(request,subj_id,tp):
	param={}
	tp = -1
	if request.GET.get("tp") != None:
		tp = int(request.GET.get('tp'))	
	param={}
	blocks = Block.objects.filter(subject_id = subj_id)
	for b in blocks:
		b.topics = Topic.objects.filter(block = b)
	param['blocks'] = blocks
	param['tp'] = tp
	param['topic'] = "None"
	param['content'] = "False"
	content = []
	concept = []
	formula = []
	if tp!=-1:
		param['topic'] = Topic.objects.get(id = tp).title
		content = TagDefinition.objects.filter(topic_id = tp).order_by('type')
		for c in content:
			c.content = c.content.replace(";","<br/>")
			c.title = c.title.replace("_"," ")
			if c.type == "C":
				concept.append(c)
			elif c.type == "F":
				formula.append(c)
	param['concept'] = concept
	param['formula'] = formula
	param.update(current(subj_id))
	return render(request,'study.html', param)

	
def concept(request,subj_id,conceptId):
	param = {}
	param.update(current(subj_id))
	
	blocks = Block.objects.filter(subject_id = subj_id)
	for b in blocks:
		b.topics = Topic.objects.filter(block = b)
	param['blocks'] = blocks
	
	concept = TagDefinition.objects.get(id = conceptId)
	concept.title = concept.title.replace("_"," ")
	concept.content = concept.content.replace(";","<br/>")
	param['concept'] = concept
	tags = Tag.objects.filter(tagdefinition = concept)
	questions = []
	for t in tags:
		questions.append(Question.objects.get(id = t.question_id))
	param['questions'] = []
	if questions != []:
		for q in questions[:5]:
			q = getLiteQuestion(q)
		param['questions'] = questions[:5]	
	return render(request,'concept.html', param)

def tag(request,subj_id,tagId):
	param = {}
	param.update(current(subj_id))
	tag = TagDefinition.objects.get(id = tagId)
	tag.title = tag.title.replace("_"," ")
	tag.all = Tag.objects.filter(tagdefinition_id = tagId)
	tag.questions = []
	for ta in tag.all:
		tag.questions.append(Question.objects.get(id = ta.question_id))
	for q in tag.questions:
		q.stars = star(int(q.marks*5/16.0)+1)
		q.images = Image.objects.filter(qa_id = q.id)
		if q.images.count() > 0:
			q.image = q.images[0].imagepath
		q.content_short = q.content[0:250]
		q.tag = Tag.objects.filter(question_id = q.id)
		q.tagdef = []
		for ta in q.tag:
			tdeg = TagDefinition.objects.get(id = ta.tagdefinition.id)

			if tdeg not in q.tagdef:
				tdeg.title = tdeg.title.replace("_"," ")
				q.tagdef.append(tdeg)
	param['tag'] = tag
	temTag = TagDefinition.objects.filter(topic = tag.topic)
	for tag in temTag:
		tag = getTagLite(tag)
	param['rtag'] = temTag
	return render(request,'tag.html', param)
	
	
"""
-------------------------------------
Search
-------------------------------------
"""	
@login_required			
def search(request,subj_id,type,tp,searchtext):
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
	
	#update cur and subj	
	param.update(current(subj_id))
	
	
	#get all block 
	blocks = Block.objects.filter(subject_id = subj_id)
		
	#get all topics
	for b in blocks:
		b.topics = Topic.objects.filter(block = b.id)
	
	#get all match question
	questions = SearchQuerySet().autocomplete(content=input).filter(subject_id=subj_id)
	
	
	finalQuestions = []
	if type == "question":
		# question count
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + 1
						q.linkId = q.id[22:]
						if q.title == None:
							q.title = q.subtopic + " #"+str(q.question_no)
						q.stars = star(int(q.marks*5/16.0)+1)
						q.images = Image.objects.filter(qa_id = q.question_id)
						if q.images.count() > 0:
							q.image = q.images[0].imagepath
						highlight = Highlighter(input, html_tag='font', css_class='found', max_length=250)
						q.content_short = highlight.highlight(q.content)
						print q.content_short
						
						finalQuestions.append(q)
				total+=t.count
				
			
	elif type == "image":
		for question in questions:
			question.images = Image.objects.filter(qa_id = question.question_id)
			question.count = question.images.count()
			question.linkId = question.id[22:]
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + q.count
						finalQuestions.append(q)
			total+=t.count
	
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

	return render(request,'search.html',param)

@login_required		
def viewquestion(request,subj_id,qid):
	param = {}
	param.update(current(subj_id))
	question = getViewQuestion(qid)
	
	param['question'] = question
	questions = Question.objects.filter(topic = question.topic).exclude(id = question.id)
	param['questions'] = questions[:3]
	param['moreQuestions'] = questions[5:]
	tags = Tag.objects.filter(question_id = qid)
	tagdefs = []
	for t in tags:
		tagdef = TagDefinition.objects.get(tag = t.id)
		if tagdef.type == "F" or tagdef.type == "C":
			if tagdef not in tagdefs:
				tagdef.title = tagdef.title.replace("_"," ")
				tagdefs.append(tagdef)
	param['tags'] = tagdefs
	return render(request,'viewquestion.html',param)
	
def test(request,subj_id):
	param = {}
	#update cur and subj	
	param.update(current(subj_id))
	return render(request,'test.html',param)

	
"""
-------------------------------------
Statistics
-------------------------------------
"""

def statistics(request,subj_id,type):
	#init
	param = {}
	param.update(current(subj_id))
	
	#get background info
	if request.GET.get("type") != None:
		type = request.GET.get("type")
	param['type'] = type 
	
	
	#count
	all = 0
	if type == "overview":
		param['total'] = 0
	blocks = Block.objects.filter(subject__id = subj_id)
	if type == "practice":
		for b in blocks:
			b.topics = Topic.objects.filter(block__id = b.id)
			for t in b.topics:
				t.a = Question.objects.filter(topic_id = t.id).filter(difficulty = 0).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 1).count()+ Question.objects.filter(topic_id = t.id).filter(difficulty = 2).count()
				t.b = Question.objects.filter(topic_id = t.id).filter(difficulty = 3).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 4).count()
				t.c = Question.objects.filter(topic_id = t.id).filter(difficulty = 5).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 6).count()
				t.d = Question.objects.filter(topic_id = t.id).filter(difficulty = 7).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 8).count()
				t.e = Question.objects.filter(topic_id = t.id).filter(difficulty = 9).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 10).count()
				
		a = Question.objects.filter(difficulty = 0).filter(topic__block__subject_id = subj_id).count() + Question.objects.filter(topic_id = t.id).filter(topic__block__subject_id = subj_id).filter(difficulty = 1).count()+ Question.objects.filter(topic__block__subject_id = subj_id).filter(difficulty = 2).count()
		b = Question.objects.filter(difficulty = 3).filter(topic__block__subject_id = subj_id).count() + Question.objects.filter(difficulty = 4).filter(topic__block__subject_id = subj_id).count()
		c = Question.objects.filter(difficulty = 5).filter(topic__block__subject_id = subj_id).count() + Question.objects.filter(difficulty = 6).filter(topic__block__subject_id = subj_id).count()
		d = Question.objects.filter(difficulty = 7).filter(topic__block__subject_id = subj_id).count() + Question.objects.filter(difficulty = 8).filter(topic__block__subject_id = subj_id).count()
		e = Question.objects.filter(difficulty = 9).filter(topic__block__subject_id = subj_id).count() + Question.objects.filter(difficulty = 10).filter(topic__block__subject_id = subj_id).count() 
		param['total'] = [a,b,c,d,e]
		all = Question.objects.filter(topic__block__subject_id = subj_id).count()
	if type == "qna":
		today = datetime.today()
		for b in blocks:
			b.topics = Topic.objects.filter(block__id = b.id)
			for t in b.topics:
				t.day = Ask.objects.filter(topic_id = t.id).filter(created__day = today.day).count()
				t.month = Ask.objects.filter(topic_id = t.id).filter(created__month = today.month).count()
				t.year = Ask.objects.filter(topic_id = t.id).filter(created__year = today.year).count()
				t.all = Ask.objects.filter(topic_id = t.id).count()
		a = Ask.objects.filter(created__day = today.day).count()
		b = Ask.objects.filter(created__month = today.month).count()
		c = Ask.objects.filter(created__year = today.year).count()
		d = Ask.objects.count()
		all = a + b + c + d 
		param['total'] = [a,b,c,d]
	param['all'] = all
	param['blocks']= blocks
	return render(request,'statistics.html',param)
	
def star(rate):
	stars = []
	for s in range(rate):
		stars.append("<i class='glyphicon glyphicon-star text-yellow '></i>")
	return stars
	
def survey(request,subj_id):
	param = {}
	param.update(current(subj_id))
	return render(request,'survey.html',param)

#search tag
def getTagLite(tag):
	if len(tag.title) > 40:
		tag.title = tag.title[:37]+"..."
	tag.title = tag.title.replace("_"," ")
	return tag
	
def searchTag(request,subj_id):
	param={}
	param.update(current(subj_id))
	param['type'] = "question"
	param['tp'] = -1
	return render(request,'level.tag.html',param)

def resultTag(request,subj_id,query,tp,type):
	total = 0
	param={}
	input = ""
	tp = -1
	if request.GET.get("query") != None:
		input = request.GET.get("query").replace(","," ")
	if request.GET.get("type") != None:
		type = request.GET.get("type")		
	if request.GET.get("tp") != None:
		tp = request.GET.get("tp")	
	
	#update cur and subj	
	param.update(current(subj_id))
	
	
	#get all block 
	blocks = Block.objects.filter(subject_id = subj_id)
		
	#get all topics
	for b in blocks:
		b.topics = Topic.objects.filter(block = b.id)
	
	#get all match question
	questions = SearchQuerySet().autocomplete(content=input).filter(subject_id=subj_id)
	
	finalQuestions = []
	if type == "question":
		# question count
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + 1
						q.linkId = q.id[22:]
						q.stars = star(int(q.marks*5/16.0)+1)
						q.images = Image.objects.filter(qa_id = q.question_id)
						if q.images.count() > 0:
							q.image = q.images[0].imagepath
						q.content_short = q.content[0:250]
						
						q.tag = Tag.objects.filter(question_id = q.linkId)
						q.tagdef = []
						for ta in q.tag:
							tdeg = TagDefinition.objects.get(id = ta.tagdefinition.id)
							tdeg.title = tdeg.title.replace("_"," ")
							q.tagdef.append(tdeg)
					
						finalQuestions.append(q)
				total+=t.count
				
			
	elif type == "image":
		for question in questions:
			question.images = Image.objects.filter(qa_id = question.question_id)
			question.count = question.images.count()
			question.linkId = question.id[22:]
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + q.count
						finalQuestions.append(q)
			total+=t.count
	
	if tp!= str(-1):
		param['topic'] = Topic.objects.get(id = tp).title
	else:
		param['topic'] = "All"
		
	param['blocks'] = blocks
	param['total'] = total
	param['type'] = type
	param['questions'] = finalQuestions
	param['tp'] = int(tp)
	
	param['query'] = input
	param['queryo'] = request.GET.get("query")
	return render(request,'search.tag.html',param)
	
def getLiteQuestion(q):
	if q.title == None or q.title == "":
		q.title = q.subtopic.title + " #" + str(q.question_no)
	return q
	
def getViewQuestion(qid):
	question = Question.objects.get(id=qid)
	question.content = formatContent(question, "Question")
	question.topic = Topic.objects.get(id=question.topic_id)
	question.subtopic = Subtopic.objects.get(id=question.subtopic_id)
	question.stars = star((question.marks+1)/2)
	question.solution = formatContent(question,"Solution")
	question.answer = "Not available"
	question.images = Image.objects.filter(qa_id = question)
	question.tag = Tag.objects.filter(question_id = question.id)
	if question.title == None:
			question.title = question.subtopic.title + " #"+str(question.question_no)
	question.tagdef = []
	for ta in question.tag:
		tdeg = TagDefinition.objects.get(id = ta.tagdefinition.id)
		if tdeg not in question.tagdef:
			tdeg = getTagLite(tdeg)
			question.tagdef.append(tdeg)
	#print question.solution
	return question

def formatContent(question,type):
	images = list(Image.objects.filter(qa_id=question.id, qa=type).only('id','imagepath').order_by('id').values())
	if type == "Question":
		question.content = question.content.replace(';','<br/>').replace('img','').replace("<br/>(","<br/><br/>(")
		return question.content
	if type =="Solution":
		solutionContent = "Not available"
		if Solution.objects.filter(question_id = question.id).count() != 0:
			solutionContent  = Solution.objects.get(question_id = question.id).content
		solutionContent = solutionContent.replace(';','<br/>').replace('img','').replace("<br/>(","<br/><br/>(").replace('(ANS)','(ANS)<br/>')
		return solutionContent

def reindex(request,subj_id):
	param = {}
	param.update(current(subj_id))
	questions = Question.objects.all()
	param['mes'] = ""
	#formulaAll = []
	if request.POST:
		type = request.POST['type']
		if type == "formula":
			for q in questions:
				formulaSet = getFormula(q)
				for formula in formulaSet:
					line = {}
					formulaOb = Formula()
					if len(formula) >2:
						semantic,vector = extractFeature(formula)
						formulaOb.question = q
						formulaOb.formula = formula
						tem = "','".join(map(str, semantic))
						formulaOb.semantic  = "['"+tem+"']"
						##print formulaOb.semantic
						formulaOb.vector = vector
						if formulaOb.semantic  != "['']":
							formulaOb.save()
			buildIndex()
			param['mes'] = "Tag index for "+param['cur'].title+" has been created successfully at "+path+"/log/index.json"
		if type == "tag":
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
			param['mes'] = "Tag index for "+param['cur'].title+" has been created successfully at "+path+"/index/tagIndex"
	return render(request,'reindex.html',param)