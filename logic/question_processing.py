from __future__ import division
from ExamPapers.DBManagement.models import *
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
from ExamPapers.DBManagement.models import Image
from ExamPapers.settings import ROOT_PATH
import re
import math

from ExamPapers.logic.question_processing import *
from ExamPapers.logic.ans_check import *

def getViewQuestion(qid):
	"""
	Get question for view page
	Input: question id
	Output: Question object including all attributes and formated content and solution
	"""
	question = Question.objects.get(id=qid)
	answer = list(Answer.objects.filter(question_id=question.id).values())
	question.content = formatContent(question, "Question")
	question.topic = Topic.objects.get(id=question.topic_id)
	question.subtopic = Subtopic.objects.get(id=question.subtopic_id)
	question.distinct_anstype = getAllDistinctAnsType(answer)
	question.stars = star((question.marks+1)/2)
	question.solution = formatContent(question,"Solution")
	question.answer = "Not available"
	if Answer.objects.filter(question = question.id).count != 0:
		question.answer = Answer.objects.filter(question = question.id)
	return question

def formatContent(question,type):
	"""
	Format question content and solution, convert image and align content
	Input: question object, content type: Question or Solution
	Output: formated content
	"""
	images = list(Image.objects.filter(qa_id=question.id, qa=type).only('id','imagepath').order_by('id').values())
	if type == "Question":
		for i in images:
			html_img = "<tempimage style = 'width:200px' src='" + i['imagepath'] + "' alt='" + i['imagepath'] + "' />"
			question.content = question.content.replace('img', html_img, 1)
		question.content = question.content.replace('<tempimage', '<img')
		question.content = question.content.replace(';','<br/>')
		return question.content
	if type =="Solution":
		solutionContent = "Not available"
		if Solution.objects.filter(question_id = question.id).count() != 0:
			solutionContent  = Solution.objects.get(question_id = question.id).content
		for i in images:
			html_img = "<tempimage style = 'width:200px' src='" + i['imagepath'] + "' alt='" + i['imagepath'] + "' />"
			solutionContent = solutionContent.replace('img', html_img, 1)
		solutionContent = solutionContent.replace('<tempimage', '<img')
		solutionContent = solutionContent.replace(';','<br/>')
		return solutionContent
		
def getAllDistinctAnsType(answer):
	distinct_anstype = list()
	for a in answer:
		desc = AnswerType.objects.get(id=a['answertype_id']).description
		if not desc in distinct_anstype:
			distinct_anstype.append(desc)
	return distinct_anstype

def star(rate):
	"Convert difficulty int value to star icon using bootstrap star"
	stars = []
	for s in range(int(rate)):
		stars.append("<i class='glyphicon glyphicon-star '></i>")
	#for s in range(5-rate):
	#	stars.append("<i class='glyphicon glyphicon-star-empty'></i>")
	return stars
	
def formatIntoLabelDictList(labellist, anslist):
	dictList = list()
	counter = 1

	for ll in labellist:
		try:
			dictList.append({'sub': counter, 'label': ll, 'ans':anslist[counter-1]})
		except IndexError:
			dictList.append({'sub': counter, 'label': ll})
		counter += 1

	return dictList
	
def display_finalanswer(finalanswer):
	curr_qns_id = ''
	currqnscount = 1
	noanscount = 0

	for fa in finalanswer:
		if fa.content is not None and fa.content!='':
			tempDict = extractLabelandAns(fa.content)
			fa.labellist = formatIntoLabelDictList(tempDict['labellist'], tempDict['anslist'])
			
		if isSketch(fa.answertype_id) or fa.content == '':
			anstype = AnswerType.objects.get(id=fa.answertype_id).description
			fa.label = " [" + anstype + " Question]. View Papers for detailed solution."
			noanscount += 1

		if curr_qns_id == fa.question_id:
			currqnscount += 1
		else:
			curr_qns_id = fa.question_id

	if currqnscount == noanscount:
		return None
	else:
		return finalanswer


def formatIntoLabelDictList(labellist, anslist):
	dictList = list()
	counter = 0

	for ll in labellist:
		try:
			dictList.append({'sub': counter, 'label': ll, 'ans':anslist[counter] , 'counter':counter})
		except IndexError:
			dictList.append({'sub': counter, 'label': ll})
		counter += 1

	return dictList

def getAllDistinctAnsType(finalanswer):
	distinct_anstype = list()
	for fa in finalanswer:
		desc = AnswerType.objects.get(id=fa['answertype_id']).description
		if not desc in distinct_anstype:
			distinct_anstype.append(desc)
	return distinct_anstype

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
	
def getAnswer(qid):
	answers = Answer.objects.filter(question_id = qid)
	return display_finalanswer(answers)
