wget https://dumps.wikimedia.org/enwiki/20191101/enwiki-20191101-pages-articles-multistream.xml.bz2

bzip2 -d enwiki-20191101-pages-articles-multistream.xml.bz2

python wikiextractor/WikiExtractor.py enwiki-20191101-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > enwiki.json

rm enwiki-20191101-pages-articles-multistream.xml

python build_wikIR.py -in enwiki.json -o $1 -title -first -skip -low -bm25

rm wiki.json
