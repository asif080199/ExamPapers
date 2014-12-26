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
from preclustering import *
from haystack.query import SearchQuerySet
path = os.getcwd()
import re
import operator
from math import *
from cluster import HierarchicalClustering,KMeansClustering
import datetime
from ExamPapers.fsearch.formula_indexer import features_extraction,ino_sem_terms,sort_sem_terms
from ExamPapers.searchc.preclustering import semantic_rep,const_rep,struct_rep,var_rep
import asciitomathml.asciitomathml
import numpy as np
def euclidean(x,y):
	sum = 0
	for i in x:
		for j in y:
			sum+= (i-j)**2
	return sum
def distance_function(x,y):
	"""
	Euclidean
	Does not take 1st element into account
	"""
	sum = 0 
	#for i in range(0,len(x)):	
	for i in range(1,len(x)):		# <-- Ignore 1st attribute - record key
		sum += (int(x[i])-int(y[i]))**2
	#print sqrt(sum)
	return sqrt(sum)
def cluster(request,subj_id):	#admin page
	
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = subj_id)
	#data = [[12,12],[34,34],[23,23],[32,32],[46,46],[96,96],[13,13],[1,1],[4,4],[9,9]]
	info = None
	#Do the rebuild cluster
	type = request.POST.get('type','')
	if type != "":
		info = []
		if type =='K' or type == 'H':
			data = readData('data')
			if type == "K":
				k = int(request.POST.get('k',2)) #2 by default 2 clusters
				buildKcluster(data,k)
				clusters = readCluster('K.25')
				info.append("<div class='alert alert-success' role='alert'>K Mean Cluster has been created successfully</div>")	
				info.append("Number of cluster: "+str(k))
			
			if type == "H":
				h = int(request.POST.get('h',0.5)) #10 by default threshold = 10
				buildHcluster(data,h)
				clusters = readCluster('H.5')
				
				info.append("<div class='alert alert-success' role='alert'>Hierachical Cluster has been created successfully</div>")	
				info.append("Threshold: "+str(h))
				info.append("<br/>Number of cluster: "+str(len(clusters)))
			
			
			#Start: info message
			info.append("<br/><br/><table class='table'><tr><th>No.</th><th>Cluster Name</th><th>No. Elements</th></tr>")
			i = 1
			for cluster in clusters:
				info.append("<tr>")
				info.append("<td>"+str(i)+"</td>")
				i+=1
				info.append("<td>"+str(cluster[-2])+"</td>")
				info.append("<td>"+str(len(cluster)-2)+"</td>")
				info.append("</tr>")
			info.append("</table>")
			#End: info message
		
		if type == "I":
			buildVector()
			info.append("<div class='alert alert-success' role='alert'>Data vectors has been built successfully</div>")		
	param['info'] = info
	return render(request,'searchc/cluster.html', param)	
def home(request,subj_id):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = subj_id)
	return render(request,'searchc/home.html', param)
def result(request,subj_id,type,cluster,query):
	param={}
	param.update(current(subj_id))
	
	if request.GET.get("query") != None:
		query = request.GET.get("query")
	queryVector =  extractFormulaFeature(query)
	clusters = readCluster('K.30')
	distance = []
	for cluster in clusters:
		distance.append(euclidean(queryVector,cluster[-1]))	#distance to cluster
	arr = np.array(distance)
	index =  arr.argsort()[:3]
	resultC = []
	for i in index:
		resultC.append(clusters[i])
	resultCluster = []
	
	for c in resultC:
		item = []
		leng = []
		name = []
		for formulaId in c[:-2]:
			formula = Formula.objects.get(indexid = formulaId) 
			formula.question = Question.objects.get(id = formula.question_id)
			item.append(formula) 
		leng.append(len(item))
		name.append(c[-2])
		resultCluster.append(cluster)
	param['name'] = name
	param['len'] = leng
	param['resultCluster'] = resultCluster
	return render(request,'searchc/result.html',param) 
