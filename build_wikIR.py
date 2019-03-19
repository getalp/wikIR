import json
import re
import os
import argparse
import random


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--json_file', nargs="?", type=str)
    parser.add_argument('--output_dir', nargs="?", type=str)
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
    
    list_ids = list(range(doc_id))
    
    print('Extracting links and building qrels')
    qrels = dict()
    for key,value in documents.items():
        list_qrels = re.findall(r'(?:href=")([^"]+)', value)
        qrels[key] = []
        qrels[key].append([key,2])
        for document in [elem.replace('%20',' ') for elem in list_qrels if elem.replace('%20',' ') in documents_ids]:
            qrels[key].append([documents_ids[document],1])
    
    print('Cleaning documents and building queries')
    regex = re.compile('[^a-zA-Z]')
    for key,value in documents.items():
        document = re.sub('<[^>]+>', '', value)
        end_of_title = document.find('\n')
        document = document[end_of_title:]
        first_sentence_location = document.find('.')
        query = document[0:first_sentence_location]
        documents[key] = ' '.join(regex.sub(' ', document).lower().split()[0:200])
        queries[key] = ' '.join(regex.sub(' ', query).lower().split()[0:200])

    
    random.shuffle(list_ids)
    
    train = list_ids[:int(0.8*(doc_id-1))]
    validation = list_ids[int(0.8*(doc_id-1)):int(0.9*(doc_id-1))]
    test = list_ids[int(0.9*(doc_id-1)):]
    
    print('Saving documents')
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
