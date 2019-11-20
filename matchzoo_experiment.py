import os
import json
import argparse
import build_wikIR
import pandas as pd
import matchzoo as mz



"""Loads the train validation and tests sets of the collection into matchzoo DataPacks.
    
    Args:
        (str) collection_path: path of the collection directory
        
    Returns:
        (matchzoo.data_pack.data_pack.DataPack) train_raw: train set 
        (matchzoo.data_pack.data_pack.DataPack) validation_raw: validation set
        (matchzoo.data_pack.data_pack.DataPack) test_raw: test set

"""

def load_wikIR(collection_path):
    
    left = pd.read_csv(collection_path + '/train/queries.csv',index_col='id_left')
    right = pd.read_csv(collection_path + '/documents.csv',index_col='id_right')
    relation = pd.read_csv(collection_path + '/train/BM25.qrels.csv',index_col=0)
    train_raw = mz.DataPack(left=left,right=right,relation=relation)
    
    left = pd.read_csv(collection_path + '/validation/queries.csv',index_col='id_left')
    right = pd.read_csv(collection_path + '/documents.csv',index_col='id_right')
    relation = pd.read_csv(collection_path + '/validation/BM25.qrels.csv',index_col=0)
    validation_raw = mz.DataPack(left=left,right=right,relation=relation)
    
    left = pd.read_csv(collection_path + '/test/queries.csv',index_col='id_left')
    right = pd.read_csv(collection_path + '/documents.csv',index_col='id_right')
    relation = pd.read_csv(collection_path + '/test/BM25.qrels.csv',index_col=0)
    test_raw = mz.DataPack(left=left,right=right,relation=relation)
    
    return train_raw,validation_raw,test_raw


"""Returns the scores givne by a model on the validation or test datapacks.
    
    Args:
        (matchzoo.models) model: matchzoo model
        (matchzoo.data_generator.data_generator.DataGenerator) set_gen: set on which the model will be evaluated
        
    Returns:
        (list) results: a sorted list of tuples (query_id,document_ids,scores) 
        
"""

def predict(model,set_gen):
    set_x, _ = set_gen[:]
    nb_elems = len(set_x['id_left'])
    scores = model.predict(set_x).reshape(nb_elems).tolist()
    q_ids = set_x['id_left'].reshape(nb_elems).tolist()
    d_ids = set_x['id_right'].reshape(nb_elems).tolist()
    results = [[q,d,s] for (q,d,s) in zip(q_ids,d_ids,scores)]
    results.sort(key=lambda tup: -tup[2])
    results.sort(key=lambda tup: tup[0])
    return results
    
    
"""Saves results in a format compatible with trec_eval:
    
    Args:
        (str) file: path of the file where the results will be saved
        (dict) results: output of predict
        (str) name: name of the model
                
"""  
def save_results(file,results,name):
    with open(file,'w') as f:
        counter = -1
        q_id = results[0][0]
        for elem in results:
            if elem[0]==q_id: 
                counter+=1
            else:
                counter = 0
                q_id = elem[0]
            f.write(str(q_id) + ' Q0 ' + str(elem[1]) + ' ' + str(counter) + ' ' + str(elem[2]) + ' ' + name + '\n')
            

"""Compute the scores and save the results and the metrics of a matchzoo model:
    
    Args:
        (matchzoo.models) model: matchzoo model
        (matchzoo.data_generator.data_generator.DataGenerator) set_gen: set on which the model will be evaluated
        (str) model_path: path of the directory where the results will be saved
        (int) run: indicates the current run
        (int) epoch: indicates the current epoch
        (str) collection_path: path ofthe collection
        (str) qrels_path: path of the qrels
""" 
def evaluate_and_save_results(model,set_gen,model_path,run,epoch,collection_path,qrels_path):
    
    set_results = predict(model,set_gen)
    
    save_results(model_path + '/run.' + str(run) + '.epoch.' + str(epoch) + '.res',
                                     set_results,
                                     'run.' + str(run)+ '.epoch.' + str(epoch) )
    
    build_wikIR.evaluate(model_path + '/run.' + str(run) + '.epoch.' + str(epoch) + '.metrics.json',
                         qrels_path,
                         model_path + '/run.' + str(run) + '.epoch.' + str(epoch) + '.res')

    
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', nargs="?", type=str)
    parser.add_argument('-gpu','--gpu', nargs="?", type=str, default = None)
    parser.add_argument('-runs','--nb_runs', nargs="?", type=int, default = 5)
    args = parser.parse_args()
    
    config = json.load(open(args.config,'r'))
    
    if args.gpu:
        os.environ["CUDA_VISIBLE_DEVICES"]=args.gpu
    
    train_raw,validation_raw,test_raw = load_wikIR(config["collection_path"])
    
    glove_embedding = mz.datasets.embeddings.load_glove_embedding(dimension=300)
    task = mz.tasks.Ranking(loss=mz.losses.RankCrossEntropyLoss(num_neg=4))
    IR_models = [mz.models.list_available()[i] for i in config["index_mz_models"]]
    
    for run in range(args.nb_runs):    
        for model_class in IR_models:
            print(model_class.__name__)


            validation_path = config["collection_path"] + '/validation/' + model_class.__name__

            if not os.path.exists(validation_path):
                os.mkdir(validation_path)

            test_path = config["collection_path"] + '/test/' + model_class.__name__

            if not os.path.exists(test_path):
                os.mkdir(test_path)


            preprocessor = model_class.get_default_preprocessor(
                                 fixed_length_left= 10,
                                 fixed_length_right = 200,
                                 filter_mode = 'tf',
                                 filter_low_freq = 5,
                                 filter_high_freq = float('inf'),
                                 remove_stop_words = True)

            model, preprocessor, data_generator_builder, embedding_matrix = mz.auto.prepare(
                task=task,
                model_class=model_class,
                data_pack=train_raw,
                preprocessor=preprocessor,
                embedding = glove_embedding)

            train_processed = preprocessor.transform(train_raw, verbose=0)
            validation_processed = preprocessor.transform(validation_raw, verbose=0)
            test_processed = preprocessor.transform(test_raw, verbose=0)

            train_gen = data_generator_builder.build(train_processed,batch_size=64,mode='pair')
            validation_gen = data_generator_builder.build(validation_processed,mode='pair',num_neg=0,num_dup=1)
            test_gen = data_generator_builder.build(test_processed,mode='pair',num_neg=0,num_dup=1)

            evaluate_and_save_results(model,
                                      validation_gen,
                                      validation_path,
                                      run,
                                      0,
                                      config["collection_path"],
                                      config["collection_path"] + '/validation/qrels')

            evaluate_and_save_results(model,
                                      test_gen,
                                      test_path,
                                      run,
                                      0,
                                      config["collection_path"],
                                      config["collection_path"] + '/test/qrels')

            for _ in range(10):
                model.fit_generator(train_gen, epochs=2,verbose = 1)

                evaluate_and_save_results(model,
                                          validation_gen,
                                          validation_path,
                                          run,
                                          (1+_)*2,
                                          config["collection_path"],
                                          config["collection_path"] + '/validation/qrels')

                evaluate_and_save_results(model,
                                          test_gen,
                                          test_path,
                                          run,
                                          (1+_)*2,
                                          config["collection_path"],
                                          config["collection_path"] + '/test/qrels')
    
if __name__ == "__main__":
    main()