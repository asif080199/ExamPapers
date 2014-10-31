# coding: utf-8
from datetime import datetime
from itertools import chain
from django.utils.encoding import smart_unicode, smart_str
import math

from django.conf import settings

from ExamPapers.fsearch.formula_indexer import features_extraction, ino_sem_terms, sort_sem_terms
from ExamPapers.DBManagement.models import *


def formula_retrieval(sorted_sem_terms, k=20):
    related_formulas = set()
    if sorted_sem_terms is None:	
        return related_formulas
    
    for element in range(len(sorted_sem_terms)):
        for term in sorted_sem_terms[element]:
            print term
            print "."
            try:      
                f_index = formula_index.objects.get(pk=term)
                posting_list  = (f_index.docsids.replace('#', ' ')).split()
        
                formula_objs = formula.objects.filter(pk__in=posting_list, status__exact=True)                                  
                #Convert string to list
                for obj in formula_objs:
                    if obj.status:
                        inorder_temp        = eval(obj.inorder_term)
                        obj.inorder_term    = [term for term in chain.from_iterable(inorder_temp)]
                        
                        sorted_temp         = eval(obj.sorted_term)
                        obj.sorted_term     = sorted_temp[len(sorted_temp)-1]
                        
                        obj.structure_term  = eval(obj.structure_term)
                        obj.constant_term   = eval(obj.constant_term)
                        obj.variable        = eval(obj.variable_term)

                        related_formulas.add(obj)
                                
            except (KeyError, formula_index.DoesNotExist):
                pass
        if len(related_formulas) >= k:
            break

    return list(related_formulas)

def is_function(term):

    operator_terms = ('lim', 'Lim', 'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh', 
                      'cot', 'sec', 'cosec', 'csc', 'log', 'ln', 'lg', 'det', 'gcd', 
                      'lcm', 'min', 'max', 'msqrt', 'mroot')
    
    #("'" +'∫'+ "'").decode('utf-8'), ("'" +'∑'+ "'").decode('utf-8'), ("'" +'∈'+ "'").decode('utf-8'), ':', ("'" +'+'+ "'").decode('utf-8'),("'" +'-'+ "'").decode('utf-8'),("'" +'='+ "'").decode('utf-8')
    return term.endswith(operator_terms)

def sem_matching_score(matching_1gram_sort, unmatching_1gram_sort, 
                       matching_ngram_inorder, unmatching_ngram_inorder, IDF_values, N):
    sem_score = 0
    num_of_func = 0

    for term in matching_1gram_sort:
        if term in IDF_values:
            sem_score += IDF_values.get(term)
        if is_function(term):
            num_of_func += 1
    
    sem_score += num_of_func*math.log10(N)
    
    for term in unmatching_1gram_sort:        
        if term in IDF_values:
            sem_score -= IDF_values.get(term)
        
    for term in matching_ngram_inorder:
        if term in IDF_values:
            sem_score += IDF_values.get(term)        
    return sem_score

def struc_matching_score(matching_struc, IDF_values):
    struc_score = 0 
    for term in matching_struc:
        if term in IDF_values:
            struc_score += IDF_values.get(term)
    
    return struc_score

def cn_matching_score(matching_cn):
    return len(matching_cn)

def var_matching_score(matching_var):
    return len(matching_var)

def compute_IDF_values(query_ino_terms, query_sort_terms, query_struc_fea, related_formulas, N):
    IDF_values = dict()
    terms_collection = set(query_ino_terms + query_sort_terms + query_struc_fea)    
        
    for rel_formula in related_formulas:
        terms_collection.update(set(rel_formula.inorder_term + 
                                    rel_formula.sorted_term + 
                                    rel_formula.structure_term))
    
    formula_index_obj = formula_index.objects.filter(pk__in=terms_collection)
    for obj in formula_index_obj:
        IDF_values[obj.indexkey]=math.log10(N/obj.df)
        
    return IDF_values

