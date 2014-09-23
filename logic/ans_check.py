from __future__ import division
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
from ExamPapers.DBManagement.models import *
from ExamPapers.settings import ROOT_PATH
import re
import math

import urllib2
import urllib

#set java server Java Server
java_server='http://czh-restlet.ap01.aws.af.cm/'
# java_server='http://localhost:8080/java_func'

from ExamPapers.logic.common import *
from ExamPapers.logic.question_processing import *

def isProve(anstype):
	return (anstype == "Prove" or anstype == 1 or anstype == '1')

def isSketch(anstype):
	return (anstype == "Sketch" or anstype == 2 or anstype == '2')

def isNumeric(anstype):
	return (anstype == "Numeric" or anstype == 3 or anstype == '3')

def isExpression(anstype):
	return (anstype == "Expression" or anstype == 4 or anstype == '4')

def isText(anstype):
	return (anstype == "Text" or anstype == 5 or anstype == '5')

def extractLabelandAns(content):
	labellist = list()
	anslist = list()

	if content != '':
		labelanslist = content.split('"')
		counter = 0
		while counter < len(labelanslist):
			temp = ("$$"+labelanslist[counter]+"$$").replace(";", "$$<br/>$$").replace(" ", " \space ")
			labellist.append(temp)

			if (counter+1) < len(labelanslist):
				anslist.append(labelanslist[counter+1])
			counter+=2

	return {'labellist': labellist, 'anslist': anslist}
	
	
		
def getAllDistinctAnsType(answer):
	distinct_anstype = list()
	for a in answer:
		desc = AnswerType.objects.get(id=a['answertype_id']).description
		if not desc in distinct_anstype:
			distinct_anstype.append(desc)
	return distinct_anstype

def format_ans(str):
	return str.replace("\\left","").replace("\\right","").strip()

def find_all(substr,string):
	return [m.start() for m in re.finditer("r'\b"+substr+"\b'", string)]

def checkAns(user_inputs,actual_ans, anstype):
	if isNumeric(anstype):
		return checkNumericAnsType(user_inputs, actual_ans)

	elif isExpression(anstype):
		return checkExpressionAnsType(user_inputs, actual_ans)

	elif isText(anstype):
		return checkTextAnsType(user_inputs, actual_ans)

	elif isProve(anstype):
		# return checkProveAnsType(user_inputs, actual_ans)
		result = checkExpressionAnsType(user_inputs, actual_ans)
		if result != 'True':
			return checkNumericAnsType(user_inputs, actual_ans)
		else:
			return result

	return 'False'

def checkNumericAnsType(user_inputs, actual_ans):
	if format_ans(user_inputs) != '':
		userans = latex2numeric(format_ans(user_inputs))
		if userans == 'hasSyntaxError':
			return userans
		else:
			actualans = latex2numeric(format_ans(actual_ans))
			if userans == actualans:
				return 'True'
	else:
		return "isEmpty"

	return 'False'

def checkExpressionAnsType(user_inputs, actual_ans):
	if format_ans(user_inputs) != '':
		userans = latex2asciiMathml(format_ans(user_inputs))
		actualans = latex2asciiMathml(format_ans(actual_ans))
		javaParam = urllib.urlencode({"userans": userans, "actualans": actualans})
		
		result = urllib2.urlopen(java_server+"/solchk",javaParam).read()
		if result == 'True':
			return 'True'
	else:
		return "isEmpty"
	return 'False'

def checkTextAnsType(user_inputs, actual_ans):
	if format_ans(user_inputs) != '':
		if format_ans(user_inputs).lower() == format_ans(actual_ans).lower():
			return 'True'
	else:
		return "isEmpty"

def checkProveAnsType(user_inputs, actual_ans):
	if format_ans(user_inputs) != '':
		userans = latex2Expression(format_ans(user_inputs))
		actualans = latex2Expression(format_ans(actual_ans))
		if userans == actualans:
			return "True"
	else:
		return "isEmpty"
	return 'False'

