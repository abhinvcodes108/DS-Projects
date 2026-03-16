Information Retrieval Assignment, README

1) Overview

This project implements a small IR pipeline that:

* loads queries and documents,

* preprocesses and indexes the collection,

* generates candidates (NL, Boolean, wildcard),

* ranks candidates (BM25 by default; TF-IDF also supported in code),

* writes a run file for evaluation,

* computes MAP against the provided dev relevance judgments.

2) Setup  
Requirements

* Python: 3.9+ (tested on 3.10/3.11)

* Packages:

* beautifulsoup4 (used for text cleaning),

* Everything else is from the Python standard library.

* Install (optional, if bs4 is not present):

* pip install beautifulsoup4

* Repo paths used by scripts

* Documents: data/dev/documents.jsonl (JSON Lines; one {"id": ..., "text": ...} per line)

* Queries: data/dev/queries.json (JSON array of {"qid": "...", "query": "..."})

* Judgments: data/dev/relevance_judge.json (used by evaluator; do not change path)

* Runs output: runs/*.json (created automatically)

* Cache (index package): cache/unified_package.pkl.gz (created automatically)

3) How to run  
A) Produce a run (end-to-end)  
python system/search_system.py data/dev/queries.json data/dev/documents.jsonl runs/run_default.json


* Loads documents and queries,

* Preprocesses and rebuilds the index package,

* Generates candidates for each query,

* Ranks (BM25 default),

* Writes runs/run_default.json.

B) Compute MAP  
python metrics/eval_map.py

* Evaluates the most recent run files against data/dev/relevance_judge.json,

* Prints MAP (e.g., ~0.586 on the dev set).

* Optional variants (no flags needed)

* Lightweight query expansion:

* python system/search_system.py data/dev/queries.json data/dev/documents.jsonl runs/run_query_expansion.json

* Extra-aggressive cleaning:

* python system/search_system.py data/dev/queries.json data/dev/documents.jsonl runs/run_data_clean.json

Modes are auto-detected from the output filename. run_default.json indicates the baseline.

4) Expected inputs and outputs  
Input formats

documents.jsonl (JSON Lines)

{"id": 2, "text": "The bank offers small business loans ..."}  
{"id": 3, "text": "Crisis management in the financial sector ..."}

queries.json (JSON array)

[  
  {"qid": "Q1", "query": "small business banking"},  
  {"qid": "Q2", "query": "(bank AND loan) OR credit"}  
]

Run file (output)

runs/run_*.json (JSON array)

[  
  {  
    "qid": "Q1",  
    "doc_ids": ["289", "472", "109", "..."],  
    "scores": [12.31, 11.07, 9.85, ...]  
  },  
  ...  
]

Notes:

* Top-10 per query (or fewer if there are fewer candidates),

* doc_ids and scores are aligned and sorted by descending score.

5) Query language (Task 2)

Supported:

Natural language (default):  
e.g., banking services for small business

Boolean with precedence NOT > AND > OR, plus parentheses:  
bank AND loan  
(bank AND loan) OR credit  
bank AND NOT student

Quoted phrase (exact): "financial crisis"

Wildcard (prefix, standalone):  
bank*, financ*

(Do not mix with AND/OR in the same query)

Notes:

* Operators are case-insensitive (and/AND/And all work).

* Standalone unary NOT X is not supported; use A AND NOT B or A NOT B.

* Malformed structured queries produce a warning and return 0 candidates for that qid (the run still completes).

6) Ranking (Task 3)

* The default method inside ranking/rankers.py is BM25 with standard parameters (k1, b) and length normalization using the cached avgdl.

* TF-IDF is available in the ranker if you switch the method argument in the code.


8) Files created

cache/unified_package.pkl.gz — rebuilt index package (auto, created automatically)

runs/run_*.json — per-run results (auto, created automatically)

You can delete them anytime (they’ll be recreated on the next run):  
rm -rf cache  
rm -f runs/*.json
