def _compute_item_info(self, session_store, difficulty):
        # magical code.
        a = 1
        b = float(difficulty)
        c = 0
        theta = session_store['ability']

        p_theta = 0
        p_theta = c + (1-c) * 1/(1 + math.exp(-a * (theta - b)))

        p_theta = p_theta * a * a

        return p_theta
	
def get_next_question(self, user, test, topic, session_store):
        # Small note: topic can be None. This happens when All Topics is chosen

        this_engine = Assessment.objects.all().get(name='CAT Test')

        # Rebuild session store
        if not session_store or session_store['engine'] != this_engine.name or session_store['test'] != test.id:
            session_store = {}
            session_store['engine'] = this_engine.name
            session_store['test'] = test.id
            session_store['numerator'] = 0
            session_store['denominator'] = 0
            session_store['ability'] = 0
            session_store['stderr'] = 0

            # Rebuild ability score from data
            responses = TestResponse.objects.all().filter(test=test)
            for prev_response in responses:
                session_store = self._compute_ability(session_store, prev_response.criterion, prev_response.correctness)

        # Get tested questions and omit them from question pool
        question_tested = TestResponse.objects.all().filter(test=test).values_list('question')
        question_pool = Question.objects.all().exclude(id__in=question_tested)
        # Don't filter by topic if it is not given
        if topic is not None:
            question_pool = question_pool.filter(topic=topic)
        else:
            # If topic is none, load the topics
            topic_pool = Topic.objects.all()

        selected_question = None

        # Get a question using ability score (Legacy CAT code)
        #max_info = -4
        min_info = 2
        question_info = {}
        best_questions = []

        for question in question_pool:
            # Normalisation of question difficulty due to remapped range (from -3 to +3 >> 1 to 5)
            difficulty = ((question.difficulty-1.0)/4.0 * 6.0)-3.0

            temp = 0
            temp = self._compute_item_info(session_store, difficulty)
            fitness = 1 - (temp * (1-temp))

#            if topic is None:
 #               topic_weight = 0
  #              topic_total = 0
   #             for atopic in topic_pool:
    #                topic_total = topic_total + atopic.weight
     #               if atopic == question.topic:
      #                  topic_weight = atopic.weight * 1
#
 #               topic_weight = topic_weight/topic_total
  #              fitness = fitness + 1 - topic_weight

            question_info[question.id] = fitness
            #if temp > max_info:
            #    max_info = temp
            # goal is to minimize
            if fitness < min_info:
                min_info = fitness
                best_questions = []
                best_questions.append(question)
            elif fitness == min_info:
                best_questions.append(question)

        if best_questions:
            if topic is None:
                question_info[0] = 100
            else:
                question_info[0] = 1

            selected_question = best_questions[random.randint(0, len(best_questions)-1)]
            selected_question.question_info = question_info

        return selected_question

		