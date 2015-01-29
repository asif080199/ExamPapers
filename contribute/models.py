from django.db import models
from django.contrib.auth.models import User
from DBManagement.models import *
import os 
from django.forms import ModelForm

def get_image_path(instance, filename):
    return os.path.join('resource/static/contribute', str(instance.questionC.id), filename)
	
class QuestionC(models.Model):
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=500, null=True)
	content = models.CharField(max_length=1000, null=True)
	created = models.DateTimeField(null=False)
	author = models.ForeignKey(User, null=True)
	topic = models.ForeignKey(Topic, null=False)
	subtopic = models.ForeignKey(Subtopic, null=False)
	solution = models.CharField(max_length=1000, null=True)
	subject = models.ForeignKey(Subject, null=False)
	def __str__(self):
		return str(self.title)

		
class FileC(models.Model):
	docfile = models.ImageField(upload_to=get_image_path)
	questionC = models.ForeignKey(QuestionC, null=True)
	
	def delete(self, *args, **kwargs):
		self.image.delete(True)
		super(FileC, self).delete(*args, **kwargs)
