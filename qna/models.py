from django.db import models
from django.contrib.auth.models import User
from DBManagement.models import *
import os 
from django.forms import ModelForm

def get_image_path(instance, filename):
    return os.path.join('resource/static/documents', str(instance.ask.id), filename)
	
class Ask(models.Model):
	id = models.AutoField(primary_key=True)
	title = models.CharField(max_length=500, null=True)
	content = models.CharField(max_length=1000, null=True)
	created = models.DateTimeField(null=False)
	modified = models.DateTimeField(auto_now=True)
	author = models.ForeignKey(User, null=True)
	view = models.IntegerField(default = 0)
	topic = models.ForeignKey(Topic, null=False)
	subject = models.ForeignKey(Subject, null=False)
	voteUp = models.IntegerField(default = 0)
	voteDown = models.IntegerField(default = 0)
	def __str__(self):
		return str(self.title)

class Askfile(models.Model):
	docfile = models.ImageField(upload_to=get_image_path)
	ask = models.ForeignKey(Ask, null=True)
	
	def delete(self, *args, **kwargs):
		self.image.delete(True)
		super(Askfile, self).delete(*args, **kwargs)
