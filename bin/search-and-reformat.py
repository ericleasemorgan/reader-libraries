#!/usr/bin/env python

# search-and-reformat.py - given a key and a query, search and compute small(er) paragraphs

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# November 1, 2025 - practicing with the new library


# configure
DEPTH    = 32
EMBEDDER = 'nomic-embed-text'

# require
from reader_libraries import Carrel, Searcher, Citations, Reformatter
from sys              import argv, exit

# get input
if len( argv ) != 3 : exit( "Usage: " + argv[ 0 ] + " <key> <query>" )
key   = argv[ 1 ]
query = argv[ 2 ]

# initialize
journal = Carrel( key, '-' )

# search, get the results, and reformat the results
results        = Searcher().search( journal, query, DEPTH )
sentences      = Citations( results ).to_sentences()
transformation = Reformatter().reformat( sentences, EMBEDDER )

# output and done
print( '      key: %s' % ( key ) )
print( '    query: %s' % ( query ) )
print( '  results: %s' % ( transformation ) )
exit
