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
from logic import assessment_engine, formatter_engine
from cat import forms
from logic.common import *
from logic.question_processing import *

from datetime import datetime, timedelta

import math, re, random, sys

@login_required
def trialtest(request,subj_id):
    "Placeholder for trial test"
    # Obtain the list of topics
    topics = Topic.objects.filter(block__subject_id = subj_id)

    # Record usage for stats purpose
    page = "cat_test"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    if 'complete' in request.GET and request.GET['complete']:
        complete = True
        if 'ability' in request.GET and request.GET['ability']:
            ability = request.GET['ability']
    else:
        complete = False
        ability = None
	param = {}
	param['topics'] = topics
	param['complete'] = complete
	param['ability'] = ability
	param.update(current(subj_id))
    return render(request, 'cat/trialtest.html', param)

@login_required
def trialtest_generate(request,subj_id):
    if request.method == 'POST':
        testid = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for i in range(6))

        #### VERY IMPORTANT TODO:: CHECK FOR UNIQUE ID
        new_test = Test(id=testid, assessment=Assessment.objects.all().get(name='CAT Test'))
        new_test.save()

        # Clear previous test questions if any
        request.session['trialtest_current_qn'] = None

        # Store topic in session, change this to db storage soon
        request.session['trialtest_topic_id'] = int(request.POST['topic'])

        return redirect('/'+str(subj_id)+'/cat/go/'+testid+'/')
    return redirect('/')

@login_required
def trialtest_go(request, test_id,subj_id):
    # Obtain the list of topics
    topics = Topic.objects.filter(block__subject_id = subj_id)

    # Get Test object
    test = Test.objects.all().get(id=test_id)

    # Selected topic
    topic_id = request.session['trialtest_topic_id']
    if topic_id > 0:
        topic = Topic.objects.all().get(id=topic_id)
    else:
        topic = None

    # Init session variable for question
    if 'trialtest_current_qn' not in request.session:
        request.session['trialtest_current_qn'] = None

    # Debug data
    debug = {}

    # Error data
    error = {}

    # GET Request or POST w/o session data >> Load Question
    # POST Request >> Answer Question
    if request.method == 'GET' or request.session['trialtest_current_qn'] is None:
   
        # Generate new question if not resuming
        if request.session['trialtest_current_qn'] == None:
            # Get assessment engine for CAT Test and dynamically load engine
            active_engine = Assessment.objects.all().get(name='CAT Test')
            engine = getattr(assessment_engine, active_engine.engine)()

            # Initialise session storage for assessment engine
            if 'engine_store' not in request.session:
                request.session['engine_store'] = None

            # Request a new question from the assessment engine
            question = engine.get_next_question(user=request.user, test=test, topic=topic, session_store=request.session['engine_store'])

            # Get current ability for debug purposes
            debug['ability'] = engine.get_user_ability(user=request.user, test=test)

            # Test ends if question is None (out of questions), redirect to completion screen
            if not question:
				param = {}
				param['topics'] = topics
				param['complete'] = True
				param['ability'] = engine.get_user_ability(user=request.user, test=test)
				param.update(current(subj_id))
				return render(request, 'cat/trialtest.html', param)

            #debug['answer'] = question.answers.all()[0].content

            # Update the question to session (for persistance if user refresh page/relogin)
            request.session['trialtest_current_qn'] = question.id

            # Update time starts from here
            request.session['trialtest_time'] = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        else:
    
            # Reload question from session data if resuming practice or page refresh
            question = Question.objects.all().get(id=request.session['trialtest_current_qn'])

        # Rendering at end of page
    else:
        
        # Submitting a test question
        if 'qid' in request.POST and request.POST['qid']:
            qnid_post = request.POST['qid']
            
        else:
            qnid_post = None

        qnid_session = request.session['trialtest_current_qn']

        if qnid_post != qnid_session:
            # Something strange is happening, missing qid from form or mismatch between form and session, TODO: Handle this PROPERLY
            debug['qnid_post'] = qnid_post
            debug['qnid_session'] = qnid_session

        # Reload question from session data
        question = Question.objects.all().get(id=qnid_session)

        # Check if answer was submitted
        if request.POST:
            user_input_dict = {}
            qid = request.POST['qid']
            for key in request.POST:
				value = request.POST[key]
				if key!= "csrfmiddlewaretoken" and key!= "qid":
					while len(key)<4:
						key = "0"+key
					user_input_dict[(key[1:])] = value

					keys = []
					for key in user_input_dict:
						keys.append(key)
					keys.sort()
					
					user_input = []
					for key in keys:
						user_input.append(user_input_dict.get(key))
					
				
            # Get assessment engine for CAT Test and dynamically load engine
            active_engine = Assessment.objects.all().get(name='CAT Test')
            engine = getattr(assessment_engine, active_engine.engine)()

            # Initialise session storage for assessment engine
            if 'engine_store' not in request.session:
                request.session['engine_store'] = None

            # Match answer using assessment engine
            result = engine.match_answers(user=request.user, test=test, response=user_input, question=question, session_store=request.session['engine_store'])

            # Restore updated engine store
            request.session['engine_store'] = result['session_store']

            # Reset current practice qn to None
            request.session['trialtest_current_qn'] = None

            # Answer is correct if full points is awarded
            if result['correctness'] != 1:									#correctness				
                correct = True
            else:
                correct = False

            # Get correct answer
            #question.answer = question.answers.all()[0]

            # Terminating condition is true!
            if result['terminate']:
                ability_list = engine.get_user_ability_list(user=request.user, test=test)
                param = {}
                param['topics'] = topics
                param['ability'] =  result['ability']
                param['ability_list'] = ability_list
                param.update(current(subj_id))
                return render(request, 'cat/trialtest.html', param)

            # Format question for web mode
            formatter = formatter_engine.WebQuestionFormatter()
            question = getViewQuestion(question.id)
            question.difficulty = question.difficulty/2
            # Temp variable to allow ajax through https
            host = request.get_host()
            is_secure = not "localhost" in host

            # Kill debug for non test users
            if request.user.get_profile().debug is False:
                debug = {}

            #Get user input
            finalResult = []
            for i in range(len(user_input)):
				r = result['resultList'][i]
				tem = []
				if r == 'True':
					tem = [user_input[i],1]
				else:
					tem = [user_input[i],0]
				
				finalResult.append(tem)
			#debug	
            debug = {}
            debug['ability'] = engine.get_user_ability(user=request.user, test=test)
            param = {}

            param.update(current(subj_id))
            param['debug'] = debug
            param['question'] = question
            param['results'] = finalResult
            param['answers'] = getAnswer(question.id)
            param['topic'] = topic
            param['correct'] = correct
            param['is_secure'] = is_secure
            param['totalAns'] = result['totalAns']
            param['numCorrect'] = result['numCorrect']
            return render(request, 'cat/trialtest.submit.html',param)
        else:
            # Option not selected, prompt error
            error['unselected'] = False

    # Format question for web mode
    formatter = formatter_engine.WebQuestionFormatter()
    question = formatter.format(question)

    # Kill debug for non test users
    if request.user.get_profile().debug is False:
        debug = {}

    # Render question page
	param = {}
	param['question'] = question
	param['answers'] = getAnswer(question.id)
	param['topic'] = topic
	param['error'] = error
	param['debug'] = debug
	param['test_id'] = test_id
	param.update(current(subj_id))
    return render(request, 'cat/trialtest.question.html', param)

