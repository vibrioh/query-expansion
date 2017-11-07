## Files

Name | Usage
--- | ---
query_expansion.py | main program
proj1-stop.txt | a list of stopwords
transcript.pdf | a transcript of the runs of the program on the 3 test cases given

## Dependencies
**Google Cloud Client Libaraies for Python**

To install, run `$ pip install --upgrade google-api-python-client`

## How to Run
Under the program's root directory, run

`
$ python query_expansion.py <google api key> <search engine id> <precision> "<query>"
`

## Internal Design

The program will first get arguments such as _API key_, _search engine ID_, _precision@10_, and _query terms_ from user input. 

Then, in function `search()`, Google Custom Search API would be called to conduct the query. For each query result receive from API call, the program encode context to utf-8 format, extract information including title, link URL, and summary, and stored each result to a `Query_result` object. All results will be stored together in `query_result` list.

In function `get_feedback()`, the program will print out each query result and get them labeled as `True` or `False` by user. Then, the precision rate of current query would be computed. If this precision reaches _precision@10_ goal or zero, then terminate the program. Otherwise, function `modify_query()` would be called to prepare for next round query.

In function `modify_query()`, query terms would be augmented by up to 2 new words. The order of query terms might also be adjusted. The method of expanding and reordering query terms is largely based on _Rocchio's Algorithm_, and would be explained in detail in the _Query-modification Method_ section. Then, the modified query would be fed into Google Custom Search API for the next iteration of query.

## Query-modification Method


### Regularizing Context
For each query result, title and summary context would be regularized by function `regularize()` -- punctuations and stopwords will be removed, and all uppercase letters would be converted to lowercase. Then, they are grouped into relevant documents and irrelevant documents.

### Vector-space Model
The document frequency for every word is first computed. Then, for each document, the term frequency is computed and then the vector is generated. Each vector is stored in a python dictionary, in which keys and their corresponding values are words and their tf-idf weights respectively.

### Rocchio's Algorithm -- Augmenting and Reordering
A `new_vector` is computed according to the formula
$$\vec{q_{m}} = \alpha\frac{1}{D_r}\sum_{\vec{d_j}\in D_r}\vec{d_j} - \beta\frac{1}{D_{nr}}\sum_{\vec{d_j}\in D_{nr}}\vec{d_j}$$where $D_r$ and $D_{nr}$ are the set of relevant and irrelevant documents respectively. In our implementation, $\alpha$ is set to 0.75 and $\beta$ is 0.15. Among all words in `new_vector`, (up to) two words that have highest weight and not in current query terms will be added to new query terms. Our reordering process follows the following rule: words appearing in original query will be placed in the top front without changing the order; then, the rest terms are sorted in descending order according to their weights in `new_vector` (weights of words that do not show up would be set to 0). 