def compute_score(sem_score_norm, struc_score_norm, cn_score_norm, var_score_norm, a=0.2):
    
    return ((1-a)*(sem_score_norm+struc_score_norm) + 
            a*(cn_score_norm+var_score_norm))/2
            
def formula_score(query_inoder_ngram, query_sort_1gram, query_struc, query_cn, query_var, retrie_inoder_ngram, retrie_sort_1gram, retrie_struc, retrie_cn, retrie_var, IDF_values, N):
    
    sem_score = sem_matching_score(set(query_sort_1gram)&set(retrie_sort_1gram), 
                       set(retrie_sort_1gram)-set(query_sort_1gram), 
                       set(query_inoder_ngram)&set(retrie_inoder_ngram), 
                       set(retrie_inoder_ngram)-set(query_inoder_ngram), 
                       IDF_values, N)
   
    struc_score = struc_matching_score(set(query_struc)&set(retrie_struc), IDF_values)
    
    cn_score = cn_matching_score(set(query_cn)&set(retrie_cn))
    
    var_score = var_matching_score(set(query_var)&set(retrie_var))
    
    return (sem_score, struc_score, cn_score, var_score)

def formulas_ranking(query_ino_terms, query_sort_1gram, query_struc_fea, query_cn_fea, query_var_fea, related_formulas, IDF_values, N):
    ranked_scores = list()
            

    (sem_score_norm, struc_score_norm, cn_score_norm, var_score_norm) = \
        formula_score(query_ino_terms, query_sort_1gram, query_struc_fea, 
                      query_cn_fea, query_var_fea, query_ino_terms, query_sort_1gram, 
                      query_struc_fea, query_cn_fea, query_var_fea, IDF_values, N)    
        
    for rel_formula in related_formulas:        
        (sem_score, struc_score, cn_score, var_score) = \
            formula_score(query_ino_terms, query_sort_1gram, query_struc_fea, 
                          query_cn_fea, query_var_fea, rel_formula.inorder_term, 
                          rel_formula.sorted_term, rel_formula.structure_term, 
                          rel_formula.constant_term, rel_formula.variable_term, 
                          IDF_values, N)
        
        if sem_score_norm != 0:
            sem_score = sem_score/sem_score_norm
        if struc_score_norm != 0:
            struc_score = struc_score/struc_score_norm
        if cn_score_norm != 0:
            cn_score = cn_score/cn_score_norm
        if var_score_norm != 0:
            var_score = var_score/var_score_norm
        score = compute_score(sem_score, struc_score, cn_score, var_score)
        if score > 0:
            ranked_scores.append((rel_formula, score))
    
    results = []
    temp_result = sorted(ranked_scores, key=lambda scores:scores[1], reverse=True)
    for index, (rel_formula, score) in enumerate(temp_result):
        question = rel_formula.question
        results.append([rel_formula.question_id, question.topic_id_id, question.content, rel_formula.formula, index+1, index+2, score])
    
    return results, len(temp_result) 

def search_content_formula(mathML):
    (query_sem_fea, query_struc_fea, query_cn_fea, query_var_fea) = features_extraction(mathML)
    print query_sem_fea
    print "----------------"
    print query_struc_fea
    print "----------------"
    print query_cn_fea
    print "----------------"
    print query_var_fea
	
    query_ino_terms = ino_sem_terms(query_sem_fea)	# sematic term in order
    query_sort_terms = sort_sem_terms(query_sem_fea)	# sematic term in sorted order

    related_formulas = formula_retrieval(query_sort_terms)

    query_ino_terms = [term for term in chain.from_iterable(query_ino_terms)]
    query_sort_terms = query_sort_terms[len(query_sort_terms)-1]
        
    N = formula.objects.count()
    
    IDF_values = compute_IDF_values(query_ino_terms, query_sort_terms, 
                                    query_struc_fea, related_formulas, N)

    results, num_of_results = formulas_ranking(query_ino_terms, query_sort_terms, query_struc_fea, 
                            query_cn_fea, query_var_fea, related_formulas, 
                            IDF_values, N)

    return results, num_of_results