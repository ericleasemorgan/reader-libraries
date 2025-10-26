#!/usr/bin/env bash

# dei.sh - a front-end to rag-against-many.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 26, 2025 - the fit continues


# configure
RAG='./bin/rag-agaist-many.py'
QUERY='diversity equity inclusion DEI'
QUESTION='What role does DEI play in libraries and librarianship?'

# do the work and done
$RAG "$QUERY" "$QUESTION"
exit
