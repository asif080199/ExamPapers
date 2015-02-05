from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponseRedirect,HttpResponse
from django.template import RequestContext
from django.core.paginator import Paginator
from ExamPapers.DBManagement.models import *
import datetime
from ExamPapers.logic.common import *
from ExamPapers.logic.question_processing import *
from logic.common import *
from ExamPapers.fsearch.views import index
from django.db.models import Q

#set Additional Maths folder
add_math_img='/static/image/'

#Solution format
sol_format={'v':'Values','r':'Ratio','c':'Coordinates','m':'Matrix','i':'Inequality','e':'Equation','n':'Not_Equal','p':'Proving','d':'Diagram'}

#Add Maths question page settings
addMaths_q_per_page=10


# Question Admin
def AddMaths_Admin(request,subj_id): #home	
	param={}
	param['papers']=list(Paper.objects.filter(subject_id=subj_id,number__gt=0).only('id','year','month','number').order_by('id').values())	
	
	topics=list(Topic.objects.filter(block__subject_id=subj_id).order_by('id').values())
	param['topics']=topics
	questions = Question.objects.filter(topic__block__subject_id = subj_id)

		
	for q in questions:
		q.noTag = Tag.objects.filter(question_id = q.id).count()
		solution = Solution.objects.filter(question_id = q.id).count()
		q.solution = "Not available"
		if solution >0:
			q.solution = "Available"
		q.display = q.content[:100]	
		
	param['questions'] = questions
	param.update(current(subj_id))
	return render_to_response('control/control.add_math_admin.html',param, context_instance=RequestContext(request))

	
	
	
	
	
#list questions to modify
def AddMaths_Admin_ModifyQuestion(request,list_type,subj_id,page_no):	#math_admin_list
    
	param={}
	
	#query paper and subtopics for display in each question
	paperlist=list(Paper.objects.filter(subject_id=subj_id,number__gt=0).only('id','year','month','number').order_by('id').values())
	seltopic=list(Topic.objects.filter(block__subject_id=subj_id).only('id','title').order_by('id').values())
	stopic=[]
	for sel_topic in seltopic:
		stopic[0:0]=list(Subtopic.objects.filter(topic_id=sel_topic['id']).only('id','title').order_by('id').values())
	
	#get id of type/topic/sol_type
	list_id = request.GET.get("list_id")
	#query questions based on paper, topic,all or solution type
	sel=[]
	if list_type=='paper':
		sel=list(Question.objects.filter(paper_id=list_id).only('id','paper_id_id','content','subtopic_id_id','type','topic_id_id').order_by('id').values())
		page_title="Paper: " + Subject.objects.get(id=Paper.objects.get(id=list_id).subject_id).title + ' ' + Paper.objects.get(id=list_id).year + ' ' +  Paper.objects.get(id=list_id).month + ' Paper ' + str(Paper.objects.get(id=list_id).number)
	elif list_type=='topic':		
		sel=list(Question.objects.filter(topic_id=list_id).only('id','paper_id_id','content','subtopic_id_id','type', 'topic_id_id').order_by('id').values())
		page_title="Topic: " + Topic.objects.get(id=list_id).title
		
	elif list_type=='tag':
		tag_list=list(tag.objects.filter(tag=list_id).order_by('question_id').values('question_id'))
		qid_set=[]
		for tagitem in tag_list:
			qid_set.append(tagitem['question_id'])
		sel = list(Question.objects.filter(pk__in=qid_set).only('id','paper_id_id','content','subtopic_id_id','type','topic_id_id').order_by('id').values())
		page_title='Tags: ' + list_id
	else:		
		for sel_topic in stopic:
			sel[0:0]=list(Question.objects.filter(subtopic_id=sel_topic['id']).only('id','paper_id_id','content','subtopic_id_id','type', 'topic_id_id').order_by('id').values())
		#if is question type and not all	
		if list_type=='question_type':
			temp=[]			
			for q in sel:
				if ((';'+q['type']).find(';'+list_id)>= 0):
					temp.append(q)
				elif (('|'+q['type']).find('|'+list_id)>= 0):
					temp.append(q)
			sel=temp
			for k in sol_format.keys():
				if (k==list_id):
					page_title=Subject.objects.get(id=sub_id).title + ' - ' + sol_format[k]	
		
	no_of_qn=len(sel)
	
	#select questions for page
	page_items=[]
	for i in range(0,addMaths_q_per_page):
		if( (i + addMaths_q_per_page * (int(page_no) - 1))<no_of_qn):
			page_items.append(sel[i + addMaths_q_per_page * (int(page_no) - 1)])
	
	#For each question in page, insert required values
	for i in range(0,len(page_items)):
		id = page_items[i]['id']
		page_items[i]['noTag'] = (Tag.objects.filter(question_id = id).count())
		answer = Solution.objects.filter(question_id = id).count()
		page_items[i]['solution'] = "Not available"
		if answer >0:
			page_items[i]['solution'] = "Available"
		page_items[i]['display']=page_items[i]['content'][:100]#[:100]+'\\]'
		page_items[i]['paper']='_'
		page_items[i]['subtopic']='_'
		page_items[i]['topic']='_'
		page_items[i]['sol_type']=''
		for p in paperlist:
			if(p['id']==page_items[i]['paper_id']):
				page_items[i]['paper']=p['month']+' '+p['year']+' Paper'+str(p['number'])
				break
		for temp in stopic:
			if(temp['id']==page_items[i]['subtopic_id']):
				page_items[i]['subtopic']=temp['title']
				break
		for temp1 in seltopic:
			if(temp1['id']==page_items[i]['topic_id']):
				page_items[i]['topic']=temp1['title']
				break	
		
		#for k in sol_format.keys():
		#	if ((';'+page_items[i]['type']).find(';'+k)>= 0):
		#		page_items[i]['sol_type']=page_items[i]['sol_type']+sol_format[k]+', '
		#	elif (('|'+page_items[i]['type']).find('|'+k)>= 0):
		#		page_items[i]['sol_type']=page_items[i]['sol_type']+sol_format[k]+', '
				
	#create links of pages
	no_pages=no_of_qn/addMaths_q_per_page
	if((no_of_qn % addMaths_q_per_page)!=0):
		no_pages=no_pages+1
	page_links=[]
	for i in range(1,no_pages+1):
		page_links.append(i)
		
	param['questions']=page_items
	param['page_links']=page_links
	param['num_q']=no_of_qn
	param['list_id']=list_id
	param['list_type']=list_type
	param['page_no']=int(page_no)
	param['page_title']=  page_title
	
	param['subj_id']=subj_id
	    
	#for links
	param['subject']=Subject.objects.all()
	param.update(current(subj_id))
	return render_to_response('control/add_math_admin_qList.html',param, context_instance=RequestContext(request))



