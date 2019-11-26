import re
import os
import json
import random
import argparse
import pytrec_eval
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

"""Reads the file produced by wikiextract.
    
    Args:
        (str) file: path to the json file produced by wikiextractor
        (int) min_nb_words: minimum number of words in the article required to add it to the collection 
        
    Returns:
        (dict) documents: keys are doc ids and values are raw text of wikipedia articles
        (dict) documents_ids: keys are articles titles and values are the associated doc_ids

"""
def read_wikiextractor(file,min_nb_words,max_docs):
    documents = dict()
    documents_ids = dict()
    doc_id = 0
    with open(file) as f:
        for line in f:
            article = json.loads(line)
            text = article['text']
            if len(text.split(' ')) < min_nb_words : continue
            documents_ids[article['title']] = doc_id
            documents[doc_id] = text
            doc_id += 1
            if max_docs==doc_id : break
    return documents,documents_ids




"""Produces the qrel file than contains relevance judgments between queries and documents using links in documents.
    
    Args:
        (dict) documents: output of read_wikiextractor
        (dict) documents_ids: output of read_wikiextractor
        (int) len_doc: number of words from the article to keep in the documents (if None: keep all words) 
        (int) min_rel: minimum number of relevant doucments asosciated to the query to add the query to the qrel
        (bool) only_first_sentence: indicates whether or not to use only the links of the first sentence of articles to build the qrels
        
    Returns:
        (dict) qrels: keys are queries ids and values are a list of pair (doc_ids,relevance_level)
    
"""
def build_qrels(documents,documents_ids,len_doc,min_rel,only_first_sentence):
    qrels = {key:[] for key in documents}
    for key,value in documents.items():
        if only_first_sentence:
            end_of_title = value.find('\n')
            short_doc = value[end_of_title:]
            first_sentence_location = short_doc.find('.')
            short_doc = short_doc[:first_sentence_location]
        else:
            short_doc = ' '.join(value.split(' ')[:len_doc])
        list_qrels = re.findall(r'(?:href=")([^"]+)', short_doc)
        linked_docs = set([documents_ids[elem.replace('%20',' ')] for elem in list_qrels if elem.replace('%20',' ') in documents_ids])
        linked_docs.discard(key)
        for document in linked_docs:
            qrels[document].append([key,1])
            
    print(len(qrels),"qrels are initially build")
    
    delete = [key for key in qrels if len(qrels[key]) < min_rel]
    
    print(len(delete),"qrels have less than",min_rel,"relevant documents")
    
    for key in delete : del qrels[key]
    for key in qrels: qrels[key].insert(0,[key,2])
    return qrels




"""Clean the documents by removing special characters and href attributes and build the queries.
    
    Args:
        (dict) qrels: output of read_wikiextractor
        (dict) documents: output of read_wikiextractor
        (int) len_doc: number of words from the article to keep in the documents (ifNone: keep all words) 
        (int) len_query: maximum number of words in the query (if None: keep all words) 
        (bool) skip_first_sentence: indicates whether or not to remove the first sentence of the article when building the associated document
        (bool) title_queries: if True the query will be the article title; if False the query will be the first sentence of the article
        (bool) lower_cased: indicated whether or not to lower case the collection
        
    Returns:        
        (dict) documents: keys are doc ids and values are cleaned text of wikipedia articles
        (dict) queries: keys are queries ids and values are cleaned text of queries
"""
def clean_docs_and_build_queries(qrels,documents,len_doc,len_query,skip_first_sentence,title_queries,lower_cased):
    
    queries = dict()
    regex = re.compile('[^a-zA-Z0-9]')
    
    for key,value in documents.items():
        
        document = re.sub('<[^>]+>', '', value)
        end_of_title = document.find('\n')
        
        if title_queries and key in qrels:
            queries[key] = document[:end_of_title]
            
        document = document[end_of_title:]
        first_sentence_location = document.find('. ')
        
        if not title_queries and key in qrels:
            queries[key] = document[:first_sentence_location]
            
        if skip_first_sentence:
            if lower_cased:
                documents[key] = ' '.join(regex.sub(' ', document[first_sentence_location:]).lower().split()[:len_doc])
            else:
                documents[key] = ' '.join(regex.sub(' ', document[first_sentence_location:]).split()[:len_doc])
        else:
            if lower_cased:
                documents[key] = ' '.join(regex.sub(' ', document).lower().split()[:len_doc])
            else:
                documents[key] = ' '.join(regex.sub(' ', document).split()[:len_doc])
        
        if key in qrels:
            if lower_cased:
                    queries[key] = ' '.join(regex.sub(' ', queries[key]).lower().split()[:len_query])
            else:
                queries[key] = ' '.join(regex.sub(' ', queries[key]).split()[:len_query])

    return documents,queries




