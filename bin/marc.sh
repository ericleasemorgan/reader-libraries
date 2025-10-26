#!/usr/bin/env bash

# marc.sh - a front-end to rag-against-many.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 26, 2025 - the fit continues


# configure
RAG='./bin/rag-agaist-many.py'
QUERY='library catalogs discovery systems marc linked data'
QUESTION='What are the advantages and disadvantages of using MARC or linked data in the creation and maintence of library catalogs or discovery systems?'

# do the work and done
$RAG "$QUERY" "$QUESTION"
exit