#delete question
def AddMaths_qDelete(request,subj_id): #no page return
	q_id=request.POST.get('d_q_id','')
	print q_id
	print "___________"
	#delete question
	qn=Question.objects.get(id=q_id)
	qn.delete();
	
	#delete answer
	ans=Solution.objects.filter(question_id=q_id)
	ans.delete();
	param={}
	param.update(current(subj_id))
	#delete relevant tags
	tags=Tag.objects.filter(question_id=q_id)
	tags.delete();
	
	return add_math_question(request,list_type,subj_id,page_no)
	


#menu page to select topic or paper
def AMaths_Menu(request,subj_id):
	param={}
	
	#query list of papers
	param['papers']=list(paper.objects.filter(subject_id=subj_id,number__gt=0,year__lt=2008).only('id','year','month','number').order_by('id').values())	
	
	# query list of topics
	topics=list(topic.objects.filter(subject_id=subj_id).order_by('id').values())
	#query list of tags
	tags=list(tag_definitions.objects.filter(id__gt=290).order_by('id').values())
	param['topics']=topics
	param['tags']=tags
	#for links
	param['subject']=subject.objects.all()
	param['cur_subj']=subject.objects.get(id=subj_id)
	
	return render_to_response('control/add_math.html',param)

#method to process question into display format
def process_question(q):
	#query for all images for this question
	img_sel=list(Image.objects.filter(qa_id=q['id'],qa='Question').only('id','imagepath').order_by('id').values())
	
	#split the content of question using ';' as separator
	token=q['content'].split(';')	
	display=[]
	item={}
	img_iterator=0
	#for each question part
	for t in token:
		#if is not image, add as text
		if t.strip()!="img":
			item['type']=1
			item['value']=t.strip()
		else:
			#if image, substitude the image path
			item['type']=2
			if len(img_sel)>img_iterator:
				#add path to where image folder is
				item['value']=add_math_img + img_sel[img_iterator]['imagepath']
			else:
				item['value']='missing image'
			img_iterator=img_iterator+1
		#The processed part is added into a list representing the content
		display.append(item)
		item={}
	
	#The 'type' helps identify images (1 for text, 2 for image)
	#In cases where image is not found, 'missing image' text is used
	return display
	
