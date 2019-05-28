import json
import re
import os
import argparse
import random
import pandas as pd

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


def get_queries_subset(qrels,documents,nb_queries):
    subset = random.sample(list(qrels), nb_queries)
    qrels = {key:qrels[key] for key in subset}
    set_relevant_docs = set(elem[0] for key,value in qrels.items() for elem in value)
    documents = {key:value for key,value in documents.items() if key in set_relevant_docs}
    return qrels,documents

def clean_docs_and_build_queries(qrels,documents,len_doc):
    queries = dict()
    regex = re.compile('[^a-zA-Z0-9]')
    for key,value in documents.items():
        document = re.sub('<[^>]+>', '', value)
        end_of_title = document.find('\n')
        document = document[end_of_title:]
        first_sentence_location = document.find('.')
        documents[key] = ' '.join(regex.sub(' ', document).lower().split()[0:len_doc])
        if key in qrels:
            query = document[0:first_sentence_location]
            queries[key] = ' '.join(regex.sub(' ', query).lower().split())
    return documents,queries
    
def delete_empty(documents,queries,qrels):
    nb_empty = 0
    empty_documents = set()
    for key in [elem for elem in documents]:
        if documents[key].isspace() or not documents[key]:
            del documents[key]
            nb_empty += 1 
            empty_documents.add(key)
            
    print(nb_empty,'empty documents have been deleted')
   
    
    nb_empty = 0
    for key in [elem for elem in queries]:
        if queries[key].isspace() or not queries[key]:
            del queries[key]
            del qrels[key]
            nb_empty += 1 
            
    print(nb_empty,' empty queries have been deleted')
    print('There is',len(documents),'documents')
    print('There is',len(queries),'queries')
    
    nb_paires = 0
    for key in [elem for elem in qrels]:
        new_list = [x for x in qrels[key] if x[0] not in empty_documents ]
        if new_list != []:
            qrels[key] = new_list
            nb_paires += len(new_list)
        else:
            del qrels[key]
    
    print('There is',nb_paires,'(queries,documents) paires labelled with a relevance level of 1 or higher')
    return documents,queries,qrels

