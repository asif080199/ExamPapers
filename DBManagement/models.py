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
		return str(self.title)

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


class Paper(models.Model):
	id = models.CharField(max_length=64, primary_key=True, null=False)
	year = models.TextField('year', null=True)
	month = models.TextField('month', null=True)
	number = models.IntegerField('number', null=True)
	subject = models.ForeignKey(Subject, null=False)

	def __str__(self):
		return str(self.id)


class Question(models.Model):
	id = models.CharField(max_length=64, primary_key=True, null=False)
	paper = models.ForeignKey(Paper, null=True)
	question_no = models.SmallIntegerField('question_no', max_length=6, null=True)
	content = models.TextField('content', null=False)
	type = models.TextField('type', null=True)
	topic = models.ForeignKey(Topic, null=True)
	subtopic = models.ForeignKey(Subtopic, null=True)
	marks = models.IntegerField('marks', max_length=2, null=True)
	source = models.TextField('source', null=True)
	difficulty = models.IntegerField('difficulty', max_length=2, null=True)
	created_at = models.DateTimeField(auto_now=True)
	title = models.CharField(max_length=200, null=True)
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




class TagDefinition(models.Model):
	id = models.AutoField('id', primary_key=True, null=False)
	title = models.TextField('content', null=True)
	type = models.TextField('content', null=True)
	topic = models.ForeignKey(Topic, null=True) 
	content = models.TextField('content', null=True)
	
	def __str__(self):
		return str(self.id)

class  Tag(models.Model):
	id = models.AutoField('id', primary_key=True, null=False)
	question = models.ForeignKey(Question, null=True) 
	tagdefinition = models.ForeignKey(TagDefinition, null=True)

"""Index Formula Search"""
class Formula(models.Model):
	index = models.AutoField('index ID', primary_key=True)
	question = models.ForeignKey(Question)
	formula = models.CharField(max_length=1024, null=False, blank=True)
	vector = models.CharField(max_length=1024, null=False, blank=True)
	semantic = models.CharField(max_length=1024, null=False, blank=True)
	
	def __str__(self):
		return str(self.formula)
		
"""Paper test and CAT"""
class Assessment(models.Model):
    "Assessment model to represent different assessment engines"

    PRACTICE = 'P'
    TEST = 'T'
    ASSESSMENT_MODE_CHOICES = (
        (PRACTICE, 'Practice'),
        (TEST, 'Test'),
    )

    name        = models.CharField(max_length=30)
    type        = models.CharField(max_length=1, choices=ASSESSMENT_MODE_CHOICES)
    active      = models.BooleanField()
    engine      = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


# New in version 20131208
class Test(models.Model):
    "Test model for storage of each test paper generated"
    STATE_CHOICES = (
        (False, 'Draft'),
        (True, 'Active'),
    )

    id          = models.CharField(max_length=6, primary_key=True) #Unique 6 char alphanumeric ID
    generated   = models.DateTimeField(auto_now=True)
    questions   = models.ManyToManyField(Question, through='TestQuestion')
    assessment  = models.ForeignKey(Assessment)
    state       = models.BooleanField(choices=STATE_CHOICES, default=False)

    def _get_score(self):
        "Gets the score of the completed test"
        question = self.questions.all().reverse()[0] # Get last question

        # Should we filter for users?
        test_response = TestResponse.objects.filter(test=self).filter(question=question)[0]

        return test_response.ability

    score     = property(_get_score)

# New in version 20131208
class TestQuestion(models.Model):
    "TestQuestion model is an intermediary model between Test qnd Question models"
    question    = models.ForeignKey(Question)
    test        = models.ForeignKey(Test)