#display the list of question for Paper or Topic selected
def add_math_question(request,list_type,subj_id,page_no):
    
	param={}
	
	#get id of paper or topic
	list_id = request.GET.get("list_id")
	topic_id = 0 #default
	paperset_id = 0 #default
	if (request.GET.get("topic_id") != None):
		topic_id = int(request.GET.get("topic_id"))
	if (request.GET.get("paperset_id") != None):
		paperset_id = int(request.GET.get("paperset_id"))
	
	#from the type (paper or topic) passed, query for questions
	sel=[]
	page_title=[] #for storing paper title / topic title
	
	if list_type=='paper': #view by paper	
		sel=list(Question.objects.select_related().filter(paper_id=list_id).only('id','content','question_no','marks').order_by('id').values())
		param['cur_subj']=Paper.objects.get(id=list_id).subject_id
		page_title=Subject.objects.get(id=subj_id).title + ' ' + Paper.objects.get(id=list_id).year + ' ' +  Paper.objects.get(id=list_id).month + ' Paper ' + str(Paper.objects.get(id=list_id).number)
	elif list_type=='topic': #view by topic
		if (paperset_id > 0): #optional of having paperset filtered
			paper_ids = paper.objects.filter(paperset_id=paperset_id)
			sel = list(Question.objects.filter(paper_id__in=paper_ids, topic_id=list_id).only('id','content','question_no','marks').order_by('id').values())
		else: #no paperset by default
			sel = list(Question.objects.filter(topic_id=list_id).only('id','content','question_no','marks').order_by('id').values())
		param['cur_subj']=Topic.objects.get(id=list_id).block.subject.id
		page_title=Subject.objects.get(id=subj_id).title + ' - ' + str(Topic.objects.get(id=list_id).title)
	elif list_type == 'tag': #view by tag
		#get questions
		qnlist=[]
		if (topic_id > 0): #topic filter
			qnlist = Question.objects.filter(topic_id=topic_id)
		elif (paperset_id > 0): #paperset filter
			paper_ids = Paper.objects.filter(paperset_id=paperset_id)
			qnlist = Question.objects.filter(paper_id__in=paper_ids)
		else: #clean, no filtering
			qnlist = question.objects.all()
		#further filter questions with tags
		tags = list_id.split('|')
		tag_list=list(Tag.objects.filter(tag__id__in=tags, question_id__in=qnlist).order_by('question_id').values('question_id').annotate(q_count=Count('question_id')).filter(q_count__gte=len(tags)))
		qid_set=[]
		for tagitem in tag_list:
			qid_set.append(tagitem['question_id'])
		#show questions
		sel = list(Question.objects.filter(pk__in=qid_set).only('id','content','question_no','marks').order_by('id').values())
		param['cur_subj'] = 1
		title=''
		#pack a list for description of formula and concept being used
		formula=[]
		concept=[]
		for t in tags:
			tag_def=TagDefinition.objects.get(id=t)
			title+= tag_def.title + ', '
			if tag_def.type == 'F':
				tag_def.content = process_tag(tag_def)
				formula.append(tag_def.content)
			elif tag_def.type == 'C':
				tag_def.content = process_tag(tag_def)
				concept.append(tag_def.content)
		title=title[0:len(title)-2]
		param['formula']=formula
		param['concept']=concept
		page_title='Tags (' + title + ')'
	elif list_type == 'single': #view as single question
		sel=list(Question.objects.filter(id=list_id).only('id','content','question_no','marks').order_by('id').values())
		param['cur_subj']=Question.objects.get(id=list_id).topic_id.subject_id_id
		page_title = "Question ID: " + list_id
	
	#to display number of questions (and assist in other operations)
	no_of_qn=len(sel)
	
	#addMaths_q_per_page is the number of questions per page
	#from the list and page number, display current page's questions
	page_items=[]
	for i in range(0,addMaths_q_per_page):
		if( (i + addMaths_q_per_page * (int(page_no) - 1))<no_of_qn):
			page_items.append(sel[i + addMaths_q_per_page * (int(page_no)-1)])
	
	#create links of pages (determine number of pages)
	no_pages=no_of_qn/addMaths_q_per_page
	if((no_of_qn % addMaths_q_per_page)!=0):
		no_pages=no_pages+1
	page_links=[]
	for i in range(1,no_pages+1):
		page_links.append(i)
	
	#call helper method to process content of each question
	for q in page_items:
		#pack in related content
		q['taglist']=[]
		q['topic']=Topic.objects.get(id=q['topic_id']).title
		q['subtopic']=Subtopic.objects.get(id=q['subtopic_id']).title
		p=Paper.objects.get(id=q['paper_id'])
		q['paper']=str(p.year) + ' ' + p.month + ' Paper ' + str(p.number)
		
		#the main question display
		q['display']=process_question(q) 
		
		if list_type == "tag":
			#list keywords involved. ONLY keywords
			keywordTags = ''
			tags = list_id.split('|')
			for t in tags:
				tagdef = TagDefintion.objects.get(id=t)
				if tagdef.type == "K":
					keywordTags += tagdef.content + '%'
			keywordTags = keywordTags[0:len(keywordTags)]
			#track down the keyword and BOLD it
			for qitem in q['display']:
				if qitem['type'] == 1:
					for keyword in keywordTags.split('%'):
						p = re.compile('^' + keyword + '$')
						newstring=''
						for word in qitem['value'].split():
							if word[-1:] == ',':
								word = word[0:len(word)-1]
								if p.match(word) != None:
									newstring += '<b>' + word + '</b>' + ', '
								else:
									newstring += word + ', '
							else:
								if p.match(word) != None:
									newstring += '<b>' + word + '</b>' + ' '
								else:
									newstring += word + ' '
						qitem['value']=newstring
		
		#pack the answer
		q['displayans']=''
		if len(Solution.objects.filter(question_id=q['id'])) > 0:
			ans=list(Solution.objects.filter(question_id=q['id']).values())[0]
			q['displayans']=process_solution(ans)
		taglist = Tag.objects.filter(question_id=q['id']).order_by('tagdefinition__title')
		if len(taglist) != 0:
			for t in taglist:
				q['taglist'].append(t)
	
	param['questions']=page_items
	param['page_links']=page_links
	param['page_no']=int(page_no)
	param['num_q']=no_of_qn
	param['title']=page_title
	param['subj_id']=subj_id
	#parameters to open next page (call back to this function)
	param['list_id']=list_id
	param['paperset_id']=paperset_id
	param['topic_id']=topic_id
	param['list_type']=list_type
	#for links
	param['subject']=Subject.objects.all()

	#for browser menu
	param['papers']=list(Paper.objects.filter(subject_id=subj_id,number__gt=0,year__lt=2008).only('id','year','month','number').order_by('id').values())	
	# query list of topics
	topics=list(Topic.objects.filter(block__subject__id=subj_id).order_by('id').values())
	tags=list(TagDefinition.objects.filter(id__gt=290).order_by('id').values())
	param['tags']=tags
	param['topics']=topics
	#for links
	param['cur_subj']=Subject.objects.get(id=subj_id)
			
	return render_to_response('control/add_math_question.html',param,RequestContext(request))



	