"""Deletes empty queries and documents and updates qrels.
    
    Args:
        (dict) documents: output of clean_docs_and_build_queries
        (dict) queries: output of clean_docs_and_build_queries
        (dict) qrels: output of build_qrels
        
    Returns:
        (dict) documents: output of clean_docs_and_build_queries
        (dict) queries: output of clean_docs_and_build_queries
        (dict) qrels: output of build_qrels
        
"""
def delete_empty(documents,queries,qrels):
    nb_empty = 0
    empty_documents = set()
    for key in [elem for elem in documents]:
        if documents[key].isspace() or not documents[key]:
            del documents[key]
            nb_empty += 1 
            empty_documents.add(key)
    
    print(nb_empty,'empty documents have been deleted',flush=True)
    
    nb_empty = 0
    for key in [elem for elem in queries]:
        if queries[key].isspace() or not queries[key] or key in empty_documents:
            del queries[key]
            del qrels[key]
            nb_empty += 1
    
    print(nb_empty,'empty queries have been deleted',flush=True)
    print('There are',len(documents),'documents',flush=True)
    print('There are',len(queries),'queries',flush=True)
    
    nb_paires = 0
    for key in [elem for elem in qrels]:
        new_list = [x for x in qrels[key] if x[0] not in empty_documents]
        if new_list != []:
            qrels[key] = new_list
            nb_paires += len(new_list)
        else:
            del qrels[key]
            del queries[key]
    
    print('There are',nb_paires,'(queries,documents) paires labelled with a relevance level of 1 or higher')
    return documents,queries,qrels





"""Separates the dataset between train, validation and test.
    
    Args:
        (dict) documents: output of clean_docs_and_build_queries
        (dict) queries: output of clean_docs_and_build_queries
        (dict) qrels: output of build_qrels
        
    Returns:
        (list) train: list of queries ids in the training set
        (list) validation: list of queries ids in the validation set
        (list) test: list of queries ids in the test set
        
"""
def build_train_validation_test(queries,validation_part,test_part):
    nb_queries = len(queries)
    list_ids = [key for key in queries]
    random.shuffle(list_ids)
    validation = list_ids[:validation_part]
    test = list_ids[validation_part:validation_part+test_part]
    train = list_ids[validation_part+test_part:]
    return train,validation,test



"""Saves queries and documents in a csv format compatible with matchzoo:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) documents: output of delete_empty
        (dict) queries: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""
def save_csv(output_dir,documents,queries,train,validation,test):
    
    index = pd.Index([key for key in documents],name = 'id_right')
    d = {"text_right":[documents[key] for key in documents]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/documents.csv')
    
    index = pd.Index([key for key in train],name = 'id_left')
    d = {"text_left":[queries[key] for key in train]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/train/queries.csv')
    
    index = pd.Index([key for key in validation],name = 'id_left')
    d = {"text_left":[queries[key] for key in validation]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/validation/queries.csv')
    
    index = pd.Index([key for key in test],name = 'id_left')
    d = {"text_left":[queries[key] for key in test]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/test/queries.csv')

    
    

"""Saves queries and documents in json format:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) documents: output of delete_empty
        (dict) queries: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""
