# -*- coding: utf-8 -*-
from django import forms
from DBManagement.models import *
from qna.models import *
from django.core.exceptions import ValidationError


class DocumentForm(forms.ModelForm):
	docfile = forms.FileField(label='Select a file',help_text='max. 42 megabytes',required=False)
	title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder' : 'Title'}),required = True)
	content = forms.CharField(widget=forms.Textarea(attrs={'id': 'editor1'}),required = True)
	#hidden
	def __init__(self, *args, **kwargs):
		super(DocumentForm, self).__init__(*args, **kwargs)
		self.fields.insert(0, 'topic', forms.ModelChoiceField(queryset=Topic.objects.filter(block__subject=self.initial['subj_id_pass'])))
	class Meta:
		model = Ask
		exclude = ('view','subject','author','created','voteUp','voteDown')