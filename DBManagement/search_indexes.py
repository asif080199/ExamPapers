from haystack import indexes
from .models import Question, Image, Answer, Subject, Topic, Subtopic
from django.utils import six

class questionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    content = indexes.CharField(model_attr='content')
    paper = indexes.CharField(model_attr='paper')
    question_no = indexes.IntegerField(model_attr='question_no')
    topic = indexes.CharField(model_attr='topic')
    topic_id = indexes.IntegerField(model_attr='topic_id')
    subject = indexes.CharField(model_attr='topic__block__subject')
    subject_id = indexes.IntegerField(model_attr='topic__block__subject_id')
    block = indexes.CharField(model_attr='topic__block')
    subtopic = indexes.CharField(model_attr='subtopic')
    marks = indexes.IntegerField(model_attr='marks')
    difficulty = indexes.IntegerField(model_attr='difficulty')
    question_id = indexes.CharField(model_attr='id')
	
    def get_model(self):
		return Question

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
		