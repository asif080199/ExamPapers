# -*- coding: utf-8 -*-
from django import forms
from DBManagement.models import *
from django.core.exceptions import ValidationError


class DocumentForm(forms.ModelForm):
	
	#id = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Question ID'}),required = True)
	question_no = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Question number'}),required = True)
	content = forms.CharField(widget=forms.Textarea(),required = True)
	marks = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Marks'}),required = True)
	difficulty = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Difficulty'}),required = True)
	source = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Source'}),required = True)
	#hidden
	def __init__(self, *args, **kwargs):
		super(DocumentForm, self).__init__(*args, **kwargs)
		self.fields.insert(1, 'subtopic', forms.ModelChoiceField(queryset=Subtopic.objects.filter(topic__block__subject=self.initial['subj_id_pass'])))
		self.fields.insert(0, 'topic', forms.ModelChoiceField(queryset=Topic.objects.filter(block__subject=self.initial['subj_id_pass'])))
		self.fields.insert(2, 'paper', forms.ModelChoiceField(queryset=Paper.objects.filter(subject=self.initial['subj_id_pass'])))
	class Meta:
		model = Question
		exclude = ('id')
		