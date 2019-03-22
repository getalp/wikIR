import json
import re
import os
import argparse
import random


def read_wikiextractor(file):
    documents = dict()
    documents_ids = dict()
    doc_id = 0
    with open(file) as f:
        for line in f:
            article = json.loads(line)
            text = article['text']
            documents_ids[article['title']] = doc_id
            documents[doc_id]=text
            doc_id += 1
    return documents,documents_ids,doc_id


def build_qrels(documents,documents_ids):
    qrels = dict()
    for key,value in documents.items():
        list_qrels = re.findall(r'(?:href=")([^"]+)', value)
        qrels[key] = []
        qrels[key].append([key,2])
        linked_docs = set([documents_ids[elem.replace('%20',' ')] for elem in list_qrels if elem.replace('%20',' ') in documents_ids])
        linked_docs.discard(key)
        for document in linked_docs:
            qrels[key].append([document,1])
    return qrels

def clean_docs_and_build_queries(documents):
    queries = dict()
    regex = re.compile('[^a-zA-Z0-9]')
    for key,value in documents.items():
        document = re.sub('<[^>]+>', '', value)
        end_of_title = document.find('\n')
        document = document[end_of_title:]
        first_sentence_location = document.find('.')
        query = document[0:first_sentence_location]
        documents[key] = ' '.join(regex.sub(' ', document).lower().split()[0:200])
        queries[key] = ' '.join(regex.sub(' ', query).lower().split())
    return documents,queries
    
def delete_empty(documents,queries,qrels):
    
    empty_documents = dict()
    for key in [elem for elem in documents]:
        if documents[key].isspace() or not documents[key]:
            del documents[key]
            empty_documents[key] = None
            
    for key in [elem for elem in queries]:
        if queries[key].isspace() or not queries[key]:
            del queries[key]
            del qrels[key]
    
    for key in [elem for elem in qrels]:
        new_list = [x for x in qrels[key] if x[0] not in empty_documents ]
        if new_list != []:
            qrels[key] = new_list
        else:
            del qrels[key]
    return documents,queries,qrels

def build_train_validation_test(queries,train_part,validation_part,test_part):
    nb_queries = len(queries)
    print('There is',nb_queries,'queries')
    list_ids = [key for key in queries]
    random.shuffle(list_ids)
    train_size = int(train_part*nb_queries)
    validation_size = int(validation_part*nb_queries)
    test_size = int(test_part*nb_queries)
    train = list_ids[:train_size]
    validation = list_ids[train_size:train_size+validation_size]
    test = list_ids[train_size+validation_size:train_size+validation_size+test_size]
    other = list_ids[train_size+validation_size+test_size:]
    return train,validation,test,other

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
    

def save_json(output_dir,documents,queries,train,validation,test):            
    with open(output_dir + '/documents.json','w') as f:
        json.dump(documents, f)

    with open(output_dir + '/train.queries.json','w') as f:
        json.dump({key:queries[key] for key in train}, f)

    with open(output_dir + '/validation.queries.json','w') as f:
        json.dump({key:queries[key] for key in validation}, f)

    with open(output_dir + '/test.queries.json','w') as f:
        json.dump({key:queries[key] for key in test}, f)
   
    

def save_qrel(output_dir,qrels,train,validation,test):
    with open(output_dir + '/train.qrel','w') as f:
        for key in train:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
                
    with open(output_dir + '/validation.qrel','w') as f:
        for key in validation:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
                
    with open(output_dir + '/test.qrel','w') as f:
        for key in test:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
                
   
                
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-in','--input', nargs="?", type=str)
    parser.add_argument('-o','--output_dir', nargs="?", type=str)
    parser.add_argument('-t','--train_part', nargs="?", type=float,default = 0.001)
    parser.add_argument('-v','--validation_part', nargs="?", type=float,default = 0.0001)
    parser.add_argument('-test','--test_part', nargs="?", type=float,default = 0.0001)
    parser.add_argument('-xml','--xml_output', action="store_true")
    parser.add_argument('-both','--both_output', action="store_true")
    parser.add_argument('-r','--random_seed', nargs="?", type=int,default=27355)
    args = parser.parse_args()
    
    if args.train_part <= 0 or args.validation_part <= 0 or args.test_part <= 0 or args.train_part + args.validation_part + args.test_part > 1.0:
        raise ValueError("train_part, validation_part and test_part must be postitive floats and their sum must be smaller than 1")
    
    if not os.path.exists(args.output_dir):
        print(args.output_dir,'does not exist.\nCreating',args.output_dir)
        os.mkdir(args.output_dir)
    
    random.seed(args.random_seed)
    
    print('Reading input file')    
    documents,documents_ids,doc_id = read_wikiextractor(args.input)
            
    print('Extracting links and building qrels')
    qrels = build_qrels(documents,documents_ids)
    
    print('Cleaning documents and building queries')
    documents,queries = clean_docs_and_build_queries(documents)
    
    print('Removing empty documents and queries')
    documents,queries,qrels = delete_empty(documents,queries,qrels)
    
    train,validation,test = build_train_validation_test(queries,args.train_part,args.validation_part,args.test_part)
    
    print('Saving documents')
    
    if args.both_output:
        save_xml(args.output_dir,documents,queries,train,validation,test)
        save_json(args.output_dir,documents,queries,train,validation,test)
        
    else:
        if args.xml_output:
            save_xml(args.output_dir,documents,queries,train,validation,test)
        else:
            save_json(args.output_dir,documents,queries,train,validation,test)
    
    save_qrel(args.output_dir,qrels,train,validation,test)
    
        
if __name__ == "__main__":
    main()
