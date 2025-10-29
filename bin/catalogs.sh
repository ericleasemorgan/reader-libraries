#!/usr/bin/env bash

# catalogs.sh - a front-end to rag-against-many.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 26, 2025 - the fit continues


# configure
RAG='./bin/rag-against-many.py'
QUERY='library catalogs discovery systems'
QUESTION='What are the similarities and differences between library catalogs and discovery systems?'

# do the work and done
$RAG "$QUERY" "$QUESTION"
exit