#Display question selected from question list

def display_add_math_question(request,question_id):

	param = {}
	#get question and save into a list
	q=list(question.objects.filter(id=question_id).values())
	#q['display']=process_question(q)
	searchtype = request.GET.get("searchtype")
	page_title = "Question ID: " + question_id 
	
	taglists=[]
	qid_set=[]
	recommended_questions=[]
	recommended_questions_topic=[]
	for qtn in q:
		qid_set.append(qtn['id'])

	for qtn in q:
		question_tags=list(tag.objects.filter(question_id=qtn['id'],tag__type='K').order_by('tag__title'))
		for keyword in question_tags:
			keyword.qs=[]
			taglists.append(keyword.tagdefinition.title)
			keyword.link=tag.objects.filter(tag_id=keyword.tagdefinition_id)	
			for eachlink in keyword.link:
				qstns=question.objects.get(id=eachlink.question_id_id)
				keyword.qs.append(qstns)

		tag_list=list(tag.objects.filter(tag__title__in=taglists).order_by('question_id','q_count').values('question_id').annotate(q_count=Count('question_id')))
		qid_list=[]
		for tagitem in tag_list:
			qid_list.append(tagitem['question_id'])
		
		global_sel = list(question.objects.filter(id__in=qid_list).only('id','content','question_no','marks','topic_id_id').order_by('id').values())
		
		for qn in global_sel:
			if qn['id'] != question_id:
				recommended_questions.append(qn)
				if qn['topic_id_id'] == qtn['topic_id_id']:
					recommended_questions_topic.append(qn)

		for qstn in recommended_questions:
			qstn['match'] = 0
			for keyword in question_tags:
				for eachlink in keyword.link:
					if eachlink.question_id_id == qstn['id']:
						qstn['match'] += 1
		recommended_questions.sort(key = itemgetter('match','id'), reverse=True)

		for qstn in recommended_questions_topic:
			qstn['match'] = 0
			for keyword in question_tags:
				for eachlink in keyword.link:
					if eachlink.question_id_id == qstn['id']:
						qstn['match'] += 1
		recommended_questions_topic.sort(key = itemgetter('match','id'), reverse=True)

		for ques in recommended_questions:
			ques['content_short'] = ques['content'][0:100]
			p=paper.objects.get(id=ques['paper_id_id'])
			ques['paper']=str(p.year) + ' ' + p.month + ' Paper ' + str(p.number)
		for ques in recommended_questions_topic:
			ques['content_short'] = ques['content'][0:100]
			p=paper.objects.get(id=ques['paper_id_id'])
			ques['paper']=str(p.year) + ' ' + p.month + ' Paper ' + str(p.number)

		qtn['recommended_questions'] = recommended_questions[0:5]
		qtn['recommended_questions_topic'] = recommended_questions_topic[0:5]

	#call helper method to process content of each question
	for qtn in q:
		qtn['taglist']=[]
		qtn['topic']=topic.objects.get(id=qtn['topic_id_id']).title
		qtn['subtopic']=subtopic.objects.get(id=qtn['subtopic_id_id']).title
		p=paper.objects.get(id=qtn['paper_id_id'])
		qtn['paper']=str(p.year) + ' ' + p.month + ' Paper ' + str(p.number)
		qtn['display']=process_question(qtn)
		keywordTags = ''
		tags = request.GET.getlist("tag")
		for t in tags:
			tagdef = tag_definitions.objects.get(title=t)
			if tagdef.type == "K":
				keywordTags += tagdef.content + '%'
		keywordTags = keywordTags[0:len(keywordTags)]
			
		for qitem in qtn['display']:
			if qitem['type'] == 1:
				for keyword in keywordTags.split('%'):
					p = re.compile('^' + keyword + '$')
					newstring=''
					for word in qitem['value'].split():
						if word[-1:] == ',':
							word = word[0:len(word)-1]
							if p.match(word) != None:
								newstring += '<b>' + word + '</b>' + ', '
							else:
								newstring += word + ', '
						else:
							if p.match(word) != None:
								newstring += '<b>' + word + '</b>' + ' '
							else:
								newstring += word + ' '
					qitem['value']=newstring
		qtn['displayans']=''
		if len(answer.objects.filter(question_id=qtn['id'])) > 0:
			ans=list(answer.objects.filter(question_id=qtn['id']).values())[0]
			qtn['displayans']=process_solution(ans)
		taglist = tag.objects.filter(question_id=qtn['id']).order_by('tag__title')
		if len(taglist) != 0:
			for t in taglist:
				qtn['taglist'].append(t)
	
	param['questions']=q
	param['tags']=tags
	param['searchtype'] = searchtype
	param['title'] = page_title
	param['cur_subj'] = subject.objects.get(id=3)
	
	#for csrf of dajax
	return render_to_response('control/display_add_math_question.html',param,RequestContext(request))

