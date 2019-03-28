wget https://dumps.wikimedia.org/enwiki/20190301/enwiki-20190301-pages-articles-multistream.xml.bz2

bzip2 -d enwiki-20190301-pages-articles-multistream.xml.bz2

python wikiextractor/WikiExtractor.py enwiki-20190301-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > wiki.json

rm enwiki-20190301-pages-articles-multistream.xml

python build_wikIR.py -in wiki.json -o $1

rm wiki.json