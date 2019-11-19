import os
import json
import argparse
import scipy.stats
import pytrec_eval
import matchzoo as mz

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', nargs="?", type=str)
    args = parser.parse_args()
    
    config = json.load(open(args.config,'r'))

    IR_models = [mz.models.list_available()[i] for i in config["index_mz_models"]]

    with open(config["collection_path"] + '/test/qrels', 'r') as f_qrel:
        qrel = pytrec_eval.parse_qrel(f_qrel)

    evaluator = pytrec_eval.RelevanceEvaluator(qrel, set(config["measures"]))

    bm25_res = json.load(open(config["collection_path"] + '/test/' + 'BM25.metrics.json','r'))

    with open(config["collection_path"] + '/test/' + 'BM25.res', 'r') as f_run:
        bm25_run = pytrec_eval.parse_run(f_run)

    bm25_results = evaluator.evaluate(bm25_run)

    _ = ""

    for key,value in bm25_res.items():
        if key in config["print_measures"]:
            _ += str(value)[:6] + " & "

    print('BM25 & ' + _[:-2] + '\\\\')

    all_res = dict()
    for model_class in IR_models:

        validation_path = config["collection_path"] + '/validation/' + model_class.__name__
        test_path = config["collection_path"] + '/test/' + model_class.__name__

        if os.path.exists(validation_path) and os.path.exists(test_path):
            best_model = ""
            best_metric = 0
            for file in os.listdir(validation_path):
                if '.json' in file:
                    val_res = json.load(open(validation_path + '/' + file,'r'))
                    if val_res[config["optim_measure"]] > best_metric:
                        best_model = file
                        best_metric = val_res[config["optim_measure"]]

            test_res = json.load(open(test_path + '/' + best_model,'r'))
            all_res[model_class.__name__] = [best_model,test_res]

            with open(config["collection_path"] + '/test/' + model_class.__name__ + '/' + best_model[:-12] + 'res', 'r') as f_run:
                run = pytrec_eval.parse_run(f_run)

            results = evaluator.evaluate(run)

            query_ids = list(set(bm25_results.keys()) & set(results.keys()))

            _ = ""

            for key,value in test_res.items():
                if key in config["print_measures"]:
                    bm25_scores = [bm25_results[query_id][key] for query_id in query_ids]
                    scores = [results[query_id][key] for query_id in query_ids]
                    test = scipy.stats.ttest_rel(bm25_scores, scores)
                    _ += str(value)[:6]
                    if test[0] < 0:
                        if test[1] < 0.01/len(config["print_measures"]):
                            _ += "\\textsuperscript{\\textbf{++}}"
                        elif test[1] < 0.05/len(config["print_measures"]):
                            _ += "\\textsuperscript{\\textbf{+}}"

                    else:
                        if test[1] < 0.01/len(config["print_measures"]):
                            _ += "\\textsuperscript{\\textbf{-\,-}}"
                        elif test[1] < 0.05/len(config["print_measures"]):
                            _ += "\\textsuperscript{\\textbf{-}}"

                    _ +=  " & "

            print(model_class.__name__ + ' & ' + _[:-2] + '\\\\' )

if __name__ == "__main__":
    main()