#helper method to split question group
def get_qType(field_value):
	#questions in question group is separated by '|'
	parts=field_value.strip(' ').split('|')
	itemlist=[]
	val_count=0
	#set variables to display for each type of question
	for p in parts:
		i=p.split(',')
		item={}
		item['type']=i[0] #first character represents type
		item['count']=val_count
		if(i[0]=='v'):	#value
			item['unit']=i[1]			
		elif(i[0]=='c'):	#coordinates
			item['num']=range(0,int(i[1]))
			item['unit']=i[2]			
		elif(i[0]=='m'):	#matrix
			item['num']=range(0,int(i[1])*int(i[2]))
			item['col']=int(i[2])
		elif(i[0]=='e' or i[0]=='n'):	#equation or not
			item['val']=i[1]
			item['unit']=i[2]			
		elif(i[0]=='i'):	#inequality
			item['val']=i[1]
			item['unit']=i[2]
			item['lower']=i[3][0]
			item['upper']=i[3][1]
		#ratio has no extra settings
			
		itemlist.append(item)
		val_count=val_count+1		
	return itemlist

#display solution (Standard Answers with steps and diagrams)
def process_solution(q):
	#query images
	img_sel=list(Image.objects.filter(qa_id=q['question_id'],qa='Solution').only('id','imagepath').order_by('id').values())
	img_iterator=0
	limit=len(img_sel)
	#split question's content using ';' as separator
	token=q['content'].split(';')	
	display=[]
	#for each part of content, determine if text or image
	#for t in token:
	#	item={}
	#	if t.strip()!="img":
	#		item['type']=1
	#		item['value']=t.strip()
	#	else:
	#		item['type']=2
	#		if img_iterator<limit:
	#			item['value']=add_math_img + img_sel[img_iterator]['imagepath']
	#		else:
	#			item['value']='no_image'
	#		img_iterator=img_iterator+1
	#	display.append(item)
	return display
	