@login_required
def trialtestutil(request, test_id=None, util_name=None):
    "Util functions for Boombastic function!"

    if test_id:
        test = Test.objects.all().get(id=test_id)
        # Util to return question endtime
        if util_name == 'getendtime':
            # 5 mins from time the question was loaded
            endtime = datetime.strptime(request.session['trialtest_time'], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=5)

            return HttpResponse(endtime.isoformat())
    raise Http404


@login_required
def practice_resume(request):
    "Restore practice session into last state"

    if 'practice_current_qn' in request.session and request.session['practice_current_qn'] != None:
        # Load previous question by going to the respective practice url
        # Retrieve topic from question id in session
        question = Question.objects.all().get(id=request.session['practice_current_qn'])
        topid_id = int(question.topic.id)

        # Redirect to correct topical practice page
        return redirect('/practice/'+str(topid_id)+'/')

    else:
        # Go back to main practice page
        return redirect('/practice/')

@login_required
def practice_end(request):
    "End current practice session"

    if 'practice_current_qn' in request.session:
        del request.session['practice_current_qn']

    # Go back to main practice page
    return redirect('/practice/')

@login_required
def question_view(request, id, practiced=False):
    "Lets the user view the question with answers"

    # Question exists?
    question = Question.objects.all().get(id=id)
    if question:
        # Check if user has done question if practiced = true
        if practiced:
            user_practiced = Response.objects.all().filter(user=request.user).filter(question=id)
            if not user_practiced:
                return redirect('/')

        # Load question and render
        # Get correct answer
        question.answer = question.answers.all()[0]

        # Format question for web mode
        formatter = formatter_engine.WebQuestionFormatter()
        question = formatter.format(question)

        # Temp variable to allow ajax through https
        host = request.get_host()
        is_secure = not "localhost" in host

        return render(request, 'itemrtweb/question.view.html', {'question': question, 'topic': question.topic, 'host': host, 'is_secure': is_secure})

    else:
        return redirect('/')

    pass


