wget https://dumps.wikimedia.org/enwiki/20191101/enwiki-20191101-pages-articles-multistream.xml.bz2

bzip2 -d enwiki-20191101-pages-articles-multistream.xml.bz2

python wikiextractor/WikiExtractor.py enwiki-20191101-pages-articles-multistream.xml --output - --bytes 100G --links --quiet --json > enwiki.json

rm enwiki-20191101-pages-articles-multistream.xml

python build_wikIR.py --input enwiki.json --output_dir $1/wikIR1k --max_docs 370000 --validation_part 100 --test_part 100 -tfscb

python build_wikIR.py --input enwiki.json --output_dir $1/wikIR59k --validation_part 1000 --test_part 1000 -tfscb

rm enwiki.json
