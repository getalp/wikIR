# wikIR
A python tool for building a large scale Wikipedia-based Information Retrieval dataset

# Requirements
  * Python 3.6+
  * [Wikiextractor](https://github.com/attardi/wikiextractor)
  * If working with high ressource language (e.g. english) you need **20GB of RAM** to process the json file returned by  [Wikiextractor](https://github.com/attardi/wikiextractor)

# Installation
Clone [Wikiextractor](https://github.com/attardi/wikiextractor) repository

```bash
git clone https://github.com/attardi/wikiextractor.git
```

Clone our repository

```bash
git clone https://github.com/getalp/wikIR.git
```

# Usage

  * Download and extract a XML wikipedia dump file from [here](https://dumps.wikimedia.org/backup-index.html) 
  * Use [Wikiextractor](https://github.com/attardi/wikiextractor) to get the text of the wikipedia pages in a signle json file, for example : 
```bash
python WikiExtractor.py input --output - --bytes 100G --links --quiet --json > output.json
```
Where input is the XML wikipedia dump file and output is the output in json format

  * Call our script
```
python build_wikIR.py [--json_file] [--output_dir] [--random_seed] [--xml_output]

arguments : 
    --json_file                the json file produced by wikiextractor
    --output_dir               the directory where the collection will be stored

optional argument:
    --random_seed              the random seed to split the data in train/validation/test
    --xml_output               if used, the documents and queries will be saved in xml format
                               compatible with Terrier Information Retrieval System
    
output : our tool creates the 7 following files in the output directory

    documents.json             Documents
    
    train.queries.json         Train queries
    validation.queries.json    Validation queries
    test.queries.json          Test queries
    
    train.qrel                 Train relevance judgments
    validation.qrel            Validation relevance judgments
    test.qrel                  Test relevance judgments
    
```

# Quick Example

Clone [Wikiextractor](https://github.com/attardi/wikiextractor) repository

```bash
git clone https://github.com/attardi/wikiextractor.git
```

Clone our repository

```bash
git clone https://github.com/getalp/wikIR.git
```

Download the swahili wikipedia dump from 01/03/2019 
```bash
wget https://dumps.wikimedia.org/swwiki/20190301/swwiki-20190301-pages-articles-multistream.xml.bz2
```

Extract the file
```bash
bzip2 -dk swwiki-20190301-pages-articles-multistream.xml.bz2
```

Use Wikiextractor
```bash
python wikiextractor/WikiExtractor.py swwiki-20190301-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > wiki.json
```

Use wikIR builder
```bash
python wikIR/build_wikIR.py --json_file wiki.json --output_dir wikIR
```

# Example on English Wikipedia (may take several hours)

Clone [Wikiextractor](https://github.com/attardi/wikiextractor) repository

```bash
git clone https://github.com/attardi/wikiextractor.git
```

Clone our repository

```bash
git clone https://github.com/getalp/wikIR.git
```

Download the english wikipedia dump from 01/03/2019 (16.9 GB file)
```bash
wget https://dumps.wikimedia.org/enwiki/20190301/enwiki-20190301-pages-articles-multistream.xml.bz2
```

Extract the file (produces a 71.3 GB file)
```bash
bzip2 -dk enwiki-20190301-pages-articles-multistream.xml.bz2
```

Use Wikiextractor (produces a 17.2 GB file)
```bash
python wikiextractor/WikiExtractor.py enwiki-20190301-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > wiki.json
```

Use wikIR builder (produces a 5.9 GB directory)
```bash
python wikIR/build_wikIR.py --json_file wiki.json --output_dir wikIR
```

:warning: **Do not forget to delete the dowloaded and intermediary files** :warning:

# Details
  * Our script takes **35 minutes** to build the collection on an Intel(R) Xeon(R) CPU E5-2623 v4 @ 2.60GHz
  * Right now, our tokenizer was mainly designed for english and does not work on non-latin alphabets
  * We delete all non alphanumeric characters
  * All tokens are lowercased 
  * The data construction process is similar to [1] and [2] :
    * Only the first 200 words of each article is used to build the documents
    * The first sentence of each article is used to build the queries
  
[1] Shota Sasaki, Shuo Sun, Shigehiko Schamoni, Kevin Duh, and Kentaro Inui. 2018. Cross-lingual learning-to-rank with shared representations

[2] Shigehiko Schamoni, Felix Hieber, Artem Sokolov, and Stefan Riezler. 2014. Learning translational and knowledge-based similarities from relevance rankings for cross-language retrieval.
