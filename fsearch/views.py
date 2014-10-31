# -*- coding: utf-8 -*-
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

def result(request,subj_id):
	param = {}
	
	# get query
	query = request.POST.get('query','')
	
	# convert query to mathml
	math_obj =  asciitomathml.asciitomathml.AsciiMathML()
	math_obj.parse_string(query)
	query = math_obj.to_xml_string()
	query = query.replace("<math xmlns=\"http://www.w3.org/1998/Math/MathML\">","<math>")
	
	#print query

	search_results_ct_all, total_rs = search_content_formula(query)
	print search_results_ct_all
	print total_rs
	
	param.update(current(subj_id))
	search_results_ct_all, total_rs = search_content_formula(query)
	return render(request,'fsearch/result.html', param,context_instance=RequestContext(request))

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
		create_index_model('',mathML,id)
	
	#return render_to_response('fsearch/findex.html',param,RequestContext(request))

def reindex(request,subj_id):
	param = {}
	param.update(current(subj_id))
	trigger = request.POST.get('trigger','')
	if trigger == "activate":
		questions = Question.objects.filter(topic__block__subject_id = subj_id)
		for question in questions:
			indexFormula(question)
	return render_to_response('fsearch/reindex.html',param,RequestContext(request))
	
def indexFormula(questionId):
	# index question formula
	q_formula_list = getFormula(questionId)
	for f in q_formula_list:
		cur_formula = Formula(question_id = questionId,formula = f,status=0)
		cur_formula.save()
	formula_list = Formula.objects.filter(question_id = questionId)
	index(formula_list)
	
def getFormula(questionId):
	content = Question.objects.get(id = questionId).content
	#get formula from  question content 
	
	formula = []
	
	# for case \[ formula \]
	fbegin = []
	fend = []
	for i in range(len(content)):
		if content[i] == "\\":
			if content[i+1] == "[":
				fbegin.append(i+2)
			if 	content[i+1] == "]":
				fend.append(i-2)
	for i in range(len(fbegin)):
		formula.append(content[fbegin[i]:fend[i]])
		
	# for case $$ formula $$
	fmark = []
	for i in range(len(content)):
		if content[i] == "$":
			if content[i+1] == "$":
				fmark.append(i)
	for i in range(0,len(fmark),2):
		fbegin = fmark[i]+2
		fend = fmark[i+1]-2
		formula.append(content[fbegin:fend])
	return formula
	
