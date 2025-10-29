#!/usr/bin/env bash

# oss.sh - a front-end to rag-against-many.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 26, 2025 - the fit continues


# configure
RAG='./bin/rag-against-many.py'
QUERY='open source software librarians'
QUESTION='To what degree should librarians know how to write open source software?'

# do the work and done
$RAG "$QUERY" "$QUESTION"
exit
