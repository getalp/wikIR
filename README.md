# wikIR
A python tool for building a large scale Wikipedia-based Information Retrieval dataset

# Requirements
  * Python 3.6+
  * [pytrec_eval](https://github.com/cvangysel/pytrec_eval) to evaluate the runs 
  * [nltk](https://www.nltk.org/) library to use PorterStemmer and perform stopword removal
  * [Pandas](https://pandas.pydata.org) library to be able to save the dataset as a dataframe compatible with [MatchZoo](https://github.com/NTMC-Community/MatchZoo) 
  * [Rank-BM25](https://github.com/dorianbrown/rank_bm25) as a first efficient ranking stage if you want to use [MatchZoo](https://github.com/NTMC-Community/MatchZoo) 
# Installation

```bash
git clone --recurse-submodules https://github.com/getalp/wikIR.git
cd wikIR
pip install -r requirements.txt
```

# Usage

  * Download and extract a XML wikipedia dump file from [here](https://dumps.wikimedia.org/backup-index.html) 
  * Use [Wikiextractor](https://github.com/attardi/wikiextractor) to get the text of the wikipedia pages in a signle json file, for example : 
```bash
python wikiextractor/WikiExtractor.py input --output - --bytes 100G --links --quiet --json > output.json
```
Where input is the XML wikipedia dump file and output is the output in json format

  * Call our script
```
python build_wikIR.py [-in,--input] [-out,--output_dir] 
                      [-maxd,--max_docs] [-ld,--len_doc] [-lq,--len_query] [-mlen,--min_len_doc]
                      [-mrel,--min_nb_rel_doc] [-val,--validation_part] [-test,--test_part]
                      [-k,--k] [-title,--title_queries] [-first,--only_first_links] 
                      [-skip,--skip_first_sentence] [-low,--lower_cased] [-json,--json] 
                      [-bm25,--bm25] [-rand,--random_seed] 
```

```
arguments : 

    [-in,--input]                 The json file produced by wikiextractor
    
    [-out,--output_dir]           Directory where the collection will be stored

optional argument:

    [-maxd,--max_docs]            Maximum number of documents in the collection
                                  Default value None

    [-ld,--len_doc]               Number of max tokens in documents
                                  Default value None: all tokens are preserved
                                  
    [-lq,--len_query]             Number of max tokens in queries
                                  Default value None: all tokens are preserved
    
    [-mlen,--min_len_doc]         Mininum number of tokens required for an article 
                                  to be added to the dataset as a document
                                  Default value 200
    
    [-mrel,--min_nb_rel_doc]      Mininum number of relevant documents required for 
                                  a query to be added to the dataset
                                  Default value 5
    
    [-val,--validation_part]      Number of queries in the validation set
                                  Default value 1000
    
    [-test,--test_part]           Number of queries in the test set
                                  Default value 1000
    
    [-title,--title_queries]      If used, queries are build using the title of 
                                  the article 
                                  If not used, queries are build using the first
                                  sentence of the article
    
    [-first,--only_first_links]   If used, only the links in the first sentence of 
                                  articles will be used to build qrels
                                  If not used, all links up to len_doc token will
                                  be used to build qrels
    
    [-skip,--skip_first_sentence] If used, the first sentence of articles is not 
                                  used in documents
    
    [-low,--lower_cased]          If used, all characters are lowercase
    
    [-json,--json]                If used, documents and queries are saved in json
                                  If not used, documents and queries are saved in
                                  csv as dataframes compatible with matchzoo
                                  
    [-bm25,--bm25]                If used, perform and save results of BM25 ranking 
                                  model on the collection
                                
    [-k,--k]                      If BM25 is used, indicates the number of documents 
                                  per query saved 
                                  Default value 100
    
    [-rand,--random_seed]         Random seed
                                  Default value 27355
        
```


# Example on 01/11/2019 English Wikipedia (take several hours)

Clone our repository

```bash
git clone --recurse-submodules https://github.com/getalp/wikIR.git
```
Download the english wikipedia dump from 01/11/2019
```bash
wget https://dumps.wikimedia.org/enwiki/20191101/enwiki-20191101-pages-articles-multistream.xml.bz2
```

Extract the file 
```bash
bzip2 -dk enwiki-20191101-pages-articles-multistream.xml.bz2
```

Use Wikiextractor (ignore the WARNING: Template errors in article)
```bash
python wikIR/wikiextractor/WikiExtractor.py enwiki-20191101-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > enwiki.json
```

Use wikIR builder
```bash
python wikIR/build_wikIR.py -in enwiki.json -out data -ld 200 -title -first -skip -low -bm25
```

### :warning: **Do not forget to delete the dowloaded and intermediary files** :warning:

```bash
rm enwiki-20190301-pages-articles-multistream.xml.bz2
rm enwiki-20190301-pages-articles-multistream.xml
rm wiki.json
```

# Reproducibility

To reproduce the same datasets we used in our experiment just call the following script


```bash
./reproduce.sh COLLECTION_PATH
```

COLLECTION_PATH is the directory where the datasets will be stored

# Details
  * Our script takes **≈30 minutes** to build the collection on an Intel(R) Xeon(R) CPU E5-2623 v4 @ 2.60GHz
  * **≈ 5.8M queries** are extracted from the english wikipedia dump of 01/03/2019
  * Right now, our tokenizer was mainly designed for english and does not work on non-latin alphabets
  * We delete all non alphanumeric characters
  * All tokens are lowercased 
  * The data construction process is similar to [1] and [2] :
    * Only the first 200 words of each article is used to build the documents
    * The first sentence of each article is used to build the queries
    * We assign a **relevance of 2** if the query and document were extracted from the **same article**
    * We assign a **relevance of 1** if there is a **link from the article of the query to the article of the document**
    * We assign a **relevance of 0** to other documents


# Statistics of the wikIR english collection

| #Documents  | #Queries | #rels | Avg rel2 | Avg rel1 |
| :-: | :-: | :-: | :-: | :-: |
| 5.8M  | 5.8M | 52.2M | 1 | 8 |

There is as much queries as documents.

Each query is associated with only one document of relevance = 2 

On average each query has 8 documents of relevance = 1

*****

Results were computed with [pytrec_eval](https://github.com/cvangysel/pytrec_eval) [3]

[1] Shota Sasaki, Shuo Sun, Shigehiko Schamoni, Kevin Duh, and Kentaro Inui. 2018. Cross-lingual learning-to-rank with shared representations

[2] Shigehiko Schamoni, Felix Hieber, Artem Sokolov, and Stefan Riezler. 2014. Learning translational and knowledge-based similarities from relevance rankings for cross-language retrieval.

[3] Christophe Van Gysel and Maarten de Rijke. 2018. Pytrec_eval: An ExtremelyFast Python Interface to trec_eval.