def latex2asciiMathml(value):
	
	#step1: remove all white spaces
	val=value
	val=re.sub(r'\s', '', val)
	val=re.sub(r'^\\\[', '', val)
	val=re.sub(r'\\\]$', '', val)
	val=re.sub(r'^\$\$', '', val)
	val=re.sub(r'\$\$$', '', val)
	
	#step2: replace functions
	
	#2: fractions
	eq_start=val.find("\\frac")	
	while(eq_start>-1):
		temp=val[:eq_start]+"("
		end=eq_start+5
		for i in range(0,2):			
			if(val[end]!='{'):
				return "Error in \\frac at "+str(end)+" require {"
			end=end+1
			start=end
			opCount=1	#set end and opCount as confirm is '{'
			while(val[end]!='}'or opCount!=0):
				end=end+1
				if (val[end]=='{'):
					opCount=opCount+1
				elif (val[end]=='}'):
					opCount=opCount-1
			temp=temp+"("+val[start:end]+")/"
			end=end+1 #start next{}
		temp=temp.rstrip('/')+")"+val[end:]
		val=temp
		eq_start=val.find("\\frac")

	#2: square root special case
	eq_start=val.find("\\sqrt[")
	while(eq_start>=0):
		temp=val[:eq_start]+"(root("
		#obtain root
		end=eq_start+5
		opCount=1
		while(val[end]!=']'or opCount!=0):
			end=end+1
			if (val[end]=='['):
				opCount=opCount+1
			elif (val[end]==']'):
				opCount=opCount-1
		temp=temp+val[eq_start+6:end]+")("
		#obtain value
		eq_start=end+1
		end=eq_start
		opCount=1
		while(val[end]!='}'or opCount!=0):
			end=end+1
			if (val[end]=='{'):
				opCount=opCount+1
			elif (val[end]=='}'):
				opCount=opCount-1
		temp=temp+val[eq_start+1:end]+"))"+val[end+1:]
		#store results and check for another instance
		val=temp
		eq_start=val.find("\\sqrt[")
		
	#for general functions
	patt=[]
	patt.append({'pre':"\\overrightarrow",'post':'(vec','end':')'})
	patt.append({'pre':"\\underline",'post':'(ul','end':')'})
	patt.append({'pre':"\\overline",'post':'(bar','end':')'})
	patt.append({'pre':"\\mathrm",'post':' mbox','end':' '})
	patt.append({'pre':"\\sqrt",'post':'(sqrt','end':')'})
	patt.append({'pre':"\\ddot",'post':'(ddot','end':')'})
	patt.append({'pre':"\\vec",'post':'(vec','end':')'})	
	patt.append({'pre':"\\bar",'post':'(bar','end':')'})	
	patt.append({'pre':"\\hat",'post':'(hat','end':')'})	
	patt.append({'pre':"\\dot",'post':'(dot','end':')'})	
	patt.append({'pre':"^",'post':"^",'end':''})
	patt.append({'pre':"_",'post':'_','end':''})				
	
	for p in patt:
		eq_start=val.find(p['pre']+"{")
		while(eq_start>=0):
			temp=val[:eq_start]+p['post']
			end=eq_start				
			opCount=0
			start=-1
			while(val[end]!='}'or opCount!=0):
				end=end+1
				if (val[end]=='{'):
					opCount=opCount+1
					if(start==-1):
						start=end
				elif (val[end]=='}'):
					opCount=opCount-1
			temp=temp+"("+val[start+1:end]+")"+p['end']+val[end+1:]
			val=temp
			eq_start=val.find(p['pre']+"{")		
			
			
	#step3: replace symbols (and enclose in bracket to represent a unit)
	val=val.replace('\\varepsilon',' varepsilon ')
	val=val.replace('\\bigtriangledown',' grad ')
	val=val.replace('\\Leftrightarrow',' fArr ')
	val=val.replace('\\leftrightarrow',' harr ')
	val=val.replace('\\diamond',' diamond ')
	val=val.replace('\\epsilon',' epsilon ')	
	val=val.replace('\\upsilon',' upsilon ')
	val=val.replace('\\rightarrow',' rarr ')
	val=val.replace('\\Rightarrow',' rArr ')
	val=val.replace('\\leftarrow',' larr ')
	val=val.replace('\\Leftarrow',' lArr ')
	val=val.replace('\\downarrow',' darr ')	
	val=val.replace('\\setminus',' \\\\ ')
	val=val.replace('\\Lambda',' Lambda ')
	val=val.replace('\\lambda',' lambda ')	
	val=val.replace('\\subseteq',' sube ')	
	val=val.replace('\\supseteq',' supe ')
	val=val.replace('\\parallel',' |\\| ')			
	val=val.replace('\\bigwedge',' ^^^ ')	
	val=val.replace('\\superset',' sup ')
	val=val.replace('\\uparrow',' uarr ')
	val=val.replace('\\bigotimes',' ox ')
	val=val.replace('\\propto',' prop ')	
	val=val.replace('\\bigoplus',' o+ ')
	val=val.replace('\\Sigma',' Sigma ')
	val=val.replace('\\Gamma',' Gamma ')
	val=val.replace('\\omega',' omega ')
	val=val.replace('\\alpha',' alpha ')	
	val=val.replace('\\gamma',' gamma ')	
	val=val.replace('\\theta',' theta ')
	val=val.replace('\\sigma',' sigma ')
	val=val.replace('\\Delta',' Delta ')
	val=val.replace('\\Omega',' Omega ')
	val=val.replace('\\Theta',' Theta ')
	val=val.replace('\\lfloor',' |__ ')
	val=val.replace('\\rfloor',' __| ')		
	val=val.replace('\\bigodot',' o. ')
	val=val.replace('\\models',' |== ')
	val=val.replace('\\subset',' sub ')
	val=val.replace('\\nabla',' grad ')	
	val=val.replace('\\bigcap',' nnn ')
	val=val.replace('\\bigcup',' uuu ')
	val=val.replace('\\bigvee',' vvv ')
	val=val.replace('\\mapsto',' |->')	
	val=val.replace('\\sinh', ' sinh ')
	val=val.replace('\\cosh', ' cosh ')
	val=val.replace('\\tanh', ' tanh ')
	val=val.replace('\\forall', ' AA ')
	val=val.replace('\\prod', ' prod ')
	val=val.replace('\\oint', ' oint ')
	val=val.replace('\\otimes', ' ox ')
	val=val.replace('\\beta', ' beta ')
	val=val.replace('\\zeta', ' zeta ')
	val=val.replace('\\vdash', ' |-- ')
	val=val.replace('\\approx', ' ~~ ')
	val=val.replace('\\|', ' |\\\\| ')
	val=val.replace('\\lceil', ' |~ ')
	val=val.replace('\\rceil', ' ~| ')
	val=val.replace('\\perp', ' _|_ ')
	val=val.replace('\\equiv', ' -= ')
	val=val.replace('\\oplus', ' o+ ')
	val=val.replace('\\wedge', ' ^^ ')
	val=val.replace('\\times', ' xx ')
	val=val.replace('\\infty', ' oo ')
	val=val.replace('\\neg', ' not ')
	val=val.replace('\\sum', ' sum ')
	val=val.replace('\\odot', ' o. ')
	val=val.replace('\\Phi', ' Phi ')
	val=val.replace('\\Psi', ' Psi ')
	val=val.replace('\\tau', ' tau ')
	val=val.replace('\\rho', ' rho ')
	val=val.replace('\\phi', ' phi ')
	val=val.replace('\\eta', ' eta ')
	val=val.replace('\\prec', ' -< ')
	val=val.replace('\\int', ' int ')
	val=val.replace('\\cong', ' ~= ')
	val=val.replace('\\sin', ' sin ')
	val=val.replace('\\cos', ' cos ')
	val=val.replace('\\tan', ' tan ')
	val=val.replace('\\csc', ' csc ')
	val=val.replace('\\sec', ' sec ')
	val=val.replace('\\cot', ' cot ')
	val=val.replace('\\log', ' log ')
	val=val.replace('\\det', ' det ')
	val=val.replace('\\dim', ' dim ')
	val=val.replace('\\lim', ' lim ')
	val=val.replace('\\gcd', ' gcd ')
	val=val.replace('\\min', ' min ')
	val=val.replace('\\max', ' max ')
	val=val.replace('\\leq', ' <= ')
	val=val.replace('\\geq', ' >= ')
	val=val.replace('\\ast', ' ** ')
	val=val.replace('\\cap', ' nn ')
	val=val.replace('\\cup', ' uu ')
	val=val.replace('\\vee', ' vv ')
	val=val.replace('\\div', ' -: ')
	val=val.replace('\\circ', ' @ ')
	val=val.replace('\\succ', ' > ')
	val=val.replace('\\neq', ' != ')
	val=val.replace('\\mu', ' mu ')
	val=val.replace('\\pi', ' pi ')
	val=val.replace('\\nu', ' nu ')
	val=val.replace('\\xi', ' xi ')
	val=val.replace('\\Xi', ' Xi ')
	val=val.replace('\\Pi', ' Pi ')
	val=val.replace('\\pm', ' +- ')
	val=val.replace('\\in', ' in ')
	val=val.replace('\\ln', ' ln ')
	val=val.replace('\\notin', ' !in ')
	val=val.replace('\\exp', ' exp ')
	val=val.replace('\\mp', ' -+ ')
					
	#val=val.replace('','')
		
	return val

