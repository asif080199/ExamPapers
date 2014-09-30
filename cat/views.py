def get_next_question(user, topic_id, cur_question):

        # Rebuild session store
        if not session_store or session_store['engine'] != this_engine or session_store['topic'] != topic:
            session_store = {}
            session_store['engine'] = this_engine
            session_store['topic'] = topic
            session_store['numerator'] = 0
            session_store['denominator'] = 0
            session_store['ability'] = 0

            # Rebuild ability score from data
            responses = Response.objects.all().filter(user=user).filter(assessment=this_engine).filter(question__topic__exact=topic)
            for prev_response in responses:
                session_store = self._compute_ability(session_store, prev_response.criterion, prev_response.correctness)

        # Get tested questions and omit them from question pool
        question_tested = Response.objects.all().filter(user=user).filter(assessment=this_engine).filter(question__topic__exact=topic).values_list('question')
        question_pool = question_pool.exclude(id__in=question_tested)

        selected_question = None

        # Get a question using ability score (Legacy CAT code)
        max_info = -4
        question_info = {}
        best_questions = []

        for question in question_pool:
            # Normalisation of question difficulty due to remapped range (from -3 to +3 >> 1 to 5)
            difficulty = ((question.difficulty-1.0)/4.0 * 6.0)-3.0

            temp = 0
            temp = self._compute_item_info(session_store, difficulty)
            temp = temp * (1-temp)
            question_info[question.id] = temp
            if temp > max_info:
                max_info = temp
                best_questions = []
                best_questions.append(question)
            elif temp == max_info:
                best_questions.append(question)

        if best_questions:
            selected_question = best_questions[random.randint(0, len(best_questions)-1)]
            selected_question.question_info = question_info
	
	return selected_question