@user_passes_test(lambda u: u.is_staff)
def controldownloadpaper(request, testid):
    "Control Panel Code"
    # Obtain the list of topics
    tests = Test.objects.all()

    # Get this test
    thisTest = Test.objects.all().get(id=testid)

    # Home mode
        # Show test responses
        # Open paper for testing
        # Download paper in LaTeX format

    # Question mode
        # Display all questions in test
        # Display dummy modify button
    questions = thisTest.questions.all()

    averagediff = thisTest.questions.all().aggregate(Avg('difficulty')).values()[0]

    # Stats mode
        # Currently not used
        # Paper users, scores, etc

    return render_to_response('itemrtweb/download.tex', {'tests': tests, 'testid': testid, 'thistest': thisTest, 'questions': questions, 'avgdiff': averagediff}, context_instance=RequestContext(request))

@csrf_exempt
def postdata(request):
    if request.method == 'POST':

        # loop through keys and values
        for key, value in request.POST.iteritems():
            pass

        return render_to_response('postdata.html', {'postdata': request.POST}, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def prototype(request, question_id=None):
    # Init
    selected_question = None

    # Obtain the list of topics
    topics = Topic.objects.all()

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))

    if request.method == 'POST':
        form = forms.InsertEditQuestionForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Check if question exists or need to create new
            if selected_question:
                # Edit existing question
                selected_question.content=form.cleaned_data['content']
                selected_question.difficulty=form.cleaned_data['difficulty']
                selected_question.topic=form.cleaned_data['topic']
                selected_question.save()

                answer = selected_question.answers.all()[0]
                answer.content = form.cleaned_data['answer']
                answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    # Check if solution exists
                    solution_exists = Solution.objects.all().filter(question=selected_question).count()

                    if solution_exists > 0:
                        # Update solution
                        solution = selected_question.solution
                        solution.content = form.cleaned_data['solution']
                        solution.save()
                    else:
                        # New solution for this question
                        solution = Solution(question=selected_question, content=form.cleaned_data['solution'])
                        solution.save()

                # Tag adding/deleting
                selected_question.tags.clear()
                for tag_name in form.cleaned_data['tags']:
                    # Check tag exists in db, otherwise add
                    # Currently no need since automatically verified
                    tag = Tag.objects.all().get(name=tag_name)

                    qn_tag = QuestionTag(question=selected_question, tag=tag)
                    qn_tag.save()

                return redirect('/prototype2/list/topic/'+ str(selected_question.topic.id) +'/?msg=Question '+ str(selected_question.id) +' edited successfully#question-'+ str(selected_question.id))
            else:
                # Insert new question
                question = Question(content=form.cleaned_data['content'], difficulty=form.cleaned_data['difficulty'], topic=form.cleaned_data['topic'])
                question.save()

                # Insert answer for question
                answer = Answer(question=question, content=form.cleaned_data['answer'])
                answer.save()

                # Insert solution if exists
                if form.cleaned_data['solution']:
                    solution = Solution(question=question, content=form.cleaned_data['solution'])
                    solution.save()

                for tag_name in form.cleaned_data['tags']:
                    # Check tag exists in db, otherwise add
                    # Currently no need since automatically verified
                    tag = Tag.objects.all().get(name=tag_name)

                    qn_tag = QuestionTag(question=question, tag=tag)
                    qn_tag.save()

                # Question inserted successfully!
                return redirect('/prototype2/list/topic/'+ str(question.topic.id) +'/?msg=Question '+ str(question.id) +' added successfully#question-'+ str(question.id))

        # Reply regardless valid
        return render(request, 'itemrtweb/manage.question.form.html', {'form': form, 'topics': topics, 'selected_question': selected_question})
    else:
        # Check if question exists or give blank form
        if selected_question:
            # Load existing question into a form
            form = forms.InsertEditQuestionForm(initial={'content':selected_question.content, 'difficulty':selected_question.difficulty, 'topic':selected_question.topic, 'answer':selected_question.answers.all()[0].content, 'tags': selected_question.tags.all().values_list('name', flat=True)})

            solution_exists = Solution.objects.all().filter(question=selected_question).count()

            if solution_exists > 0:
                form.fields["solution"].initial = selected_question.solution.content
        else:
            # Display new form for user to fill in
            form = forms.InsertEditQuestionForm()

    return render(request, 'itemrtweb/manage.question.form.html', {'form': form, 'topics': topics, 'selected_question': selected_question})

