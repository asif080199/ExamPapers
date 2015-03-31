from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User
from django.db.models import Avg

from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.models import Comment

from DBManagement.models import *

from datetime import datetime, timedelta

import math, re, random, sys
from ExamPapers.views import current, getViewQuestion

@login_required
def papertest(request, subj_id, test_id=None):
    "Boombastic function! Change with care."
    # Record usage for stats purpose
    page = "paper_test"
    # Never accessed this page before, or last access was more than 10 mins ago
    #if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        #usage = UserUsage(user=request.user, page=page)
        #usage.save()
        #request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Obtain the list of topics
    topics = Topic.objects.filter(block__subject_id = subj_id)

    if not test_id:
        if request.method == 'POST' and 'test_id' in request.POST and request.POST['test_id']:
            return redirect('/papertest/'+request.POST['test_id']+'/')
        elif request.method == 'POST' and 'num_qn' in request.POST and request.POST['num_qn'] and 'topics' in request.POST:
            # Check if all param is in
            # Get number of questions and difficulty

            numQns = int(request.POST['num_qn'])
            if numQns > 25:
                numQns = 25

            testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

            #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
            new_test = Test(id=testid, assessment=Assessment.objects.all().get(name='Paper Test'))
            new_test.save()

            numQns = int(numQns)

            topics_selected = request.POST.getlist('topics')

            topics_all = list(topics.values_list('id', flat=True))

            for topic_id in topics_selected:
                topics_all.remove(int(topic_id))

            question_pool = Question.objects.all()
            question_pool = question_pool.exclude(topic__in=topics_all)

            for i in range (0, numQns):
                # Get a random question and add to paper
                question_pool = question_pool.exclude(id__in=new_test.questions.all().values_list('id'))
                """ I don't get this. Isn't it just random /ly/"""
                if question_pool:
                    question = question_pool[random.randint(0, question_pool.count()-1)]
                    newTestQuestion = TestQuestion(question=question, test=new_test)
                    newTestQuestion.save()
                """ I don't get this. Isn't it just random /ly/"""
            return redirect('/'+subj_id+'/paper/papertest/'+str(testid)+'/')
        elif request.method == 'POST':
			
            error = {}
            if 'num_qn' not in request.POST or not request.POST['num_qn']:
                error['num_qn'] = True
            param = {}
            param.update(current(subj_id))
            param['error'] = error
            param['topics'] = topics
            return render(request, 'paper/papertest.home.html', param)
        param = {}
        param.update(current(subj_id))
        param['topics'] = topics
        return render(request, 'paper/papertest.home.html', param)
    else:
        # test_id is available, render test instead
        test = Test.objects.get(id=test_id)
        testQuestion = []
        for question in test.questions.all():
			question = getViewQuestion(question.id)
			testQuestion.append(question)
        param = {}
        param.update(current(subj_id))
        param['testQuestion'] = testQuestion
        param['test'] = test
        return render(request, 'paper/papertest.question.html', param)

@login_required
def solution(request, subj_id, test_id):
	test = Test.objects.all().get(id=test_id)
	testQuestion = []
	for question in test.questions.all():
		question = getViewQuestion(question.id)
		testQuestion.append(question)
	param = {}
	param['testQuestion'] = testQuestion
	param.update(current(subj_id))
	param['test'] = test
	return render(request, 'paper/papertest.solution.html', param)

@login_required
def papertestutil(request, test_id=None, util_name=None):
    "Util functions for Boombastic function!"

    if test_id:
        test = Test.objects.all().get(id=test_id)
        # Util to return test endtime
        if util_name == 'getendtime':
            time = test.questions.count()*3
            endtime = test.generated+timedelta(minutes=time)

            return HttpResponse(endtime.isoformat())
        elif util_name == 'save':
            if 'qn_id' in request.POST and request.POST['qn_id']:
                # Get question (or nothing) from orm
                question = Question.objects.all().get(id=request.POST['qn_id'])

                # Check test not completed, question exists
                if test.state == False and test.questions.filter(id=question.id).exists():
                    # Check that there was a answer sent together with message
                    if 'answer' in request.POST and request.POST['answer']:
                        try:
                            # Previously saved response available? Resave if so!
                            test_response = TestResponse.objects.filter(test=test).filter(user=request.user).get(question=question)
                            test_response.response = request.POST['answer']
                            test_response.save()
                        # Otherwise new response, create object
                        except ObjectDoesNotExist:
                            test_response = TestResponse(test=test, user=request.user, question=question, response=request.POST['answer'], criterion=question.marks, assessment=test.assessment)
                            test_response.save()

                        return HttpResponse("Saved")
                    # Otherwise no answer just return nothing happened!
                    else:
                        return HttpResponse("Empty")
    raise Http404
