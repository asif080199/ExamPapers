import forms
from django.shortcuts import render, render_to_response, redirect
from DBManagement.models import *
from qna.models import *
from haystack.query import SearchQuerySet
import datetime

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

from datetime import datetime, timedelta

import math, re, random, sys

from datetime import timedelta
from django.utils import timezone

from ExamPapers.logic.common import *
from ExamPapers.logic.question_processing import *

"""
-------------------------------------
Account
-------------------------------------
"""

def account_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user w/db
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                # Success, check permissions (user/admin)
                if user.is_staff:
                    # Staff redirected to control panel
                    return redirect('/3/')
                else:
                    # User redirected to practice homepage
                    return redirect('/3/')
            else:
                if user.last_login == user.date_joined:
                    # Not activated
                    return render(request, 'account/auth.login.html', {'error': 'inactive'})
                else:
                    # User account has been disabled
                    return render_to_response('account/auth.login.html', {'error': 'disabled'}, context_instance=RequestContext(request))
        else:
            # User account not found or password is incorrect
            return render_to_response('account/auth.login.html', {'error': 'incorrect'}, context_instance=RequestContext(request))
    else:
        if request.user.is_authenticated():
            if 'next' not in request.GET:
                # Why are you visiting my sign in page again?
                return redirect('/')
            else:
                return render(request, 'account/auth.login.html', {'error':'permission'})
        else:
            return render(request, 'account/auth.login.html')

def account_logout(request):
    # Logout for user
    logout(request)

    return render_to_response('account/auth.logout.html', {}, context_instance=RequestContext(request))

def account_register(request):
    if request.method == 'POST':
        form = forms.RegistrationForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Process account registration
            user = User.objects.create_user(username=form.cleaned_data['email'], email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            user.first_name=form.cleaned_data['first_name']
            user.last_name=form.cleaned_data['last_name']
            user.is_active = False
            user.save()

            # Generate a activation key using existing salt for pwd
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            activation_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, activation_key = activation_key.split('$', 3)
            activation_key = activation_key[:-1]
            # Alternative char for + and /
            activation_key = activation_key.replace('+','-').replace('/','_')

            title = 'Account Activation'
            content = render_to_string('email/register.email', {'first_name': user.first_name, 'last_name': user.last_name, 'is_secure': request.is_secure(), 'host': request.get_host(), 'activation_key': activation_key, 'sender': settings.PROJECT_NAME})

            send_mail(title, content, settings.PROJECT_NAME + ' <' + settings.EMAIL_HOST_USER + '>', [user.email])

            return render(request, 'account/account.register.success.html')
    else:
        # Display new form for user to fill in
        form = forms.RegistrationForm()

    return render(request, 'account/account.register.form.html', {'form': form})

def account_activate(request):
    # Already activated
    if request.user.is_authenticated():
        return render(request, 'account/account.activate.success.html', {'error': 'activated'})

    if request.method == 'GET':
        # Get activation details
        activation_key = request.GET.get('key')

        # No activation key, throw to login page
        if activation_key is None:
            return redirect('/accounts/login/')

        # Keep activation key in session awaiting login
        request.session['activation_key'] = activation_key

        form = forms.ActivationForm()
    else:
        # Attempt to activate user using given user, password and key
        form = forms.ActivationForm(request.POST)
        if form.is_valid():
            # Try logging in
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])

            if user is None:
                form.activation_error = 'incorrect'
            else:
                # Already active? error!
                if user.is_active:
                    form.activation_error = 'expired'
                else:
                    # Match activation key
                    algorithm, iterations, salt, hashed = user.password.split('$', 3)
                    activation_key = make_password(user.email, salt, algorithm)
                    algorithm, iterations, salt, activation_key = activation_key.split('$', 3)
                    activation_key = activation_key[:-1]
                    # Alternative char for + and /
                    activation_key = activation_key.replace('+','-').replace('/','_')

                    form.key1 = request.session['activation_key']
                    form.key2 = activation_key

                    # Match keys
                    if activation_key == request.session['activation_key']:
                        # Activated, login and proceed
                        user.is_active = True
                        user.save()
                        login(request, user)

                        return render(request, 'account/account.activate.success.html')
                    else:
                        # Key expired!
                        form.activation_error = 'expired'

    return render(request, 'account/account.activate.form.html', {'form': form})