def result2(request,subj_id,type,cluster,searchtext):
	total = 0
	param={}
	input = ""
	cluster = 0
	if request.GET.get("searchtext") != None:
		input = request.GET.get("searchtext")
	if request.GET.get("type") != None:
		type = request.GET.get("type")		
	if request.GET.get("cluster") != None:
		cluster = request.GET.get("cluster")	
		
	
	#update cur and subj	
	param.update(current(subj_id))
	
	#get all block 
	blocks = Block.objects.filter(subject = subj_id)

	#get all topics
	for b in blocks:
		b.topics = Topic.objects.filter(block = b.id)
	
	
	#get all match question
	questions = SearchQuerySet().autocomplete(content=input).filter(subject_id=subj_id)

	if type == "question":
		for question in questions:
			#question.stars = star(int(question.marks*5/16.0)+1)
			question.images = Image.objects.filter(qa_id = question.question_id)
			if question.images.count() > 0:
				question.image = question.images[0].imagepath
			question.content_short = question.content[0:100]
			
		# question count
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + 1
				total+=t.count
		
		
	elif type == "image":
		for question in questions:
			question.images = Image.objects.filter(qa_id = question.question_id)
			question.count = question.images.count()
		for b in blocks:
			for t in b.topics:
				t.count = 0
				for q in questions:
					if q.topic == t.title:
						t.count = t.count + q.count
			total+=t.count

	param['total'] = total
	param['type'] = type
	param['blocks'] = blocks
	param['questions'] = questions
	param['cluster'] = int(cluster)
	param['searchtext'] = input
	return render(request,'searchc/result.html',param)
def buildKcluster(data,k):
	"""
	Description:Build K-mean Cluster
	Input:
			data: e.g. data = [	[12,12],[34,34],
								[23,23],[32,32],
								[46,46],[96,96],
								[13,13],[1,1],
								[4,4],[9,9]] 
								# The first variable is key, not counted for clustering
						k: number of cluster
	Output: cluster record file  /searchc/save/K.cluster
	"""
	print "Clustering..."
	a = datetime.datetime.now()
	cl = KMeansClustering(data,distance_function)
	clusterK =  cl.getclusters(k)	     			# get k clusters
	b = datetime.datetime.now()
	print "Naming..."
	featureAll = readFeature('all')
	c = nameCluster(clusterK,featureAll)
	name = c[0]
	centroid = c[1]
	writeCluster('K',clusterK,name,centroid,k)
	print "Writting log..."
	with open(path+'/log/K_'+str(k)+'.log','w') as outfile:
		outfile.write("KMean Clustering Log\nDate:\t"+str(a.date())+"\nStart:\t"+str(a.time())+"\nEnd:\t"+str(b.time())+"\nDuration:\t"+str(b-a)+"\nK:\t"+str(k)+"\nNo. cluster:\t"+str(len(clusterK)))
		for cluster in clusterK:
			outfile.write(str(len(cluster)-2)+"\n")
	return
def buildHcluster(data, threshold):
	"""
	Description:Build Hierachical Cluster
	Input:
			data: e.g. data = [	[12,12],[34,34],
								[23,23],[32,32],
								[46,46],[96,96],
								[13,13],[1,1],
								[4,4],[9,9]] 
								# The first variable is key, not counted for clustering
			threshold: threshold distance to break cluster
	Output: cluster record file  /searchc/save/H.cluster
	"""
	print "Clustering..."
	a = datetime.datetime.now()
	cl = HierarchicalClustering(data,distance_function,'complete')
	clusterH =  cl.getlevel(threshold)	     			# get h clusters
	b = datetime.datetime.now()
	print "Naming..."
	featureAll = readFeature('all')
	c = nameCluster(clusterH,featureAll)
	name = c[0]
	centroid = c[1]
	writeCluster('H',clusterH,name,centroid,threshold)
	print "Writing..."
	with open(path+'/log/H_'+str(threshold)+'.log','w') as outfile:
		outfile.write("Hierahical Clustering Log\nDate:\t"+str(a.date())+"\nStart:\t"+str(a.time())+"\nEnd:\t"+str(b.time())+"\nDuration:\t"+str(b-a)+"\nH:\t"+str(threshold)+"\nMethod:\tComplete"+"\nNo. cluster:\t"+str(len(clusterH))+"\n\n")
		for cluster in clusterH:
			outfile.write(str(len(cluster)-2)+"\n")
	
	return