#display tag list	
def AddMaths_Admin_TagList(request,subj_id):
	param={}
	param.update(current(subj_id))
	tag_type=request.GET.get('type')
	param['type']=tag_type
	
	if tag_type != None:
		taglist = TagDefinition.objects.filter(type=tag_type).order_by('title')
		for t in taglist:
			t.content = process_tag(t)
			#t.content ='\n'+t.content.replace(';','\n')
			t.noTag = Tag.objects.filter(tagdefinition = t.id).count()
		param.update(current(subj_id))
		#Do paging 
		paginator = Paginator(taglist, 5)
			
		try: page = int(request.GET.get("page", '1'))
		except ValueError: page = 1

		try:
			taglist = paginator.page(page)
		except (InvalidPage, EmptyPage):
			taglist = paginator.page(paginator.num_pages)
		param['taglist']=taglist
	return render_to_response('control/add_math_admin_taglist.html',param,RequestContext(request))

#delete a tag
def AddMaths_Admin_DeleteTag(request,subj_id):
	param={}
	
	tag_id = int(request.GET.get('id'))
	
	if tag_id > 0:
		tagdef = TagDefinition.objects.get(id=tag_id)
		tags = Tag.objects.filter(tagdefinition=tagdef)
		tags.delete()
		tagdef.delete()
	param.update(current(subj_id))
	param['mes'] = "<div class='alert alert-success' >The tag has been removed successfully</div>"
	return render_to_response('control/add_math_admin_taglist.html',param,RequestContext(request))

#create/modify a tag	
def AddMaths_Admin_TagForm(request,subj_id):
	param={}
	param['topics'] = Topic.objects.all()
	
	tag_id = 0
	if request.GET.get('id') != None:
		tag_id = int(request.GET.get('id'))
	
	if tag_id > 0:
		tagdef = TagDefinition.objects.get(id=tag_id)
		param['tag_def'] = tagdef
		param['display']='\n'+tagdef.content.replace(';','\n')
		param.update(current(subj_id))
	return render_to_response('control/add_math_admin_tagform.html',param,RequestContext(request))

#save a tag	
def AddMaths_Admin_SaveTag(request,subj_id):

	param={}
	
	#parameter values
	tag_id=request.POST.get('tag_id','')
	tag_title=request.POST.get('title','')
	tag_type=request.POST.get('type','')
	tag_topic=request.POST.get('topic','')
	tag_content=request.POST.get('desc','')
	
	if tag_id != '': #existing tag
		tagdef = TagDefinition.objects.get(id=tag_id) #retrieve old object
		if tag_title != '' and tag_type != '': #check mandatory attributes before modifications
			tagdef.title = tag_title
			tagdef.type = tag_type
			if int(tag_topic) == 0: #null a topic if not assigned
				tagdef.topic = None
			else:
				tagdef.topic = Topic.objects.get(id=tag_topic) #assign topic
			tagdef.content = string.join(string.split(tag_content, '\n'), ';')
			tagdef.save()
	else: #new tag
		if tag_title != '' and tag_type != '': #check mandatory attributes before modifications
			tpc = None
			if int(tag_topic) > 0:
				tpc = Topic.objects.get(id=tag_topic) #assign topic if found
			tagdef = TagDefinition(title=tag_title, type=tag_type, topic=tpc, content=tag_content)
			tagdef.save()
	param.update(current(subj_id))
	return render_to_response('control/add_math_admin_taglist.html',param,RequestContext(request))
	