def save_json(output_dir,documents,queries,train,validation,test):            
    with open(output_dir + '/documents.json','w') as f:
        json.dump(documents, f)

    with open(output_dir + '/train/queries.json','w') as f:
        json.dump({key:queries[key] for key in train}, f)

    with open(output_dir + '/validation/queries.json','w') as f:
        json.dump({key:queries[key] for key in validation}, f)

    with open(output_dir + '/test.queries/json','w') as f:
        json.dump({key:queries[key] for key in test}, f)
    
    
    
"""Saves queries and documents in an xml format compatible with Terrier information retireval system:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) documents: output of delete_empty
        (dict) queries: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""
def save_xml(output_dir,documents,queries,train,validation,test):
    with open(output_dir + '/documents.xml','w') as f:
        for key,value in documents.items():
            f.write('<DOC>\n<DOCNO>' + str(key) + '</DOCNO>\n<TEXT>\n' + value + '\n</TEXT></DOC>\n')

    with open(output_dir + '/train.queries.xml','w') as f:
        for key in train:
            f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')

    with open(output_dir + '/validation.queries.xml','w') as f:
        for key in validation:
            f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')

    with open(output_dir + '/test.queries.xml','w') as f:
        for key in test:
            f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')
    
    
    
"""Saves qrels in the TREC format:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (str) file_name: name of the file
        (dict) qrels: output of delete_empty
        (list) subset: output of build_train_validation_test
                
"""    
def save_qrel(output_dir,file_name,qrels,subset):
    with open(output_dir + '/' + file_name + 'qrels','w') as f:
        for key in subset:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')



"""Saves train, validation and test qrels in the TREC format:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) qrels: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""                      
def save_all_qrel(output_dir,qrels,train,validation,test):
    save_qrel(output_dir,'train/',qrels,train)
    save_qrel(output_dir,'validation/',qrels,validation)
    save_qrel(output_dir,'test/',qrels,test)


"""Saves qrels in a csv format compatible with matchzoo:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (str) file_name: name of the file
        (dict) qrels: output of delete_empty
        (list) subset: output of build_train_validation_test
                
"""        
def save_qrel_csv(output_dir,file_name,qrels,subset):

    id_left=[]
    id_right=[]
    label=[]
    for key in subset:
        for elem in qrels[key]:
            id_left.append(key)
            id_right.append(elem[0])
            label.append(elem[1])
       
            
    d = {"id_left":id_left,"id_right":id_right,"label":label}
    pd.DataFrame(data=d).to_csv(output_dir + '/' + file_name + 'qrels.csv')
    
    

"""Saves train, validation and test qrels in a csv format compatible with matchzoo:
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) qrels: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""       
def save_all_qrel_csv(output_dir,qrels,train,validation,test):
    save_qrel_csv(output_dir,'train/',qrels,train)
    save_qrel_csv(output_dir,'validation/',qrels,validation)
    save_qrel_csv(output_dir,'test/',qrels,test)
    

    
"""Saves results of BM25 in a format compatible with trec_eval:
    
    Args:
        (str) file: path of the file where the results will be saved
        (dict) results: dictionnary of BM25 results produced by evaluate_BM25_query()
                
"""        
def save_BM25_res(file,results):
    with open(file,'w') as f:
        for key,value in results.items():
            for i,elem in enumerate(value):
                f.write(str(key) + ' Q0 ' + str(elem[0]) + ' ' + str(i) + ' ' + str(elem[1]) + ' BM25\n')
    


"""Saves the top documents returned by BM25 and their relevance level in a dataframe compatible with matchzoo:
    
    Args:
        (str) file: path of the file where the results will be saved
        (dict) results: dictionnary of BM25 results produced by evaluate_BM25_query()
        (dict) qrels : output of delete_empty
        (bool) train: indicates whether we are building the training qrels or not
                
"""          
def save_BM25_qrels_dataframe(file,results,qrels,train):
    id_left=[]
    id_right=[]
    label=[]
    for query_id,list_docs in results.items():
        dict_docs = {elem[0]:elem[1] for elem in qrels[query_id]}
        for elem in list_docs:
            rel = dict_docs.get(elem[0],0)
            id_left.append(query_id)
            id_right.append(elem[0])
            if train:
                label.append(rel)
            else:
                label.append(1)
        if not train:          
            id_left.append(query_id)
            id_right.append(query_id)      
            label.append(0)
    
    d = {"id_left":id_left,"id_right":id_right,"label":label}
    pd.DataFrame(data=d).to_csv(file)
    

    

"""Evaluate a result file given a qrel file. Evaluation metrics values are saved in a json file

