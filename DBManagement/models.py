from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.timesince import timesince

class Education_Level(models.Model):
	id = models.IntegerField(primary_key=True, null=False)
	title = models.CharField(max_length=64, null=True)
	description = models.CharField(max_length=1000, null=True)

	def __str__(self):
		return str(self.title)

class Subject(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	title = models.TextField('title', null=True)
	edu_level = models.ForeignKey(Education_Level, null=True)
	description = models.TextField('description', null=True)
	def __str__(self):
		return str(self.id)

class Block(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	title = models.TextField('title', null=True)
	subject = models.ForeignKey(Subject, null=True)
	def __str__(self):
		return str(self.title)


class Topic(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	block = models.ForeignKey(Block, null=True)
	title = models.TextField('title', null=True)

	def __str__(self):
		return str(self.title)


class Subtopic(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	topic = models.ForeignKey(Topic, null=True)
	title = models.TextField('title', null=True)

	def __str__(self):
		return str(self.title)


class Paperset(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	title = models.TextField('title', null=True)
	subject = models.ForeignKey(Subject, null=False)

	def __str__(self):
		return str(self.title)


class Paper(models.Model):
	id = models.CharField(max_length=64, primary_key=True, null=False)
	year = models.TextField('year', null=True)
	month = models.TextField('month', null=True)
	number = models.IntegerField('number', null=True)
	subject = models.ForeignKey(Subject, null=False)
	paperset = models.ForeignKey(Paperset, null=False)

	def __str__(self):
		return str(self.id)


class Question(models.Model):
	id = models.CharField(max_length=64, primary_key=True, null=False)
	paper = models.ForeignKey(Paper, null=True)
	question_no = models.SmallIntegerField('question_no', max_length=6, null=True)
	content = models.TextField('content', null=False)
	topic = models.ForeignKey(Topic, null=True)
	subtopic = models.ForeignKey(Subtopic, null=True)
	marks = models.IntegerField('marks', max_length=2, null=True)
	source = models.TextField('source', null=False)
	difficulty = models.IntegerField('difficulty', max_length=2, null=True)
	def __str__(self):
		return str(self.id)


class Solution(models.Model):
	id = models.AutoField('id', primary_key=True, null=False)
	question = models.ForeignKey(Question, null=False)
	content = models.TextField('content', null=False)

	def __str__(self):
		return str(self.id)


class Image(models.Model):
	id = models.AutoField('id', primary_key=True, null=False)
	qa = models.TextField('qa', null=True)
	qa_id = models.ForeignKey(Question, null=False)
	imagepath = models.FileField(upload_to="/static/image/")

	def __str__(self):
		return str(self.id)


class AnswerType(models.Model):
	id = models.IntegerField('id', primary_key=True, null=False)
	description = models.TextField('description', null=False)

	def __str__(self):
		return str(self.id)

class Answer(models.Model):
	id = models.AutoField('id', primary_key=True, null=False)
	answertype = models.ForeignKey(AnswerType, null=False)
	question = models.ForeignKey(Question, null=False)
	part_no = models.CharField(max_length=3, null=False)
	content = models.TextField('content', null=True)
	switch = models.BooleanField(default=False, null=False)

	def __str__(self):
		return str(self.id)
