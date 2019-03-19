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
python build_wikIR.py [--json_file] [--output_dir] [--random_seed]

arguments : 
    --json_file        the json file produced by wikiextractor
    --output_dir       the directory where the collection will be stored

optional argument:
    --random_seed      the random seed to split the data in train/validation/test

```

# Example 
```bash
#Download the wikipedia dump in swahili
wget https://dumps.wikimedia.org/swwiki/20190301/swwiki-20190301-pages-articles-multistream.xml.bz2

#Extract the file
bzip2 -dk swwiki-20190301-pages-articles-multistream.xml.bz2

#Use Wikiextractor
python WikiExtractor.py swwiki-20190301-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > wiki.json

#Use wikIR builder
python build_wikiIR.py --json_file wiki.json --output_dir wikIR

```

# Details
  * Right now our tool is designed to treat english wikipedia
  * We delete all non alphanumeric characters
  * The data construction process is similar to [1] and [2] :
  
  
[1] Shota Sasaki, Shuo Sun, Shigehiko Schamoni, Kevin Duh, and Kentaro Inui. 2018. Cross-lingual learning-to-rank with shared representations
