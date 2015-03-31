# -*- coding: utf-8 -*-
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
from DBManagement.models import *
from ExamPapers.views import current, getViewQuestion
import os
path = path = os.getcwd()
import json
import datetime

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
	return render_to_response('searchf/home.html',param,context_instance=RequestContext(request))

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
	
def result(request,subj_id):
	param = {}
	param.update(current(subj_id))
	query = request.POST['query']
	semantic, vector = extractFeature(query)
	print semantic
	
	#read index
	file = open(path+"/log/index.json")
	for line in file:
		index = json.loads(line)
		
		
	result = []
	for feature in semantic:
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
	print final
	questions = []	
	for item in list(final):
		formula = (Formula.objects.get(index = item))
		question = Question.objects.get(id = formula.question_id)
		question.formula = formula.formula
		questions.append(question)
	param['questions'] = questions
	param['query'] = query
		
	#match
		
	return render_to_response('searchf/result.html',param,context_instance=RequestContext(request))