from DBManagement.models import *
from django.conf import settings
import os
path = os.getcwd()
print path 
def get_all_structure():
	# get all structure feature and print to file
	structure_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.structure_term!= '[]':
			f_structure_array = f.structure_term[1:-1].split(',')
			for f in f_structure_array:
				f = f.replace("'",'').replace(" ",'').replace("\"","")
				if f not in structure_all and f != "":
					structure_all.append(f)
	with open(path+'/fsearch/structure.feature','w') as outfile:
		for structure in structure_all:
			print structure
			outfile.write(structure)
			outfile.write("\n")
	print len(structure_all)
	return
def get_all_constant():
	# get all structure feature and print to file
	constant_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.constant_term!= '[]':
			f_constant_array = f.constant_term[1:-1].split(',')
			for f in f_constant_array:
				f = f.replace("'",'').replace(" ",'').replace("\"","")
				if f not in constant_all and f != "":
					constant_all.append(f)
	with open(path+'/fsearch/constant.feature','w') as outfile:
		for constant in constant_all:
			print constant
			outfile.write(constant)
			outfile.write("\n")
	print len(constant_all)
	return
def get_all_semantic():
	# get all structure feature and print to file
	semantic_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.sorted_term!= '[]':
			f_semantic_array = f.sorted_term[1:-1].split(',')
			for line in f_semantic_array:
				fa = line.split('$')
				for f in fa:
					f = f.replace("'",'').replace(" ",'').replace("\"","").replace("[","").replace("]","")
					if f not in semantic_all and f != "":
						semantic_all.append(f)
	with open(path+'/fsearch/semantic.feature','w') as outfile:
		for semantic in semantic_all:
			print semantic
			outfile.write(semantic)
			outfile.write("\n")
	print len(semantic_all)
	return
def get_all_variable():
	# get all structure feature and print to file
	variable_all = []
	formula = Formula.objects.all()
	for f in formula:
		if f.variable_term!= '[]':
			f_variable_array = f.variable_term[1:-1].split(',')
			for f in f_variable_array:
				f = f.replace("'",'').replace(" ",'').replace("\"","")
				if f not in variable_all and f != "":
					variable_all.append(f)
	with open(path+'/fsearch/variable.feature','w') as outfile:
		for variable in variable_all:
			print variable
			outfile.write(variable)
			outfile.write("\n")
	print len(variable_all)
	return