from django.contrib import admin
import models


class DefaultAdmin(admin.ModelAdmin):  
    pass


class PaperAdmin(admin.ModelAdmin):
    list_display=('id','year','month','number')


class ImageAdmin(admin.ModelAdmin):
	list_display=('id','imagepath')


class QuestionAdmin(admin.ModelAdmin):
    list_display=('id','content')
    list_filter=('topic','paper')


class AnswerAdmin(admin.ModelAdmin):
    list_display=('id','content')
    list_filter=('question',)


admin.site.register(models.Education_Level, DefaultAdmin)
admin.site.register(models.Subject, DefaultAdmin)
admin.site.register(models.Topic, DefaultAdmin)
admin.site.register(models.Subtopic, DefaultAdmin)
admin.site.register(models.Paperset, DefaultAdmin)
admin.site.register(models.Paper, PaperAdmin)
admin.site.register(models.Question, QuestionAdmin)
admin.site.register(models.Solution, AnswerAdmin)
admin.site.register(models.Image, ImageAdmin)
admin.site.register(models.AnswerType, DefaultAdmin)
admin.site.register(models.Answer, DefaultAdmin)
