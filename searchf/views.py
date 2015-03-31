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
from ExamPapers.views import *
from django.contrib.auth.decorators import login_required, user_passes_test
def current(subj_id):
	param = {}
	param['cur'] = Subject.objects.get(id = subj_id)
	param['level'] = Subject.objects.all()
	return param
def star(rate):
	stars = []
	for s in range(rate):
		stars.append("<i class='glyphicon glyphicon-star text-yellow '></i>")
	return stars
def reindex(request,subj_id):
	param = {}
	param.update(current(subj_id))
	questions = Question.objects.all()
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
						#print formulaOb.semantic
						formulaOb.vector = vector
						if formulaOb.semantic  != "['']":
							formulaOb.save()
			buildIndex()

	return render_to_response('searchf/reindex.html',param,context_instance=RequestContext(request))


def buildIndex():
	feature1 = ["int","sum","lim","pro"] 
	feature2 = ["cup","cap"]
	feature3 = ["leq","geq","neq",">","<"]
	feature4 = ["ln","log","lg"]
	feature5 = ["sin","cos","tan","sec","cot"]
	feature6 = ["+","-","sqrt","|","^","vec","frac"]
	feature7 = ["binom","choose","brack","brace","bangle"]
	featureStandard = feature1+feature2+feature3+feature4+feature5+feature6+feature7
	
	index = {}
	formulas = Formula.objects.all()
	for feature in featureStandard:
		list = []
		for formula in formulas:
			if feature in eval(formula.semantic):
				list.append(formula.index)
		index[feature] = list	
	with open(path+"/log/index.json", 'w') as outfile:
		json.dump(index, outfile)
	return
	
def extractFeature(formula):
	semantic = []
	vector = []
	feature1 = ["int","sum","lim","pro"] 
	feature2 = ["cup","cap"]
	feature3 = ["leq","geq","neq",">","<"]
	feature4 = ["ln","log","lg"]
	feature5 = ["sin","cos","tan","sec","cot"]
	feature6 = ["+","-","sqrt","|","^","vec","frac"]
	feature7 = ["binom","choose","brack","brace","bangle"]
	
	featureStandard = feature1+feature2+feature3+feature4+feature5+feature6+feature7

	for feature in featureStandard:
	
		tem = formula
		if feature == "^":
			tem = formula.replace("^{\circ}"," ").replace("^{-1}"," ")
		if feature == "frac":
			tem = formula.replace("/","frac")
		if feature == "-":
			tem = formula.replace("|->"," ").replace("<-|"," ").replace("^{-1}"," ")
		if feature == "|":
			tem = formula.replace("|->"," ").replace("<-|"," ").replace("| \left"," ").replace("\right |"," ")
		
		if feature in tem:
			semantic.append(feature)
		vector.append(tem.count(feature))

	return list(set(semantic)),vector
	

def home(request,subj_id):
	param = {}
	param.update(current(subj_id))
	param['type'] = 'question'
	param['tp'] = -1
	return render(request,'searchf/home.html',param)

def getFormula(question):
	content = question.content
	#get formula from  question content 
	
	formula = []
	
	# for case \[ formula \]
	fbegin = []
	fend = []
	for i in range(len(content)-1):
		if content[i] == "\\":
			if content[i+1] == "[":
				fbegin.append(i+2)
			if 	content[i+1] == "]":
				fend.append(i)
	for i in range(len(fbegin)):
		#print content[fbegin[i]:fend[i]]
		formula.append(content[fbegin[i]:fend[i]])
		
	# for case $$ formula $$
	fmark = []
	for i in range(len(content)-1):
		if content[i] == "$":
				if content[i+1] == "$":
					fmark.append(i)
	for i in range(0,len(fmark),2):
		fbegin = fmark[i]+2
		fend = fmark[i+1]
		formula.append(content[fbegin:fend])
	return formula
	
@login_required			
def result(request,subj_id,type,tp,query):
	

	total = 0
	param={}
	input = ""
	tp = -1
	if request.GET.get("query") != None:
		input = request.GET.get("query")
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
	questions = formulaSearch(input,subj_id)
	
	
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
		
	if tp!= str(-1) and tp!=-1:
		param['topic'] = Topic.objects.get(id = tp).title
	else:
		param['topic'] = "All"

	param['blocks'] = blocks
	param['total'] = total
	param['type'] = type
	param['questions'] = finalQuestions
	param['tp'] = int(tp)
	
	param['query'] = input
	for q in questions:
		formula = Formula.objects.filter(question = q.id)

	return render(request,'searchf/result.html',param)

def formulaSearch(query,subj_id):
	#read index
	file = open(path+"/log/index.json")
	for line in file:
		index = json.loads(line)
	semantic, vector = extractFeature(query)	

	result = []
	for feature in semantic:
		print feature
		result.append((index.get(feature)))
	
	final = (result[0])
	for line in result[1:]:
		tem = []
		for item in line:
			if item in final:
				tem.append(item)
		if tem == []:
			break
		final = tem
	questions = []	
	for item in list(final):
		formula = (Formula.objects.get(index = item))
		question = Question.objects.get(id = formula.question_id)
		question.formula = formula.formula
		questions.append(question)
	return questions
	
	
	