Args:
    (str) eval_path: path of the file where the evaluation metrics values will be saved
    (str) qrel_path: path of the qrel file 
    (str) res_path: path of the results file
    
"""   
def evaluate(eval_path,qrel_path,res_path):
    
    measures = {"map","ndcg_cut","recall","P"}
    
    with open(qrel_path, 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)
        
    evaluator = pytrec_eval.RelevanceEvaluator(qrel,measures)

    with open(res_path, 'r') as f_run:
        run = pytrec_eval.parse_run(f_run)

    all_metrics = evaluator.evaluate(run)

    metrics = {'P_5': 0,
     'P_10': 0,
     'P_20': 0,
     'ndcg_cut_5': 0,
     'ndcg_cut_10': 0,
     'ndcg_cut_20': 0,
     'ndcg_cut_100': 0,
     'map': 0,
     'recall_100': 0}

    nb_queries = len(all_metrics)
    for key,values in all_metrics.items():
        for metric in metrics:
            metrics[metric] += values[metric]/nb_queries    
    
    with open(eval_path, 'w') as f:
        json.dump(metrics, f)



"""Run BM25 on a query :
    
    Args:
        (str) query: query
        (rank_bm25.BM25Okapi) bm25: processed corpus
        (list) doc_indexes: list of the docs ids
        (int) n: number of top documents to return 
    
    Returns:
        (list) results: sorted list of doc_ids and their scores
                
"""       
def run_BM25_query(query,bm25,doc_indexes,k):
    tokenized_query = [stemmer.stem(elem) for elem in query.split(" ") if elem not in stop_words]
    doc_scores = bm25.get_scores(tokenized_query)
    top_k = np.argsort(doc_scores)[::-1][:k]
    results = [[doc_indexes[key],doc_scores[key]] for key in top_k]
    return results



"""Run BM25 on the entire collection, save the results and the top documents :
    
    Args:
        (str) output_dir: path of the directory where the collection will be stored
        (dict) documents: output of delete_empty
        (dict) queries: output of delete_empty
        (dict) qrels: output of delete_empty
        (list) train: output of build_train_validation_test
        (list) validation: output of build_train_validation_test
        (list) test: output of build_train_validation_test
                