def build_train_validation_test(queries,train_part,validation_part,test_part):
    nb_queries = len(queries)
    list_ids = [key for key in queries]
    random.shuffle(list_ids)
    train_size = int(train_part*nb_queries)
    validation_size = int(validation_part*nb_queries)
    test_size = int(test_part*nb_queries)
    train = list_ids[:train_size]
    validation = list_ids[train_size:train_size+validation_size]
    test = list_ids[train_size+validation_size:train_size+validation_size+test_size]
    other = list_ids[train_size+validation_size+test_size:]
    return train,validation,test

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
        
        
def save_csv(output_dir,documents,queries,train,validation,test):
    
    index = pd.Index([key for key in documents],name = 'id_right')
    d = {"text_right":[documents[key] for key in documents]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/documents.csv')
    
    index = pd.Index([key for key in train],name = 'id_left')
    d = {"text_left":[queries[key] for key in train]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/train.queries.csv')
    
    index = pd.Index([key for key in validation],name = 'id_left')
    d = {"text_left":[queries[key] for key in validation]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/validation.queries.csv')
    
    index = pd.Index([key for key in test],name = 'id_left')
    d = {"text_left":[queries[key] for key in test]}
    pd.DataFrame(data=d,index=index).to_csv(output_dir + '/test.queries.csv')
        

                
def generate_irrelevant_docs(qrel,documents_id,nb_non_relevant):
    list_irrelevant_docs = []
    while len(list_irrelevant_docs) < nb_non_relevant:
        doc = random.choice(documents_id)
        if doc not in qrel and doc not in list_irrelevant_docs:
            list_irrelevant_docs.append(doc)
    return list_irrelevant_docs
        
def save_qrel(output_dir,file_name,qrels,subset,documents,nb_non_relevant):
    documents_id = [key for key in documents]
    with open(output_dir + '/' + file_name + '.qrel','w') as f:
        for key in subset:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
            if nb_non_relevant > 0 :
                for elem in generate_irrelevant_docs(qrels[key],documents_id,nb_non_relevant):
                    f.write(str(key) + '\t0\t' + str(elem) + '\t' + '0' + '\n')

def save_all_qrel(output_dir,qrels,train,validation,test,documents,nb_non_relevant):
    save_qrel(output_dir,'train',qrels,train,documents,nb_non_relevant)
    save_qrel(output_dir,'validation',qrels,validation,documents,nb_non_relevant)
    save_qrel(output_dir,'test',qrels,test,documents,nb_non_relevant)


def save_qrel_csv(output_dir,file_name,qrels,subset,documents,nb_non_relevant):

    documents_id = [key for key in documents]
    
    id_left=[]
    id_right=[]
    label=[]
    for key in subset:
        for elem in qrels[key]:
            id_left.append(key)
            id_right.append(elem[0])
            label.append(elem[1])
        if nb_non_relevant > 0 :
            for elem in generate_irrelevant_docs(qrels[key],documents_id,nb_non_relevant):
                id_left.append(key)
                id_right.append(elem)
                label.append(0)
            
    d = {"id_left":id_left,"id_right":id_right,"label":label}
    pd.DataFrame(data=d).to_csv(output_dir + '/' + file_name + '.qrel.csv')
    
    
    
def save_all_qrel_csv(output_dir,qrels,train,validation,test,documents,nb_non_relevant):
    save_qrel_csv(output_dir,'train',qrels,train,documents,nb_non_relevant)
    save_qrel_csv(output_dir,'validation',qrels,validation,documents,nb_non_relevant)
    save_qrel_csv(output_dir,'test',qrels,test,documents,nb_non_relevant)
    
    
                
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-in','--input', nargs="?", type=str)
    parser.add_argument('-o','--output_dir', nargs="?", type=str)
    parser.add_argument('-q','--nb_queries', nargs="?", type=int, default = -1)
    parser.add_argument('-n','--nb_non_relevant', nargs="?", type=int, default = 20)
    parser.add_argument('-l','--len_doc', nargs="?", type=int, default = 200)
    parser.add_argument('-t','--train_part', nargs="?", type=float,default = 0.8)
    parser.add_argument('-v','--validation_part', nargs="?", type=float,default = 0.1)
    parser.add_argument('-test','--test_part', nargs="?", type=float,default = 0.1)
    parser.add_argument('-xml','--xml_output', action="store_true")
    parser.add_argument('-csv','--csv_output', action="store_true")
    parser.add_argument('-all','--all_output', action="store_true")
    parser.add_argument('-r','--random_seed', nargs="?", type=int,default=27355)
    args = parser.parse_args()
    
    if args.train_part <= 0 or args.validation_part <= 0 or args.test_part <= 0 or args.train_part + args.validation_part + args.test_part != 1.0:
        raise ValueError("train_part, validation_part and test_part must be postitive floats and their sum must be equal to 1")
    
    if not os.path.exists(args.output_dir):
        print(args.output_dir,'does not exist.\nCreating',args.output_dir)
        os.mkdir(args.output_dir)
    
    random.seed(args.random_seed)
    
    print('Reading input file')    
    documents,documents_ids,doc_id = read_wikiextractor(args.input)
            
    print('Extracting links and building qrels')
    qrels = build_qrels(documents,documents_ids)
    
    if args.nb_queries != -1 and args.nb_queries < len(qrels):
        print('Extracting subset of',args.nb_queries,'queries')
        qrels,documents = get_queries_subset(qrels,documents,args.nb_queries)
        
    print('Cleaning documents and building queries')
    documents,queries = clean_docs_and_build_queries(qrels,documents,arg.len_doc)
    
    print('Removing empty documents and queries')
    documents,queries,qrels = delete_empty(documents,queries,qrels)
    
    train,validation,test = build_train_validation_test(queries,args.train_part,args.validation_part,args.test_part)
    
    print('Saving documents')
    
    if args.all_output:
        save_xml(args.output_dir,documents,queries,train,validation,test)
        save_json(args.output_dir,documents,queries,train,validation,test)
        save_csv(args.output_dir,documents,queries,train,validation,test)
        save_all_qrel_csv(args.output_dir,qrels,train,validation,test,documents,args.nb_non_relevant)
        save_all_qrel(args.output_dir,qrels,train,validation,test,documents,args.nb_non_relevant)
        
    elif args.csv_output:
        save_csv(args.output_dir,documents,queries,train,validation,test)
        save_all_qrel_csv(args.output_dir,qrels,train,validation,test,documents,args.nb_non_relevant)
        
    else:
        if args.xml_output:
            save_xml(args.output_dir,documents,queries,train,validation,test)
        else:
            save_json(args.output_dir,documents,queries,train,validation,test)

        save_all_qrel(args.output_dir,qrels,train,validation,test,documents,args.nb_non_relevant)

        
if __name__ == "__main__":
    main()