@user_passes_test(lambda u: u.is_staff)
def prototype3(request, question_id=None):
    # Init
    selected_question = None

    # Obtain the list of topics
    topics = Topic.objects.all()

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))

    # Check if question exists otherwise redirect to question list
    if selected_question:
        # Hide question and save. Then give message to user
        selected_question.is_active = False
        selected_question.save()

        return redirect('/prototype2/?msg=Question has been deleted')
    else:
        # Redirect user back to question lists
        return redirect('/prototype/')

@user_passes_test(lambda u: u.is_staff)
def prototype2(request, topic_id=None):
    # Record usage for stats purpose
    page = "question_management"
    # Never accessed this page before, or last access was more than 10 mins ago
    if 'user_usage_'+page not in request.session or datetime.now() > datetime.strptime(request.session['user_usage_'+page], "%a %b %d %H:%M:%S %Y") + timedelta(minutes=10):
        usage = UserUsage(user=request.user, page=page)
        usage.save()
        request.session['user_usage_'+page] = usage.datetime.strftime("%a %b %d %H:%M:%S %Y")
    # End usage recording

    # Init
    filtered_questions = None
    selected_topic = None

    # Obtain the list of topics
    topics = Topic.objects.all()
    all_tags = Tag.objects.all()

    # int the selected topic
    if topic_id:
        selected_topic = Topic.objects.all().get(id=int(topic_id))

    if topic_id:
        # Retrieve questions for this topic
        filtered_questions = Question.objects.all().filter(topic=topic_id)

        # Filter for difficulty if specified
        if request.GET.__contains__('difficulty'):
            difficulty = request.GET.get('difficulty')

            # Only filter if input is an int!
            try:
                difficulty = int(difficulty)
                filtered_questions = filtered_questions.filter(difficulty=difficulty)
            except exceptions.ValueError:
                pass

    return render(request, 'itemrtweb/manage.question.list.html', {'topics': topics, 'selected_topic': selected_topic, 'questions': filtered_questions, 'all_tags': all_tags})

@user_passes_test(lambda u: u.is_staff)
def prototype2a(request):
    # Init
    filtered_questions = Question.objects.all()

    # Obtain the list of topics
    topics = Topic.objects.all()
    all_tags = Tag.objects.all()

    # Filter by tags given from input
    tags = request.GET.getlist("tags")

    print >> sys.stderr, tags

    if tags:
        for tag in tags:
            print >> sys.stderr, tag
            filtered_questions = filtered_questions.filter(tags__name=tag)
    else:
        filtered_questions = None

    return render(request, 'itemrtweb/manage.question.list.html', {'topics': topics, 'questions': filtered_questions, 'tags': tags, 'all_tags': all_tags})

@user_passes_test(lambda u: u.is_staff)
def preview(request, question_id=None):
    # Init
    selected_question = None

    # Objectify the selected question
    if question_id:
        selected_question = Question.objects.all().get(id=int(question_id))
        # Get correct answer
        selected_question.answer = selected_question.answers.all()[0]

    # Check if question exists otherwise redirect to question list
    if selected_question:
        return render(request, 'itemrtweb/manage.question.preview.html', {'question': selected_question})
    else:
        # 404 if question was not found
        raise Http404

@user_passes_test(lambda u: u.is_staff)
def testquestion(request, question_id=None):


    if question_id is not None:
        # Get question (or nothing) from orm
        question = Question.objects.all().get(id=question_id)

        if 'answer' in request.POST and request.POST['answer']:
            response = request.POST['answer']
            response = response.replace(' ', '').replace('\\n', '').replace('\\r', '').replace('\\t', '')

            # Get actual answer in string
            answer_text = question.choices[question.answers.all()[0].content.lower()]
            answer_text = answer_text.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')

            print sys.stderr, answer_text

            if re.match('^'+answer_text+'$', response):
                return HttpResponse("Answer is Correct")
            else:
                return HttpResponse("Answer do not Match\nInput: "+ response+ "\nActual: "+ answer_text)
        # Otherwise no answer just return nothing happened!
        else:
            return HttpResponse("Empty Field!")
    raise Http404