"""
def run_BM25_collection(output_dir,documents,queries,qrels,train,validation,test,k):
    corpus = [] 
    doc_indexes = []
    for key,value in documents.items():
        doc_indexes.append(key)
        doc = [stemmer.stem(elem) for elem in value.split(" ") if elem not in stop_words]
        corpus.append(value.split(" "))
    bm25 = BM25Okapi(corpus)
    
    print("Running BM25",flush=True)
    
    results = dict()
    for i,elem in enumerate(train):
        results[elem] = run_BM25_query(queries[elem],bm25,doc_indexes,k)
        if i%1000==0:
            print('Processing query',i,'/',len(train),flush=True)
    save_BM25_res(output_dir+'/train/BM25.res',results)
    save_BM25_qrels_dataframe(output_dir + '/train/BM25.qrels.csv',results,qrels,True)
    
    results = dict()
    for elem in validation:
        results[elem] = run_BM25_query(queries[elem],bm25,doc_indexes,k)
    save_BM25_res(output_dir+'/validation/BM25.res',results)
    save_BM25_qrels_dataframe(output_dir + '/validation/BM25.qrels.csv',results,qrels,False)
    
    results = dict()
    for elem in test:
        results[elem] = run_BM25_query(queries[elem],bm25,doc_indexes,k)
    save_BM25_res(output_dir+'/test/BM25.res',results)
    save_BM25_qrels_dataframe(output_dir + '/test/BM25.qrels.csv',results,qrels,False)

    
def main():
        
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input', nargs="?", type=str)
    parser.add_argument('-o','--output_dir', nargs="?", type=str)
    parser.add_argument('-m','--max_docs', nargs="?", type=int, default = None)
    parser.add_argument('-d','--len_doc', nargs="?", type=int, default = 200)
    parser.add_argument('-q','--len_query', nargs="?", type=int, default = None)
    parser.add_argument('-l','--min_len_doc', nargs="?", type=int, default = 200)
    parser.add_argument('-e','--min_nb_rel_doc', nargs="?", type=int, default = 5)
    parser.add_argument('-v','--validation_part', nargs="?", type=int,default = 1000)
    parser.add_argument('-t','--test_part', nargs="?", type=int,default = 1000)
    parser.add_argument('-k','--k', nargs="?", type=int,default = 100)
    parser.add_argument('-i','--title_queries', action="store_true")
    parser.add_argument('-f','--only_first_links', action="store_true")
    parser.add_argument('-s','--skip_first_sentence', action="store_true")
    parser.add_argument('-c','--lower_cased', action="store_true")
    parser.add_argument('-j','--json', action="store_true")
    parser.add_argument('-x','--xml', action="store_true")
    parser.add_argument('-b','--bm25', action="store_true")
    parser.add_argument('-r','--random_seed', nargs="?", type=int,default=27355)
    args = parser.parse_args()
        
    if not os.path.exists(args.output_dir):
        print(args.output_dir,"directory does not exist.\nCreating",args.output_dir, 'directory',flush=True)
        os.mkdir(args.output_dir)
        os.mkdir(args.output_dir + '/train')
        os.mkdir(args.output_dir + '/validation')
        os.mkdir(args.output_dir + '/test')
    
    random.seed(args.random_seed)
    
    print("Reading wikiextractor file",flush=True)
    documents,documents_ids = read_wikiextractor(args.input,
                                                 args.min_len_doc,
                                                 args.max_docs)
    print(len(documents),"documents have more than",args.min_len_doc,"tokens")
    
    print("Building qrels",flush=True)
    qrels = build_qrels(documents,
                        documents_ids,
                        args.len_doc,
                        args.min_nb_rel_doc,
                        args.only_first_links)
    
    print(len(qrels),"qrels have been built",flush=True)
        
    print("Cleaning queries and documents",flush=True)
    documents,queries = clean_docs_and_build_queries(qrels,
                                                    documents,
                                                    args.len_doc,
                                                    args.len_query,
                                                    args.skip_first_sentence,
                                                    args.title_queries,
                                                    args.lower_cased)
    
    print('Removing empty documents and queries',flush=True)
    documents,queries,qrels = delete_empty(documents,queries,qrels)
    
    train,validation,test = build_train_validation_test(queries,args.validation_part,args.test_part)
    
    if args.json:
        print('Saving collection with json format',flush=True)
        save_json(args.output_dir,documents,queries,train,validation,test)
    
    elif args.xml:
        print('Saving collection with xml format',flush=True)
        save_xml(args.output_dir,documents,queries,train,validation,test)
    
    else: 
        print('Saving collection with csv format',flush=True)
        save_csv(args.output_dir,documents,queries,train,validation,test)

    save_all_qrel(args.output_dir,qrels,train,validation,test)
    
    if args.bm25:
        print('Building index',flush=True)
        run_BM25_collection(args.output_dir,documents,queries,qrels,train,validation,test,args.k)

        print('Evaluating BM25 results',flush=True)
        evaluate(args.output_dir + '/train/BM25.metrics.json',
                 args.output_dir + '/train/qrels',
                 args.output_dir + '/train/BM25.res')

        evaluate(args.output_dir + '/validation/BM25.metrics.json',
                 args.output_dir + '/validation/qrels',
                 args.output_dir + '/validation/BM25.res')

        evaluate(args.output_dir + '/test/BM25.metrics.json',
                 args.output_dir + '/test/qrels',
                 args.output_dir + '/test/BM25.res')

if __name__ == "__main__":
    main()