def account_forgot(request):
    if request.method == 'POST':
        form = forms.PasswordForgetForm(request.POST) # Bind to user submitted form
        if form.is_valid():
            # Retrieve user from db
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
            except User.DoesNotExist:
                return redirect('/accounts/forgot/?error=nouser')

            # Generate a reset key using existing salt for pwd
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            reset_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, reset_key = reset_key.split('$', 3)
            reset_key = reset_key[:-1]
            # Alternative char for + and /
            reset_key = reset_key.replace('+','-').replace('/','_')

            title = 'Password Reset'
            content = render_to_string('email/passwordreset.email', {'first_name': user.first_name, 'last_name': user.last_name, 'host': request.get_host(), 'reset_key': reset_key, 'sender': settings.PROJECT_NAME, 'email': user.email})

            send_mail(title, content, settings.PROJECT_NAME + ' <' + settings.EMAIL_HOST_USER + '>', [user.email])

            return render(request, 'account/account.forgot.success.html')
    else:
        # Display new form for user to fill in
        form = forms.PasswordForgetForm()

    return render(request, 'account/account.forget.form.html', {'form': form})

def account_reset(request):
    if request.user.is_authenticated():
        pass
    else:
        if request.method == 'GET':
            # TODO: Error messages if key is not valid or email is wrong

            # Reset password for user who has forgotten it
            # Get user from request data
            user_email = request.GET.get('user')

            # Retrieve user from db
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                return redirect('/accounts/forgot/?error=nouser')

            # Get reset key from request data
            reset_key_input = request.GET.get('key')

            # No reset key, throw to login page
            if reset_key_input is None:
                return redirect('/accounts/forgot/?error=nokey')

            # Match reset key
            algorithm, iterations, salt, hashed = user.password.split('$', 3)
            reset_key = make_password(user.email, salt, algorithm)
            algorithm, iterations, salt, reset_key = reset_key.split('$', 3)
            reset_key = reset_key[:-1]
            # Alternative char for + and /
            reset_key = reset_key.replace('+','-').replace('/','_')

            # Match keys
            if reset_key == reset_key_input:
                # Reset keys match, render page for user to reset
                # Store reset email in session
                request.session['reset_email'] = user_email

                form = forms.PasswordResetForm(initial={'email': user_email})
            else:
                # Key expired!
                return redirect('/accounts/forgot/?error=keymismatch')
        elif request.method == 'POST':
            form = forms.PasswordResetForm(request.POST)
            if form.is_valid():
                # Perform real resetting of account
                # Check if emails from form and session matches
                if form.cleaned_data['email'] == request.session['reset_email']:
                    # Get user
                    try:
                        user = User.objects.get(email=request.session['reset_email'])
                    except User.DoesNotExist:
                        return redirect('/accounts/forgot/?error=nouser')

                    # Update password of user in system
                    user.set_password(form.cleaned_data['password'])
                    user.save()

                    # Success, login user and display success page
                    user = authenticate(username=user.username, password=form.cleaned_data['password'])
                    login(request, user)

                    return render(request, 'account/account.reset.success.html')
                else:
                    return redirect('/accounts/forgot/?error=email')

        return render(request, 'account/account.reset.form.html', {'form': form})

@login_required		
def profile(request):
	param = {}
	param['cur'] = Subject.objects.get(id = 1)
	param['level'] = Subject.objects.all()
	
	#get subscription - TODO
	subjects = Subject.objects.all()
	
	param['subjects'] = subjects
	return render(request,'account/account.profile.html',param)



@login_required	
def level(request,lid):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = Subject.objects.get(id = lid)
	return render(request,'level.html', param)
	
@login_required	
def home(request):
	param = {}
	param['level'] = Subject.objects.all()
	param['cur'] = ''
	return render(request,'index.html', param)

"""
-------------------------------------
Study
-------------------------------------
"""		
@login_required		
def study(request,subj_id,tp):
	param={}
	tp = -1
	if request.GET.get("tp") != None:
		tp = int(request.GET.get('tp'))	
	param={}
	blocks = Block.objects.filter(subject_id = subj_id)
	for b in blocks:
		b.topics = Topic.objects.filter(block = b)
	param['blocks'] = blocks
	param['tp'] = tp
	if tp!=-1:
		param['content'] = ["Content1","Content2","Content3"] #to be replaced by file content
		
	param.update(current(subj_id))
	return render(request,'study.html', param)

	
