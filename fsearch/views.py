# -*- coding: utf-8 -*-
from operator import itemgetter, attrgetter

from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse

from DBManagement.models import *
from ExamPapers.logic.common import *

import asciitomathml.asciitomathml

from ExamPapers.fsearch.formula_searcher import search_content_formula
from ExamPapers.fsearch.formula_indexer import *

import re

@login_required	
def home(request,subj_id):
	param = {}
	param.update(current(subj_id))
	request.session.subj_id = subj_id
	return render(request,'fsearch/home.html', param)

def result(request, subj_id):
	param={}
	param.update(current(subj_id))
	
	query = None
	text_query = None
		
	if request.session.get('outputMathML', None) is not None:
		del request.session['outputMathML']
	if request.session.get('formula_query', None) is not None:
		del request.session['formula_query']

	try:
		query = request.POST.get('query','')
	
		original = query
		math_obj =  asciitomathml.asciitomathml.AsciiMathML()
		math_obj.parse_string(query)
		query = math_obj.to_xml_string()
		
		query = query.replace("<math xmlns=\"http://www.w3.org/1998/Math/MathML\">","<math>")
		
       	#topic_id = request.POST.get('topic','')
    	#query = unicode(query.decode('utf8'))
    	#query = request.POST['outputMathML']
		if request.POST['query'] == '':
			query = None
		request.session['outputMathML'] = query
		request.session['formula_query'] = request.POST['query']
            #text_query = request.POST.get('query', '')
		text_query = request.POST['query']
	except ValueError:
		query = None
    
	if query is not None:
		response, total_rs = search_content_formula(query)
	questions = []
	for r in response:
		question = Question.objects.get(id = r[0])
		question.formula = r[3]
		question.image = Image.objects.filter(qa_id = question.id)
		questions.append(question)
	#print questions 
	#Do paging for questions entries
	paginator = Paginator(questions, 10)
	
	try: page = int(request.GET.get("page", '1'))
	except ValueError: page = 1

	try:
		questions = paginator.page(page)
	except (InvalidPage, EmptyPage):
		questions = paginator.page(paginator.num_pages)
	#print questions 
	param['questions'] = questions
	param['total'] = total_rs
	param['query'] = original
	return render_to_response('fsearch/result.html', param, context_instance=RequestContext(request))

def index(formula_list):
	#reindex Formula
	for f in formula_list:
		the_string = f.formula
		#the_string = unicode(the_string.decode('utf8')) # adjust to your own encoding
		id = f.indexid
		math_obj =  asciitomathml.asciitomathml.AsciiMathML()
		math_obj.parse_string(the_string)
		mathML = math_obj.to_xml_string()
		mathML = mathML.replace("<math xmlns=\"http://www.w3.org/1998/Math/MathML\">","<math>") 
		try:
			create_index_model('',mathML,id)
		except:
			print "error create index model"
			print the_string
	
	#return render_to_response('fsearch/findex.html',param,RequestContext(request))

def reindex(request,subj_id):
	param = {}
	param.update(current(subj_id))
	trigger = request.POST.get('trigger','')
	if trigger == "activate":
		topics = Topic.objects.filter(block__subject_id = subj_id)
		for t in topics:
			t.questions = Question.objects.filter(topic = t)
			for question in t.questions:	
					indexFormula(question)
	return render_to_response('fsearch/reindex.html',param,RequestContext(request))
	
def indexFormula(questionId):
	# index question formula
	q_formula_list = getFormula(questionId)
	for f in q_formula_list:
		if len(f) > 4:
			cur_formula = Formula(question_id = questionId,formula = f,status=0)
			cur_formula.save()
	formula_list = Formula.objects.filter(question_id = questionId)
	try:
		index(formula_list)
	except:
		print questionId
	
def getFormula(questionId):
	content = Question.objects.get(id = questionId).content
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
	