def latex2numeric(value):
	val = latex2sympy(value)
	try:
		return round_figures(parse_expr(val).evalf(), 3)
	except:
		return "hasSyntaxError"

def latex2Expression(value):
	x, y, z, t = symbols('x y z t')
	val = latex2sympy(value)
	return simplify(parse_expr(val))

def latex2sympy(value):
	#step1: remove all white spaces
	val=value
	val=re.sub(r'\s', '', val)
	val=re.sub(r'^\\\[', '', val)
	val=re.sub(r'\\\]$', '', val)
	val=re.sub(r'^\$\$', '', val)
	val=re.sub(r'\$\$$', '', val)

	#step2: replace functions

	#2: fractions
	eq_start=val.find("\\frac")
	while(eq_start>-1):
		temp=val[:eq_start]
		end=eq_start+5
		temp+='('
		for i in range(0,2):
			if(val[end]!='{'):
				return "Error in \\frac at "+str(end)+" require {"
			end=end+1
			start=end
			opCount=1	#set end and opCount as confirm is '{'
			while(val[end]!='}'or opCount!=0):
				end=end+1
				if (val[end]=='{'):
					opCount=opCount+1
				elif (val[end]=='}'):
					opCount=opCount-1
			temp=temp+"("+val[start:end]+")/"
			end=end+1 #start next{}
		temp=temp.rstrip('/')+')'+val[end:]
		val=temp
		eq_start=val.find("\\frac")

	#2: square root special case - \\sqrt[3]{27} to 27**((1)/(3))
	eq_start=val.find("\\sqrt[")
	while(eq_start>=0):
		temp=val[:eq_start]
		end=eq_start+6
		start = end
		temp+="("
		opCount=1
		while(val[end]!=']'or opCount!=0):
			end=end+1
			if (val[end]=='['):
				opCount=opCount+1
			elif (val[end]==']'):
				opCount=opCount-1
		#obtain root
		root = val[start:end]

		#obtain value
		eq_start=end+1
		end=eq_start
		opCount=1
		while(val[end]!='}'or opCount!=0):
			end=end+1
			if (val[end]=='{'):
				opCount=opCount+1
			elif (val[end]=='}'):
				opCount=opCount-1

		temp=temp+val[eq_start+1:end]+"^(1/"+root+"))"+val[end+1:]
		#store results and check for another instance
		val=temp
		eq_start=val.find("\\sqrt[")

	#2: trigo special case - \\sin^{-1}{x} to asin...etc.
	val=val.replace('sin^{-1}', 'asin')
	val=val.replace('cos^{-1}', 'acos')
	val=val.replace('tan^{-1}', 'atan')

	#2: trigo special case - \\sin^{2}{x} to sin(x)**(2)...etc.
	#code here#

	#2: others function - remove \\ and change {} to ()
	# func =["\\sqrt", "\\ln", "\\sin", "\\cos", "\\tan"]
	# for f in func:
	# 	eq_start=val.find(f)
	# 	while(eq_start>-1):
	# 		temp=val[:eq_start]
	# 		end=eq_start+len(f)
	# 		temp+=f[1:]+'('
	# 		opCount=1	#set end and opCount as confirm is '{'
	# 		while(val[end]!='}'or opCount!=0):
	# 			end=end+1
	# 			if (val[end]=='{'):
	# 				opCount=opCount+1
	# 			elif (val[end]=='}'):
	# 				opCount=opCount-1
	# 		start= eq_start+len(f)+1
	# 		temp=temp + val[start:end]+")"+val[end+1:]
	# 		end=end+1 #start next{}
	#
	# 		val=temp
	# 		eq_start=val.find(f)

	#step3: replace symbols
	val=val.replace('\\','')
	val=val.replace('{','(')
	val=val.replace('}',')')
	val=val.replace('[','(')
	val=val.replace(']',')')
	val=val.replace('^', '**')
	val=val.replace('e', 'exp(1)')

	#print val
	return val

