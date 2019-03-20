import json
import re
import os
import argparse
import random


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_file', nargs="?", type=str)
    parser.add_argument('--output_dir', nargs="?", type=str)
    parser.add_argument('--xml_output', action="store_true")
    parser.add_argument('--random_seed', nargs="?", type=int,default=27355)
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        print(args.output_dir,'does not exist. Creating directory.')
        os.mkdir(args.output_dir)
    
    random.seed(args.random_seed)
    queries = dict()
    documents = dict()
    documents_ids = dict()
    doc_id = 0
    
    print('Reading json file')    
    with open(args.json_file) as f:
        for line in f:
            article = json.loads(line)
            text = article['text']
            documents_ids[article['title']] = doc_id
            documents[doc_id]=text
            doc_id += 1
            
    print('Extracting links and building qrels')
    qrels = dict()
    for key,value in documents.items():
        list_qrels = re.findall(r'(?:href=")([^"]+)', value)
        qrels[key] = []
        qrels[key].append([key,2])
        linked_docs = set([documents_ids[elem.replace('%20',' ')] for elem in list_qrels if elem.replace('%20',' ') in documents_ids])
        linked_docs.discard(key)
        for document in linked_docs:
            qrels[key].append([document,1])
    
    print('Cleaning documents and building queries')
    regex = re.compile('[^a-zA-Z0-9]')
    for key,value in documents.items():
        document = re.sub('<[^>]+>', '', value)
        end_of_title = document.find('\n')
        document = document[end_of_title:]
        first_sentence_location = document.find('.')
        query = document[0:first_sentence_location]
        documents[key] = ' '.join(regex.sub(' ', document).lower().split()[0:200])
        queries[key] = ' '.join(regex.sub(' ', query).lower().split())

    
    print('Removing empty documents and queries')
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
    
    nb_queries = len(queries)
    
    list_ids = [key for key in queries]
    
    random.shuffle(list_ids)
    
    train = list_ids[:int(0.8*(nb_queries))]
    validation = list_ids[int(0.8*(nb_queries)):int(0.9*(nb_queries))]
    test = list_ids[int(0.9*(nb_queries)):]
    
    print('Saving documents')
    
    if args.xml_output:
        with open(args.output_dir + '/documents.xml','w') as f:
            for key,value in documents.items():
                f.write('<DOC>\n<DOCNO>' + str(key) + '</DOCNO>\n<TEXT>\n' + value + '\n</TEXT></DOC>\n')
       
        with open(args.output_dir + '/train.queries.xml','w') as f:
            for key in train:
                f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')

        with open(args.output_dir + '/validation.queries.xml','w') as f:
            for key in validation:
                f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')

        with open(args.output_dir + '/test.queries.xml','w') as f:
            for key in test:
                f.write('<top>\n<num>' + str(key) + '</num><title>\n' + queries[key] + '\n</title>\n</top>\n')
    else:
        with open(args.output_dir + '/documents.json','w') as f:
            json.dump(documents, f)

        with open(args.output_dir + '/train.queries.json','w') as f:
            json.dump({key:queries[key] for key in train}, f)

        with open(args.output_dir + '/validation.queries.json','w') as f:
            json.dump({key:queries[key] for key in validation}, f)

        with open(args.output_dir + '/test.queries.json','w') as f:
            json.dump({key:queries[key] for key in test}, f)
        
    with open(args.output_dir + '/train.qrel','w') as f:
        for key in train:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
                
    with open(args.output_dir + '/validation.qrel','w') as f:
        for key in validation:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
                
    with open(args.output_dir + '/test.qrel','w') as f:
        for key in test:
            for elem in qrels[key]:
                f.write(str(key) + '\t0\t' + str(elem[0]) + '\t' + str(elem[1]) + '\n')
        
if __name__ == "__main__":
    main()
