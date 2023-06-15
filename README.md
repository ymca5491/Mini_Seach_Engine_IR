# Mini Search Engine
## Introduction
This is a mini search engine designed for wikipedia, with BM25 used for ranking and support for field search(title, body). For now it only has CLI.
## Usage 
To use this mini search engine:
* First install the needed packages use `pip install -r requirments.txt'
* Switch to the project directory
* Download the dumped file of wikipedia with `wget -P dump https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract.xml.gz`
* Run `myWikiIndexer.py`, `k-way-merge.py` sequencially
* Run `search.py` to start the CLI, and remember to type as "field:keyword" when you want to search by fields