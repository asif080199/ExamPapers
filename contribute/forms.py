# -*- coding: utf-8 -*-
from django import forms
from DBManagement.models import *
from contribute.models import *
from django.core.exceptions import ValidationError


class ContributeForm(forms.ModelForm):
	docfile = forms.FileField(label='Select a file',help_text='max. 42 megabytes',required=False)
	title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Title'}),required = True)
	content = forms.CharField(widget=forms.Textarea(attrs={'onKeyUp':  "input()" , 'id' : 'q_content' , 'class' : 'form-control'}),required = True)
	solution = forms.CharField(widget=forms.Textarea(attrs={'onKeyUp':  "input2()" , 'id' : 'q_solution' , 'class' : 'form-control'}),required = True)
	source = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Source'}),required = True)
	#hidden
	def __init__(self, *args, **kwargs):
		super(ContributeForm, self).__init__(*args, **kwargs)
		self.fields.insert(0, 'subject', forms.ModelChoiceField(queryset=Subject.objects.all()))
		self.fields.insert(1, 'topic', forms.ModelChoiceField(queryset=Topic.objects.all()))
		self.fields.insert(2, 'subtopic', forms.ModelChoiceField(queryset=Subtopic.objects.all()))
	class Meta:
		model = QuestionC
		exclude = ('author','created')