def readCluster(name):
	file = open(path+'/data/'+name+'.cluster')
	for line in file:
		return  (json.loads(line))
def writeCluster(type,clusters,name,centroid,t):
	# type: cluster type. eg. "H" or "K"
	# clusters: clusterH or clusterK
	# name: name array, no. item = no. cluster
	print "Write Cluster"
	with open(path+'/data/'+type+'.'+str(t)+'.cluster','w') as outfile:
		keyOnlyClusters = []
		i = 0 
		for cluster in clusters:
			keyOnlyCluster = [item[0] for item in cluster]
			keyOnlyCluster.append(name[i])
			keyOnlyCluster.append(centroid[i])
			i+=1
			keyOnlyClusters.append(keyOnlyCluster)
		json.dump(keyOnlyClusters, outfile)	
	return
def nameCluster(clusters,featureAll):
	centroid = []
	name = []
	allMax = []
	for cluster in clusters:	
		# centroid
		sumFeature = [0 for feature in featureAll]
		for i in range(len(sumFeature)):
			for item in cluster:
				if i!=0:
					sumFeature[i] += item[i]
		averageFeature =  [float(sum)/(len(cluster)) for sum in sumFeature]	
		centroid.append(averageFeature)
			
		# name
		m = max(sumFeature)
		index = [i for i, j in enumerate(sumFeature) if j > (m-1)] 	#top range max 1
		allMax.append(index)
	for index1 in allMax:
		sname = ""
		for i in index1:	
			sname += "(" + featureAll[i] + ") "
		name.append(sname)
		
	return [name,centroid]
def buildVector():
	#extract feature term
	semantic,structure,constant,variable = get_formula_feature_term()
	featureAll = semantic + structure +constant + variable
	with open(path+'/data/all.feature','w') as outfile:
		json.dump(featureAll,outfile)
	
	all_formula = Formula.objects.all()
	all_tag = TagDefinition.objects.all()
	
	for formula in all_formula:
		
		formula.semantic = []
		formula.structure = []
		formula.constant = []
		formula.variable = []
		
		#semantic
		if formula.sorted_term!= '[]':
			f_semantic_array = formula.sorted_term[1:-1].split(',')
			for line in f_semantic_array:
				fa = line.split('$')
				for f in fa:
					f = semantic_rep(f)
					if  f != "":
						formula.semantic.append(f)
		#structure
		if formula.structure_term!= '[]':
			f_structure_array = formula.structure_term[1:-1].split(',')
			for f in f_structure_array:
				f = struct_rep(f)
				if f != "":
					formula.structure.append(f)		
		#constant
		if formula.constant_term!= '[]':
			f_constant_array = formula.constant_term[1:-1].split(',')
			for f in f_constant_array:
				f = const_rep(f)
				if f != "":
					formula.constant.append(f)
		#variable
		if formula.variable_term!= '[]':
			f_variable_array = formula.variable_term[1:-1].split(',')
			for f in f_variable_array:
				f = var_rep(f)
				if f != "":
					formula.variable.append(f)
	

	#------------------ Build data vector ------------------------------
	term_matrix = []
	for f in all_formula:
		line = []
		line.append(int(f.indexid))
		print line
		for s in semantic:
			line.append(min(1,f.semantic.count(s)))
		for s in structure:
			line.append(min(1,f.structure.count(s)))
		for c in constant:
			line.append(min(1,f.constant.count(c)))
		for v in variable:
			line.append(min(1,f.variable.count(v)))
		#tag
		"""
		f.tagdef = Tag.objects.filter(question_id = f.id)
		f.tagid = []
		for tag in f.tagdef:
			f.tagid.append(int(tag.tagdefinition.id))
		for t in all_tag:	
			line.append(min(1,f.tagid.count(t.id)))
		"""
		term_matrix.append(line)
		
	with open(path+'/data/data.vector','w') as outfile:
		json.dump(term_matrix,outfile)
	with open(path+'/data/data2.vector','w') as outfile:
		for line in term_matrix:
			for item in line:
				outfile.write(str(item))
				outfile.write("\t")
			outfile.write("\n")
	return
