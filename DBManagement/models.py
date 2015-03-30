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

class Progress(models.Model):
	user = models.ForeignKey(User, null=False)
	question_id = models.ForeignKey(Question, null=False)
	created = models.DateTimeField(auto_now=True)
	score = models.IntegerField(null = True)
	
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
    #indexid = models.PositiveIntegerField(primary_key=True)
    indexid = models.AutoField('index ID', primary_key=True)
    question = models.ForeignKey(Question)
    formula = models.CharField(max_length=1024, null=True, blank=True)
    status = models.BooleanField(default=True)
    inorder_term = models.CharField(max_length=1024, null=True, blank=True)
    sorted_term = models.CharField(max_length=1024, null=True, blank=True)
    structure_term = models.CharField(max_length=1024, null=True, blank=True)
    constant_term = models.CharField(max_length=1024, null=True, blank=True)
    variable_term = models.CharField(max_length=1024, null=True, blank=True)
            
class Formula_index(models.Model):
    indexkey = models.CharField('index key', primary_key=True, max_length=64)
    docsids = models.CharField(max_length=9192, null=True, blank=True)
    df = models.PositiveIntegerField('frequency', default=1, blank=True)

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

# New in version 20131023
class Response(models.Model):
    "Response model to store user responses"
    user        = models.ForeignKey(User)
    question    = models.ForeignKey(Question)
    response    = models.TextField(max_length=100)
    date        = models.DateTimeField(auto_now=True)
    duration    = models.IntegerField(blank=True, null=True) # In seconds
    correctness = models.DecimalField(max_digits=3, decimal_places=2, null=True) # Percent correct in dec (0-1)
    criterion   = models.DecimalField(max_digits=3, decimal_places=1) # Max marks for random practice/test, diff for CAT
    ability     = models.DecimalField(max_digits=5, decimal_places=2, null=True) # Current ability score for practices
    assessment  = models.ForeignKey(Assessment)

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
class TestResponse(Response):
    "TestResponse model for storage of test responses, this links back to the test itself"
    test        = models.ForeignKey(Test, related_name='responses')

    def __unicode__(self):
        return 'TestResponse ' + str(self.id)

class Meta(models.Model):
    "Meta model to keep the list of meta tags used"
    metatag     = models.CharField(max_length=30, primary_key=True)

    def __unicode__(self):
        return self.metatag
# Many to Many intermediary models

# New in version 20131023
class QuestionMeta(models.Model):
    "QuestionMeta model is an intermediary model between Question and Meta models"
    question    = models.ForeignKey(Question)
    meta        = models.ForeignKey(Meta)
    content     = models.CharField(max_length=50)

# New in version 20131208
class TestQuestion(models.Model):
    "TestQuestion model is an intermediary model between Test qnd Question models"
    question    = models.ForeignKey(Question)
    test        = models.ForeignKey(Test)

# New in version 20140205
class UserProfile(models.Model):
    user        = models.OneToOneField(User)

    debug       = models.BooleanField()

    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    post_save.connect(create_user_profile, sender=User)

# New in version 20140215
class UserUsage(models.Model):
    user        = models.ForeignKey(User)
    datetime    = models.DateTimeField(auto_now=True)
    page        = models.CharField(max_length=50)

    class Meta:
        ordering = ['-datetime']

    def __unicode__(self):
        return self.user.get_full_name() + ' last accessed ' + self.page + ' ' + timesince(self.datetime) + ' ago'
	
class UserProfile(models.Model):
    user        = models.OneToOneField(User)

    debug       = models.BooleanField()

    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    post_save.connect(create_user_profile, sender=User)

