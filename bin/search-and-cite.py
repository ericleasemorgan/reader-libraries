#!/usr/bin/env python

# search-and-cite.py - given a key and a query, search and ouput the citations in JSON form
# sample usage: ./bin/search-and-cite.py code4lib 'digital libraries' | jq | less

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# November 1, 2025 - practicing with the new library


# configure
DEPTH = 8

# require
from reader_libraries import Carrel, Searcher, Citations
from sys              import argv, exit
from json             import dumps

# get input
if len( argv ) != 3 : exit( "Usage: " + argv[ 0 ] + " <key> <query>" )
key   = argv[ 1 ]
query = argv[ 2 ]

# initialize, search, and get the citations
journal   = Carrel( key, '-' )
results   = Searcher().search( journal, query, DEPTH )
citations = Citations( results ).to_citations( journal )

# ouptut and done
print( dumps( citations ) )
exit
