from DBManagement.models import *
from django.conf import settings
import os
path = os.getcwd()+"/searchc/"
import json
from ExamPapers.fsearch.formula_indexer import features_extraction,ino_sem_terms,sort_sem_terms
import asciitomathml.asciitomathml
from ExamPapers.searchc.clustering import readFeature
import re
# print path 
def get_formula_feature_term():
	return [get_all_semantic(),get_all_structure(),get_all_constant(),get_all_variable()]
def get_all_structure():
	# get all structure feature and # print to file
	structure_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.structure_term!= '[]':
			f_structure_array = f.structure_term[1:-1].split(',')
			for f in f_structure_array:
				f = struct_rep(f)
				if f not in structure_all and f != "":
					structure_all.append(f)
	with open(path+'/data/structure.feature','w') as outfile:
		json.dump(structure_all,outfile)
	# print len(structure_all)
	return structure_all
def get_all_constant():
	# get all structure feature and # print to file
	constant_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.constant_term!= '[]':
			f_constant_array = f.constant_term[1:-1].split(',')
			for f in f_constant_array:
				f = const_rep(f)
				if f not in constant_all and f != "":
					constant_all.append(f)
	with open(path+'/data/constant.feature','w') as outfile:
		json.dump(constant_all,outfile)
	# print len(constant_all)
	return constant_all
def get_all_semantic():
	# get all structure feature and # print to file
	semantic_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.sorted_term!= '[]':
			f_semantic_array = f.sorted_term[1:-1].split(',')
			for line in f_semantic_array:
				fa = line.split('$')
				for f in fa:
					f = semantic_rep(f)
					if f not in semantic_all and f != "":
						semantic_all.append(f)
	with open(path+'/data/semantic.feature','w') as outfile:
		json.dump(semantic_all,outfile)
	# print len(semantic_all)
	return semantic_all
def get_all_variable():
	# get all structure feature and # print to file
	variable_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.variable_term!= '[]':
			f_variable_array = f.variable_term[1:-1].split(',')
			for f in f_variable_array:
				f = var_rep(f)
				if f not in variable_all and f != "":
					variable_all.append(f)
	with open(path+'/data/variable.feature','w') as outfile:
		json.dump(variable_all,outfile)
	# print len(variable_all)
	return variable_all
def semantic_rep(f):
	return f.replace("'",'').replace(" ",'').replace("\"","").replace("[","").replace("]","").replace("\\","").replace("=","").replace(":","").replace(".","").replace(";","").replace("(","").replace(")","")
def struct_rep(f):
	return f.replace("'",'').replace(" ",'').replace("\"","").replace("\\","")
def const_rep(f):
	return f.replace("'",'').replace(" ",'').replace("\"","").replace("\\","")
def var_rep(f):
	return f.replace("'",'').replace(" ",'').replace("\"","").replace("\\","")
def extractFormulaFeature(query):
	"Input: Formula Query"
	"Output: Query vector"
	
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
	featureAll = readFeature('formula')
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
def buildFormulaVector():
	#extract feature term
	semantic,structure,constant,variable = get_formula_feature_term()
	featureAll = semantic + structure +constant + variable
	with open(path+'/data/all.feature','w') as outfile:
		json.dump(featureAll,outfile)
	
	all_formula = Formula.objects.all()
	
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
def buildTagVector():
	#------------------ Build data vector ------------------------------
	term_matrix = []
	all_tag = TagDefinition.objects.all()
	for f  in Question.objects.all():
		line = []
		line.append(int(f.id))
		#tag
		f.tagid = []
		f.tagdef = Tag.objects.filter(question_id = f.id)
		for tag in f.tagdef:
			f.tagid.append((tag.tagdefinition.id))
		for t in all_tag:	
			line.append(min(1,f.tagid.count(t.id)))
		term_matrix.append(line)
	# Tag feature
	tag_feature = []
	for tag in all_tag:
		tag_feature.append(tag.title)
	with open(path+'/data/tag.feature','w') as outfile:
		json.dump(tag_feature,outfile)
	with open(path+'/data/data.vector','w') as outfile:
		json.dump(term_matrix,outfile)
	with open(path+'/data/data2.vector','w') as outfile:
		for line in term_matrix:
			for item in line:
				outfile.write(str(item))
				outfile.write("\t")
			outfile.write("\n")
	return
def buildTagVector(query):
	tagVector = []
	for tagdef in TagDefinition.objects.all():
		match = False
		for item in query:
			if tagdef.title == item:
				match = True
			if tagdef.type == "K":
				if re.match(str(tagdef.content), item) != None:
					match = True
		if match == True:
			tagVector.append(1)
		else:
			tagVector.append(0)
	return tagVector