"""
-------------------------------------
Search
-------------------------------------
"""	
@login_required			
def search(request,subj_id,type,tp,searchtext):
	total = 0
	param={}
	input = ""
	tp = -1
	if request.GET.get("searchtext") != None:
		input = request.GET.get("searchtext")
	if request.GET.get("type") != None:
		type = request.GET.get("type")		
	if request.GET.get("tp") != None:
		tp = request.GET.get("tp")	
	
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
			question.stars = star(int(question.marks*5/16.0)+1)
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
	#Do paging 
	paginator = Paginator(questions, 10)
		
	try: page = int(request.GET.get("page", '1'))
	except ValueError: page = 1

	try:
		questions = paginator.page(page)
	except (InvalidPage, EmptyPage):
		questions = paginator.page(paginator.num_pages)
			
	param['total'] = total
	param['type'] = type
	param['blocks'] = blocks
	param['questions'] = questions
	param['tp'] = int(tp)
	param['searchtext'] = input
	return render(request,'search.html',param)

@login_required		
def viewquestion(request,lid,qid):
	param = {}
	#todo
	param['cur'] = Subject.objects.get(id = lid)
	param['level'] = Subject.objects.all()
	
	param['question'] = getViewQuestion(qid)
	return render(request,'viewquestion.html',param)
	
def test(request,subj_id):
	param = {}
	#update cur and subj	
	param.update(current(subj_id))
	return render(request,'test.html',param)

	
"""
-------------------------------------
Statistics
-------------------------------------
"""
def statistics(request,subj_id,type):
	#init
	param = {}
	param.update(current(subj_id))
	
	#get background info
	if request.GET.get("type") != None:
		type = request.GET.get("type")
	param['type'] = type 
	
	
	#count
	if type == "overview":
		param['total'] = 0
	blocks = Block.objects.filter(subject__id = subj_id)
	if type == "practice":
		for b in blocks:
			b.topics = Topic.objects.filter(block__id = b.id)
			for t in b.topics:
				t.a = Question.objects.filter(topic_id = t.id).filter(difficulty = 0).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 1).count()+ Question.objects.filter(topic_id = t.id).filter(difficulty = 2).count()
				t.b = Question.objects.filter(topic_id = t.id).filter(difficulty = 2).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 3).count()
				t.c = Question.objects.filter(topic_id = t.id).filter(difficulty = 4).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 5).count()
				t.d = Question.objects.filter(topic_id = t.id).filter(difficulty = 6).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 7).count()
				t.e = Question.objects.filter(topic_id = t.id).filter(difficulty = 8).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 9).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 10).count()
		a = Question.objects.filter(difficulty = 0).count() + Question.objects.filter(topic_id = t.id).filter(difficulty = 1).count()+ Question.objects.filter(difficulty = 2).count()
		b = Question.objects.filter(difficulty = 2).count() + Question.objects.filter(difficulty = 3).count()
		c = Question.objects.filter(difficulty = 4).count() + Question.objects.filter(difficulty = 5).count()
		d = Question.objects.filter(difficulty = 6).count() + Question.objects.filter(difficulty = 7).count()
		e = Question.objects.filter(difficulty = 8).count() + Question.objects.filter(difficulty = 9).count() + Question.objects.filter(difficulty = 10).count()
		param['total'] = [a,b,c,d,e]
	if type == "qna":
		today = datetime.today()
		for b in blocks:
			b.topics = Topic.objects.filter(block__id = b.id)
			for t in b.topics:
				t.day = Ask.objects.filter(topic_id = t.id).filter(created__day = today.day).count()
				t.month = Ask.objects.filter(topic_id = t.id).filter(created__month = today.month).count()
				t.year = Ask.objects.filter(topic_id = t.id).filter(created__year = today.year).count()
				t.all = Ask.objects.filter(topic_id = t.id).count()
		a = Ask.objects.filter(created__day = today.day).count()
		b = Ask.objects.filter(created__month = today.month).count()
		c = Ask.objects.filter(created__year = today.year).count()
		d = Ask.objects.count()
		param['total'] = [a,b,c,d]
	
	param['blocks']= blocks
	return render(request,'statistics.html',param)
	
	
	

	
def star(rate):
	stars = []
	for s in range(rate):
		stars.append("<i class='glyphicon glyphicon-star '></i>")
	#for s in range(5-rate):
	#	stars.append("<i class='glyphicon glyphicon-star-empty'></i>")
	return stars