#method to process question into display format
def process_tag(t):
	#query for all images for this question
	img_sel=list(Image.objects.filter(qa_id=t.id,qa='Tag').only('id','imagepath').order_by('id').values())
	
	#split the content of question using ';' as separator
	token=t.content.split(';')	
	display=[]
	item={}
	img_iterator=0
	#for each question part
	for t in token:
		#if is not image, add as text
		if t.strip()!="img":
			item['type']=1
			item['value']=t.strip()
		else:
			#if image, substitude the image path
			item['type']=2
			if len(img_sel)>img_iterator:
				#add path to where image folder is
				item['value']=add_math_img + img_sel[img_iterator]['imagepath']
			else:
				item['value']='missing image'
			img_iterator=img_iterator+1
		#The processed part is added into a list representing the content
		display.append(item)
		item={}
	
	#The 'type' helps identify images (1 for text, 2 for image)
	#In cases where image is not found, 'missing image' text is used
	return display	

def AddMaths_Admin_QuestionForm(request,list_type,page_no,list_id,subj_id,question_id):	#form
	param={}
	
	#if less than 0, insert new question
	param['question']=None
	if(int(question_id)>=0):
		param['question']=Question.objects.get(id=question_id)
		param['source']=param['question'].source
		param['difficulty']=param['question'].difficulty
		param['topic']=param['question'].topic.title
		param['subtopic']=param['question'].subtopic.title
		param['paper']=Paper.objects.get(id=param['question'].paper_id)
		param['marks']=param['question'].marks
		param['display']='\n'+param['question'].content.replace(';','\n')
		if len(Solution.objects.filter(question_id=question_id)) == 1:
			param['solution']='\n'+Solution.objects.get(question_id=question_id).content.replace(';','\n')
		
		#param['formula'] = '\n'
		#if len(formula.objects.filter(question_id=question_id)) > 0:
		#	formula_list = formula.objects.filter(question_id=question_id).values()
		#	for f in formula_list:
		#		param['formula'] += f['formula']+'\n'
		
		param['tags']=Tag.objects.select_related().filter(question_id=question_id)
		param['tagdefs']=TagDefinition.objects.all()
		

	else:
		param['tagdefs']=TagDefinition.objects.all()
		
	param['list_type']=list_type
	param['page_no']=page_no
	param['list_id']=list_id
	
	#for new questions (additional info to select)
	param['year_list']=range(1995,datetime.datetime.now().year) #up till previous year
	topics=list(Topic.objects.filter(block__subject_id=subj_id).order_by('-id').filter(block__subject_id = subj_id).values())
	#topics.reverse()
	param['topics']=[]
	for t in topics:
		param['topics'][0:0]=list(Topic.objects.filter(id=t['id']).values())
	param['subtopics']=[]
	for t in topics:		
		param['subtopics'][0:0]=list(Subtopic.objects.filter(topic_id=t['id']).values() )
		
	param['subj_id']=subj_id
	
	#for links
	param['subject']=Subject.objects.all()
	param.update(current(subj_id))
	#for csrf for preview page
	return render_to_response('control/add_math_admin_form.html',param,RequestContext(request))
	
	
