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
	question.solution = "Not available"
	question.solution = formatContent(question,"Solution")
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
	