def readData(name):
	file = open(path+'/data/'+name+'.vector')
	for line in file:
		return  (json.loads(line))
def readFeature(name):
	file = open(path+'/data/'+name+'.feature')
	for line in file:
		return  (json.loads(line))
def extractFormulaFeature(query):
	"""
	Step 1: Query to MathML
	"""
	math_obj =  asciitomathml.asciitomathml.AsciiMathML()
	math_obj.parse_string(query)
	mathML = math_obj.to_xml_string()
	mathML = mathML.replace("<math xmlns=\"http://www.w3.org/1998/Math/MathML\">","<math>") 
	mathML = mathML.replace("&","") 
	
	"""
	Step 2: MathML to Formula object
	"""
	#Extract four types of formula_obj
	formula_obj = Formula()
	(sem_features, struc_features, const_features, var_features) = features_extraction(mathML)            
            
	# Generate index terms
	inorder_sem_terms = ino_sem_terms(sem_features)
	sorted_sem_terms = sort_sem_terms(sem_features)
            
	#Insert into formulas table
	formula_obj.inorder_term = inorder_sem_terms
	formula_obj.sorted_term = sorted_sem_terms
	formula_obj.structure_term = struc_features
	formula_obj.constant_term = const_features
	formula_obj.variable_term = var_features
	formula_obj.status = 1

	"""
	Step 3: Extract feature
	"""
	featureAll = readFeature('all')
	formula = formula_obj
	formula.structure = []
	formula.semantic = []
	formula.constant = []
	formula.variable = []
	#semantic
	if formula.sorted_term!= '[]':
		f_semantic_array = formula.sorted_term[0]
		for line in f_semantic_array:
			fa = line.split('$')
			for f in fa:
				f = semantic_rep(f)
				if  f != "":
					formula.semantic.append(f)
	#structure
	if formula.structure_term!= '[]':
		f_structure_array = formula.structure_term
		#print f_structure_array
		for f in f_structure_array:
			f = struct_rep(f)
			if f != "":
				formula.structure.append(f)		
	#constant
	if formula.constant_term!= '[]':
		f_constant_array = formula.constant_term
		#print f_constant_array
		for f in f_constant_array:
			f = const_rep(f)
			if f != "":
				formula.constant.append(f)
	#variable
	if formula.variable_term!= '[]':
		f_variable_array = formula.variable_term
		for f in f_variable_array:
			f = var_rep(f)
			if f != "":
				formula.variable.append(f)
	"""
	Step 4: Build vector
	"""
	line = []
	
	#print formula.semantic
	#print formula.structure
	#print formula.constant
	#print formula.variable
	
	for s in readFeature('semantic'):
		line.append(min(1,formula.semantic.count(s)))
	for s in readFeature('structure'):
		line.append(min(1,formula.structure.count(s)))
	for c in readFeature('constant'):
		line.append(min(1,formula.constant.count(c)))
	for v in readFeature('variable'):
		line.append(min(1,formula.variable.count(v)))
	return  line
def test():
	return