def AddMaths_qChange(request,list_type,page_no,subj_id):

	q_id=request.POST.get('a_q_id','')
	q_content=request.POST.get('a_content','')
	q_sol=request.POST.get('a_sol','')
	q_formula=request.POST.get('a_formula','')
	q_input=request.POST.get('a_input','')
	q_type=request.POST.get('a_type','')
	q_ans=request.POST.get('a_ans','')
	q_tag=request.POST.get('a_tag','')
	q_topic=request.POST.get('paper_topic','')
	
	q_subtopic=request.POST.get('paper_subtopic','')
	q_new_tag=request.POST.get('a_new_tag','')
	q_marks=request.POST.get('a_marks','')
	q_source=request.POST.get('q_source','')
	q_difficulty=request.POST.get('q_difficulty','')
	
	q_item=None
	if(q_id!=''):
		q_item=Question.objects.get(id=q_id)
	else:
		#question number
		q_no=1
		#for new question, find or insert paper
		q_year=request.POST.get('paper_year','')
		q_month=request.POST.get('paper_month','')
		q_num=request.POST.get('paper_num','')
		q_topic=request.POST.get('paper_topic','')
		q_subtopic=request.POST.get('paper_subtopic','')
		q_paper_id=q_year
		if(q_month=='11' and q_num=='1'):
			q_paper_id=q_paper_id+'01'
		elif(q_month=='11' and q_num=='2'):
			q_paper_id=q_paper_id+'02'
		q_paper_id=q_paper_id+'{0:0>3}'.format(subj_id)
		cur_paper=Paper.objects.filter(id=q_paper_id)
		if(len(cur_paper)==0):
			cur_paper=Paper()
			cur_paper.id=q_paper_id
			cur_paper.year=q_year
			cur_paper.month=q_month
			cur_paper.month=q_month
			cur_paper.number=q_num
			cur_paper.subject=Subject.objects.get(id=subj_id)
			#create paperset
			cur_paperset = Paperset()
			cur_paperset.title = str(q_year)+" "+cur_paper.month
			cur_paperset.subject = cur_paper.subject
			cur_paperset.save()
			cur_paper.paperset = cur_paperset
			cur_paper.save()
			
		else:
			q_no=len(Question.objects.filter(paper_id=q_paper_id))+1
			
		q_item=Question()
		#generate id
		q_item.id=q_year
		if(q_month=='11' and q_num=='1'):
			q_item.id=q_item.id+'01'
		elif(q_month=='11' and q_num=='2'):
			q_item.id=q_item.id+'02'
		q_item.id=q_item.id+'{0:0>3}'.format(subj_id)
		q_item.id=q_item.id+'{0:0>3}'.format(q_no)
		q_item.source = q_source
		q_item.difficulty = q_difficulty
		#end
	
		q_item.paper_id=Paper.objects.get(id=q_paper_id)
		q_item.question_no=q_no
	
	
	q_item.topic_id=Topic.objects.get(id=q_topic).id
	q_item.subtopic_id=Subtopic.objects.get(id=q_subtopic).id
	q_item.content=q_content
	q_item.marks=q_marks
	q_item.input=q_input
	q_item.type=q_type
	q_item.type_answer=q_ans

	
	#must include
	q_item.q_category=''
	q_item.q_type='exam'
	q_item.difficulty_level=''
	q_item.num_views='0'
	
	q_item.save()
	
	#tag update
	oldtags =Tag.objects.filter(question_id=q_item.id)
	oldtags.delete()
	
	#existing tag format
	etags = q_tag.split(';') #split into tags
	for etag in etags:
		if etag != '':
			if len(TagDefinition.objects.filter(id=int(etag))) > 0: #verify tag exists
				tagdef = TagDefinition.objects.get(id=int(etag))
				new_etag_record = Tag(question=q_item, tagdefinition=tagdef)
				new_etag_record.save()
	#new tag format
	ntags = q_new_tag.split('||') #split into tags
	for ntag in ntags:
		columns = ntag.split(';')
		if len(columns) == 3: #title, content, type
			new_ntag_record = TagDefinition(title=columns[0], content=columns[1], type=columns[2])
			new_ntag_record.save() #create the new tag first
			new_etag_record = Tag(question=q_item, tagdefinition=new_ntag_record)
			new_etag_record.save() #save the relationship with the question
	
	#answer update
	if len(Solution.objects.filter(question_id=q_item.id)) > 0: #update existing
		cur_answer = Solution.objects.get(question_id=q_item.id)
		cur_answer.content = q_sol
		cur_answer.save()
	else:
		cur_answer = Solution(question_id=q_item, content=q_sol)
		cur_answer.save()

	#formula update and indexing
	
	#formulae=formula.objects.filter(question_id=q_item.id)
	#formulae.delete();
	#q_formula_list = q_formula.split(';')
	#for f in q_formula_list:
	#	if f != '':
	#		cur_formula = formula(question_id=q_item.id, formula=f, status=0)
	#		cur_formula.save()

	#index(request)
		
	return add_math_question(request,list_type,subj_id,page_no)
