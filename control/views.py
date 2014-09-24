from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect,HttpResponse
from ExamPapers.DBManagement.models import *
from django.template import RequestContext
import datetime
from ExamPapers.logic.common import *
from ExamPapers.logic.question_processing import *
from control.forms import *

def home(request,subj_id):
	param = {}
	param.update(current(subj_id))
	questions = Question.objects.filter(topic__block__subject__id = subj_id)
	for question in questions:
		question.short = question.content[:150]
	param['questions'] = questions
	param['papers'] = Paper.objects.filter(subject__id = subj_id)
	topics = Topic.objects.filter(block__subject__id = subj_id)
	for t in topics:
		t.question = Question.objects.filter(topic = t).count()
		
	param['topics'] = topics
	return render(request,'control/control.home.html', param)
	

def question(request,subj_id,qid):
	u = request.user
	
	param  = {}
	param.update(current(subj_id))
	

	if request.GET.get("qid") != None:
		qid = request.GET.get("qid")	
	# if no question selected --> default do 1st question
	if int(qid) == 0 or qid == None:
		qid = questions[0].id

	
	#Return param
	param['question'] = getViewQuestion(qid)
	param['answers'] = getAnswer(qid)
	
	return render_to_response('control/control.question.html', param,context_instance=RequestContext(request))


def edit(request, subj_id, qid):
	param = {}
	param.update(current(subj_id))

	question = Question.objects.get(pk=int(qid)) #get current object
			
	if request.method == "POST":
		form = DocumentForm(request.POST, request.FILES ,initial = {'subj_id_pass' : subj_id})	
				
		if form.is_valid():
			question = Question.objects.get(id = qid)
			#question.id = request.POST['id']
			question.paper = Paper.objects.get(id = request.POST['paper'])
			question.question_no = request.POST['question_no']
			question.content =  request.POST['content']
			question.topic =  Topic.objects.get(id = request.POST['topic'])
			question.subtopic =  Subtopic.objects.get(id = request.POST['subtopic'])
			question.marks = request.POST['marks']
			question.source = request.POST['source']
			question.difficulty = request.POST['difficulty']
			
			question.save()
			return  HttpResponseRedirect('/'+str(subj_id)+'/control/question/'+str(question.id)+"/")
	else:	
				form = DocumentForm(instance = question, initial = {'subj_id_pass' : subj_id}) 
	param['form'] = form
	return render_to_response('control/control.form.html',param,context_instance=RequestContext(request))






def mathbuddy_papers_auth(request,subj_id):
	return render(request,'account/login.html', {'subj_id': subj_id})

def mathbuddy_papers(request,subj_id):
	param = dict()
	
	param.update(mathbuddy_paper_sidebar_param(subj_id))
	param.update(current(subj_id))
	param['admin'] = isAdmin(request)

	return render(request,'control/mathbuddy_papers.html', param)

def mathbuddy_view_papers(request, subj_id):
	param = dict()

	paper = request.POST.getlist("paper")
	topic = request.POST.getlist("topic")
	param.update(mathbuddy_paper_sidebar_param(subj_id))
	param.update(mathbuddy_paper_view_param(paper, topic, subj_id))
	param['admin'] = isAdmin(request)

	return render(request,'control/mathbuddy_view_papers.html', param)
	
def mathbuddy_admin_form(request, subj_id, question_id):
	param = dict()

	param['subj_id'] = subj_id
	param['year_list'] = list(reversed(range(1995,datetime.datetime.now().year))) #up till previous year
	param['topics'] = list(Topic.objects.filter(block__subject_id=subj_id).order_by('id').values())

	#if less than 0, insert new question
	param['question'] = None
	if int(question_id) >= 0:
		param['question'] = Question.objects.get(id=question_id)
		param['topic'] = param['question'].topic_id.title
		param['subtopic'] = param['question'].subtopic_id.title
		param['subtopics']=list(Subtopic.objects.filter(topic_id=param['question'].topic_id).values())
		param['paper'] = Paper.objects.get(id=param['question'].paper_id)
		param['display'] = '\n'+param['question'].content.replace(';', '\n')
		if len(Answer.objects.filter(question_id=question_id)) == 1:
			param['answer'] = '\n'+Answer.objects.get(question_id=question_id).content.replace(';', '\n')
		else:
			param['answer'] = "More than 1 answer for these question is found. Please check your database."
		param['qnsNoRange'] = getQuestionNumRange(param['paper'], param['question'].question_no)
	else:
		param['subtopics'] = list(Subtopic.objects.filter(topic_id=param['topics'][0]['id']).values())
		param['qnsNoRange'] = getQuestionNumRange(getPaperId(str(param['year_list'][0]), '6', '1', subj_id), '-1')

	param['answertypes'] = list(AnswerType.objects.all().values())
	finalanswerlist = list(Answer.objects.filter(question_id=question_id).order_by('part_no').values('answertype_id', 'part_no', 'content','switch'))
	for fa in finalanswerlist:
		if fa['content'] is not None and fa['content'] != '':
			fa['content'] = fa['content'].replace(';','\n')
	param['finalanswer'] = finalanswerlist
	param['exe_input'] = getExerciseInputImages()

	return render(request, 'control/mathbuddy_admin_form.html', param)
	