def round_figures(x, n):

	if x == 0 :
		return 0
	else:
		return round(x, int(n - math.ceil(math.log10(abs(x)))))
		
def check_qns_solution(qid, user_inputs):
	
	param = dict()
	param['qid'] = qid
	param['totalAns'] = len(user_inputs)

	finalanswer = list(Answer.objects.filter(question = qid).values())

	new_user_inputs = list()
	actual_ans = list()
	facount = 0
	if len(finalanswer) > 0:
		for fa in finalanswer:
			if not isSketch(fa['answertype_id']) and fa['content'] != '':
				tempDict = extractLabelandAns(fa['content'])
				actual_ans.append({'value': tempDict['anslist'], 'id': fa['answertype_id'], 'switch':fa['switch']})
				if len(tempDict['anslist']) > 1:
					user_anslist = list()
					for index, a in enumerate(tempDict['anslist']):
						user_anslist.append(user_inputs[facount+index])
						
					facount += len(tempDict['anslist'])
					new_user_inputs.append(user_anslist)
				else:
					new_user_inputs.append(user_inputs[facount])
					facount += 1

	correctans = 0
	resultList = list()
	if len(new_user_inputs) == len(actual_ans):
		for index, a in enumerate(actual_ans):
			u_input = new_user_inputs[index]
			if isinstance(u_input, list):
				if a['switch']:
					for u in u_input:
						for v in a['value'][:]:
							result = checkAns(u, v, a['id'])
							if result != 'True' and result != 'False':
								param[result] = result
								
							else:
							#	print u, v, result, 'multi switch'
								#print result
								if result == 'True':
									correctans += 1
									a['value'].remove(v)
									break
						resultList.append(result)
				else:
					counter = 0
					for v in a['value']:
						result = checkAns(u_input[counter], v, a['id'])
						resultList.append(result)
						if result != 'True' and result != 'False':
							param[result] = result
						else:
						#	print u_input[counter], v, result, 'multi no switch'
							#print result
							if result == 'True':
								correctans += 1
						counter += 1
			else:
				
				result = checkAns(u_input, a['value'][0], a['id'])
				resultList.append(result)
				if result != 'True' and result != 'False':
					param[result] = result
				else:
					#print u_input, a['value'][0], result, 'no switch'
					#print result
					if result == 'True':
						correctans += 1
	

	param['resultList'] = resultList
	param['numCorrect'] = correctans
	
	return 	param
	
