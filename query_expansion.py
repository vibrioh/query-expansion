import pprint
from googleapiclient.discovery import build
import sys
import re
from collections import defaultdict
import math


class Query_result(object):
    def __init__(self, title=None, link=None, snippet=None):
        self.title = title
        self.link = link
        self.summary = snippet
        self.is_relevant = False


def search(query_terms):
    '''
    Search by calling Google Custom Search API
    with input query terms. 
    Return a list of (10) search results.
    '''
    # Call Google Custom Search API
    service = build("customsearch", "v1", developerKey=JSON_API_KEY)
    query = ' '.join(query_terms)
    res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID,).execute()
    
    # Parse returned query results
    result = []
    for item in res['items']:
        # unicode to utf-8
        title = item['title'].encode('utf-8').strip()
        link = item['link'].encode('utf-8').strip()
        snippet = item['snippet'].encode('utf-8').strip()
        t = Query_result(title, link, snippet)
        result.append(t)
    
    return result


def get_feedback(query_result, query):
    '''
    Print query results out, 
    Add user's feedback information
    to Query_result.label attribute
    '''
    print "Parameters:"
    print "Client Key = {}\nEngine Key = {}\nQuery = {}\nPrecision = {}".format(JSON_API_KEY, SEARCH_ENGINE_ID, ' '.join(query), PREC)
    print "Google Search Results:"
    print "======================"
    
    # Print each query result
    for i, v in enumerate(query_result):
        print "\nResult #{}:".format(i+1)
        print "["
        print "URL: {}\n".format(v.link)
        print "Title: {}\n".format(v.title)
        print "Summary: {}\n".format(v.summary)
        print "]\n"
        # Receive user's feedback
        feedback = raw_input("Relevant ([Y]/N)?")
        assert(feedback == '' or feedback.lower() in 'yn')
        if feedback == '' or feedback.lower() == 'y':
            v.is_relevant = True

    return


def modify_query(query_result, query, alpha=0.75, beta=0.15):
    '''
    According to the user's feedback,
    derive new terms for query,
    and adjust order of query terms.
    '''
    N = len(query_result)
    re_vectors, irre_vectors, doc_freq = [], [], defaultdict(set)
    
    # Count term frequency and document frequency for each term in each document
    print "Indexing results ..."
    for i, v in enumerate(query_result):
        vector = defaultdict(int)
        terms = regularize(v.title + ' ' + v.summary) # terms: all terms in a document
        for term in terms:
            doc_freq[term].add(i)
            vector[term] += 1
        if v.is_relevant:
            re_vectors.append(vector)  
        else:
            irre_vectors.append(vector)         
    
    # After this loop, every vector, each representing a document,
    # will store the tf-idf value for each term in this document
    for vector in re_vectors + irre_vectors:
        for term in vector:
            vector[term] = math.log(1+vector[term], 10) * math.log(float(N)/len(doc_freq[term]), 10) * 10000
    
    # Rocchio Algorithm -- combine all relevant and irrelevant vectors
    print "Indexing results ..."
    DR, DNR = len(re_vectors), len(irre_vectors)
    new_vector = defaultdict(float)
    for vector in re_vectors:
        for term in vector:
            new_vector[term] += vector[term] * alpha / DR 
    for vector in irre_vectors:
        for term in vector:
            new_vector[term] = max(0, new_vector[term] - vector[term] * beta / DNR)

    # Print new_vector, for test purposes
    # pprint.pprint(sorted([(i, v) for i, v in new_vector.iteritems()], key=lambda x: x[1], reverse=True))
        
    # Find (up to) 2 "new" terms in new_vector and add them to query terms
    first, second, first_val, second_val = '', '', 0, 0
    for term in new_vector:
        if term not in query and new_vector[term] > 0: # pass terms that are already in query terms
            weight = new_vector[term]
            if weight > first_val:
                first, first_val, second, second_val = term, weight, first, first_val
            elif weight > second_val:
                second, second_val = term, weight
            else:
                pass
    
    if first: query.append(first)
    if second: query.append(second)    
    print "Augmenting by {}".format(first + ' ' + second)
    
    # Arrange new order of query terms:
    query = ORIGIN_QUERY.rstrip('\n').split() + \
    map(lambda x: x[0], sorted([(t, new_vector[t]) for t in query if t not in ORIGIN_QUERY], \
                               key=lambda x: x[1], reverse=True))

    return query


def regularize(string):
    '''
    Discard all punctuations and stopwords, 
    convert all letters to lower case.
    '''
    return [word for word in re.sub(r'[^a-zA-Z0-9_ ]', '', string).lower().strip().split()\
            if word not in STOPWORDS]


def get_stopwords():
    '''
    Get a set of stopwords.
    '''
    with open('./proj1-stop.txt') as f:
        return set(word.rstrip('\n') for word in f.readlines())


def main():
    '''
    Main function.
    '''
    # Parse Arguments
    global JSON_API_KEY, SEARCH_ENGINE_ID, PREC, ORIGIN_QUERY, STOPWORDS
    JSON_API_KEY, SEARCH_ENGINE_ID, PREC, ORIGIN_QUERY = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    PREC = float(PREC)
    ORIGIN_QUERY = ORIGIN_QUERY.lower()  # Record original query terms
    STOPWORDS = get_stopwords()
    query = ORIGIN_QUERY.rstrip('\n').split()
    
    ### MAIN LOOP ###
    while True:
        query_result = search(query)
        if len(query_result) < 10:
            print "Not enough query results. Stop."
            return
        get_feedback(query_result, query)
        print "======================"
        print "FEEDBACK SUMMARY"
        print "Query {}".format(' '.join(query))
        prec = sum(q.is_relevant for q in query_result) / float(len(query_result))
        print "Precision {}".format(prec)
        if prec >= PREC:  # Reached goal, exit
            print "Desired precision reached, Done!"
            return
        elif prec == 0.0:  # Precision too low, exit
            print "Precision reached zero, stop."
            return
        print "Still below the desired precision of {}".format(PREC)
        query = modify_query(query_result, query)
    
    return


if __name__ == '__main__':
    main()