def mathbuddy_admin_delete(request,subj_id, question_id):
	deleteQuestion(question_id)
	return mathbuddy_papers(request, subj_id)

def mathbuddy_paper_sidebar_param(subj_id):
	param = dict()

	param['cur_subj_h1'] = Subject.objects.get(id=subj_id)
	param['papers'] = list(Paper.objects.filter(subject_id=subj_id, number__gt=0).only('id', 'year', 'month', 'number').order_by('id').values())
	topics = list(Topic.objects.filter(block__subject_id=subj_id).order_by('id').values())
	param['topics'] = topics

	subtopics = list()
	for t in topics:
		tempst = list(Subtopic.objects.filter(topic_id=t['id']).values())
		for st in tempst:
			subtopics.append(st)

	param['subtopics'] = subtopics

	return param

def mathbuddy_paper_view_param(paper,topic, subj_id):
	param = dict()
	querypaper = ""
	if len(paper) >= 1 and paper[0] != "all":
		querypaper = reduce(lambda q, value: q|Q(paper_id=value), paper, Q())

	querytopic = ""
	if len(topic) >= 1 and topic[0] != "all":
		querytopic = reduce(lambda q, value: q|Q(topic_id=value), topic, Q())

	param.update(retainPaperTopicChkbox(paper, topic, querypaper, querytopic))

	param['questions'] = getSelectedQuestionFromDB(querypaper, querytopic, subj_id)
	param["total_num_qns"] = len(param['questions'])

	for q in param['questions']:
		q['content'] = format_question(q, "Question")
		p = Paper.objects.get(id=q['paper_id_id'])
		q['paper'] = str(p.year) + ' ' + p.month + ' Paper ' + str(p.number)
		q['qtopic'] = Topic.objects.get(id=q['topic_id_id']).title
		q['qsubtopic'] = Subtopic.objects.get(id=q['subtopic_id_id']).title

		if len(Answer.objects.filter(question_id=q['id'])) > 0:
			ans = list(Answer.objects.filter(question_id=q['id']).values())
			q['qanswer'] = format_answer(ans, "Answer")
		else:
			q['qanswer'] = dict()
	return param

def retainPaperTopicChkbox(paper, topic, querypaper, querytopic):
	param = dict()

	param['paperselected'] = paper
	param['topicselected'] = topic

	if querypaper == "":
		param['allpaperselected'] = True

	if querytopic == "":
		param['alltopicselected'] = True

	return param

def getSelectedQuestionFromDB(querypaper, querytopic, subj_id):
	if querypaper != "" and querytopic != "":
		return list(Question.objects.filter(querypaper, querytopic).order_by('id').values())
	elif querypaper != "":
		return list(Question.objects.filter(querypaper).order_by('id').values())
	elif querytopic != "":
		return list(Question.objects.filter(querytopic).order_by('id').values())
	else:
		subj_paperdict = list(Paper.objects.filter(subject_id = subj_id).values('id'))
		subj_paperlist = list()
		for pid in subj_paperdict:
			subj_paperlist.append(pid['id'])
		querysubj_paper = reduce(lambda q, value: q|Q(paper_id=value), subj_paperlist, Q())
		return list(Question.objects.filter(querysubj_paper).order_by('id').values())

def isAdmin(request):
	if request.path.__contains__("admin"):
		return True
	else:
		return False

def getQuestionNumRange(paper_id, qns_no):
	qnsNum_available = defaultQuestionNumRange()
	qns_list = Question.objects.filter(paper_id=paper_id).values()
	qnsNum_used = list()
	for q in qns_list:
		qnsNum_used.append(q['question_no'])

	for q in qnsNum_used:
		if q != qns_no:
			qnsNum_available.remove(q)
	return qnsNum_available
	
def getPaperId(q_year, q_month, q_num, subj_id):
	q_paper_id = q_year

	if q_month == '6' and q_num == '1':
		q_paper_id += '01'
	elif q_month == '6' and q_num == '2':
		q_paper_id += '02'
	elif q_month == '11' and q_num == '1':
		q_paper_id += '03'
	elif q_month == '11' and q_num == '2':
		q_paper_id += '04'
	q_paper_id += '{0:0>3}'.format(subj_id)

	return q_paper_id
	
def defaultQuestionNumRange():
	return range(1,32)
	
def getExerciseInputImages():
	inputList = list()

	exercise_input_file = ROOT_PATH+"/resource/static/exercise_input.txt"
	ins = open(exercise_input_file, "r" )

	tagContent = list()
	for latex in ins:
		latex = latex[:-1].strip()
		if latex.startswith("Tab:"):
			tagContent = list()
			inputList.append({'tabHeader': latex[4:], 'content': tagContent})
		elif latex == "":
			continue
		else:
			tagContent.append({'display': "$$"+latex+"$$", 'id': latex})
	return inputList