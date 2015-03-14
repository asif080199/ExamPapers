# -*- coding: utf-8 -*-
from operator import itemgetter, attrgetter
from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required 	#for login required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponse
from django.core.urlresolvers import reverse
import os 
import json
from DBManagement.models import *
from ExamPapers.logic.common import *
from haystack.query import SearchQuerySet
path = os.getcwd()
import re
import operator
from math import *
from cluster import HierarchicalClustering,KMeansClustering
import datetime
from ExamPapers.fsearch.formula_indexer import features_extraction,ino_sem_terms,sort_sem_terms
from ExamPapers.searchc.dataprocessing import *
from ExamPapers.searchc.clustering import *
import asciitomathml.asciitomathml
import numpy as np
import re
from datetime import datetime

def cluster(request,subj_id):	#cluster admin
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = subj_id)
	
	info = None
	
	type = request.POST.get('type','')
	dataName = request.POST.get('data','')

	if type != "":
		info = []
		if type =='K' or type == 'H':
			noCluster = int(request.POST.get('noCluster',2)) # 2 by default 2 clusters
			buildCluster(type,dataName,noCluster)				 # build cluster
			
			filename = type+"."+str(noCluster)+"."+dataName	
			clusters = readCluster(filename)
			info.append("<div class='alert alert-success' role='alert'>"+ type +" Cluster has been created successfully</div>")	
			info.append("Number of cluster: "+str(noCluster))
			info.append("<br/><br/><table class='table'><tr><th>No.</th><th>Cluster Name</th><th>No. Elements</th></tr>")
			i = 1
			for cluster in clusters:
				info.append("<tr>")
				info.append("<td>"+str(i)+"</td>")
				i+=1
				info.append("<td>"+str(cluster[1])+"</td>")
				info.append("<td>"+str(len(cluster[0]))+"</td>")
				info.append("</tr>")
			info.append("</table>")
			#End: info message
		
		if type == "I":
			if dataName == "formula":
				buildFormulaVector()
			elif dataName == "tag":
				buildTagVector()
			info.append("<div class='alert alert-success' role='alert'>Data vectors has been built successfully</div>")		
	param['info'] = info
	return render(request,'searchc/cluster.html', param)	

""""""

def homeFormula(request,subj_id):
	param = {}
	param.update(current(subj_id))
	clusters = readCluster('A.68.formula')

	final = []
	for cluster in clusters:
		content = []
		ids = cluster[0]
		print ids
		for id in ids:
			print Formula.objects.get(indexid= id).indexid
			print Formula.objects.get(indexid= id).formula
		final.append(content)
		
	param['clusters'] = final
	return render(request,'searchc/home.formula.html',param) 	
def homeTag(request,subj_id):
	param = {}
	param.update(current(subj_id))
	return render(request,'searchc/home.tag.html',param) 
def homeText(request,subj_id):
	param = {}
	param.update(current(subj_id))
	return render(request,'searchc/home.text.html',param) 

""""""

def resultFormula(request,subj_id):
	param = {}
	param.update(current(subj_id))
	
	"""
	Process query
	"""
	query = request.POST.get("query","")
	queryVector =  extractFormulaFeature(query)
	clusters = readCluster('A.68.formula')		# cluster name
	distance = []
	
	"""
	Rank cluster
	"""
	for cluster in clusters:
		distance.append(euclidean(queryVector,cluster[2]))	#distance to cluster		
	arr = np.array(distance)
	index =  arr.argsort()[:1]
	
	"""
	Format result
	"""
	temClusters = []
	for i in index:
		temClusters.append(clusters[i])
	
	i=0
	resultCluster = []
	for cluster in temClusters:
		newCluster = []
		formulaObjects = []
		for id in cluster[0]:
			formula = Formula.objects.get(indexid = id)
			formula.question = Question.objects.get(id = formula.question_id)
			formula.question.content_short = formula.question.content[:150]
			formula.question.stars = star(int(formula.question.marks*5/16.0)+1)
			formulaObjects.append(formula)
		newCluster.append(i)				#index
		newCluster.append(cluster[1][:50])		#name
		newCluster.append(formulaObjects)	#array
		resultCluster.append(newCluster)
		i+=1
		
	#resultCluster
	#0 : index
	#1 : cluster name
	#2 : array of formula and question
	
	param['resultCluster'] = resultCluster
	param['query'] = query
	return render(request,'searchc/result.formula.html',param) 
	
def resultTag(request,subj_id):
	param = {}
	param.update(current(subj_id))
	
	query = request.POST.get("query","")
	tags = query.split(",")
	queryVector = buildTagVector(tags)
	
	distance = []
	clusters = readCluster('H.50.tag')		# cluster name
	for cluster in clusters:
		distance.append(euclidean(queryVector,cluster[2]))	#distance to cluster		
	arr = np.array(distance)
	index =  arr.argsort()[:7]
	
	"""
	Format result
	"""
	temClusters = []
	for i in index:
		temClusters.append(clusters[i])
	
	i=0
	resultCluster = []
	for cluster in temClusters:
		newCluster = []
		questionObjects = []
		for id in cluster[0]:
			question = Question.objects.get(id = id)
			question.content_short = question.content[:150]
			question.tags = Tag.objects.filter(question_id = question.id)
			images = Image.objects.filter(qa_id = question.id)
			if len(images)!=0:
				question.image = images[0].imagepath
			questionObjects.append(question)
		newCluster.append(i)				#index
		newCluster.append(cluster[1][:50])		#name
		newCluster.append(questionObjects)	#array
		resultCluster.append(newCluster)
		i+=1
		
	#resultCluster
	#0 : index
	#1 : cluster name
	#2 : array of formula and question
	
	param['resultCluster'] = resultCluster
	param['query'] = query
	
	return render(request,'searchc/result.tag.html',param) 
	
def resultText(request,subj_id):
	param={}
	
	#get input 
	type = "question"
	cluster = 0 
	if request.GET.get("query") != None:
		query = request.GET.get("query","")
	if request.GET.get("type") != None:
		type = request.GET.get("type","question")		
	if request.GET.get("cluster") != None:
		clusterId = int(request.GET.get("cluster",0))
	
	#update cur and subj	
	param.update(current(subj_id))

	""" The search """
	#get all match question
	questions = SearchQuerySet().autocomplete(content=query).filter(subject_id=subj_id)
	
	#cluster online
	
	if len(questions) > 1:
		finalCluster = buildOnlineCluster("H","tag",questions)
	elif len(questions) == 1:
		finalCluster = [[0,query,questions,1]]	# a dummy cluster
	else:
		finalCluster = [[]]
	selectedCluster = finalCluster[clusterId]
	
	if len(questions) >= 1:
		#prepare question display
		for question in selectedCluster[2]:
			question.stars = star(int(question.marks*5/16.0)+1)
			question.images = Image.objects.filter(qa_id = question.id)
			if question.images.count() > 0:
				question.image = question.images[0].imagepath
			question.content_short = question.content[0:270]
		param['cluster'] = selectedCluster 
		param['clusters'] = finalCluster 
	param['type'] = type
	param['query'] = query
	param['clusterId'] = clusterId
	
	return render(request,'searchc/result.text.html',param) 

def euclidean(x,y):
	sum = 0
	for i in range(len(x)):			
		sum+= (x[i]-y[i])**2
	return sqrt(sum)
	

def star(rate):
	stars = []
	for s in range(rate):
		stars.append("<i class='glyphicon glyphicon-star text-yellow'></i>")
	#for s in range(5-rate):
	#	stars.append("<i class='glyphicon glyphicon-star-empty'></i>")
	return stars
