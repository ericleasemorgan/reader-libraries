#!/usr/bin/env python

# search.py

from rrag import Searcher, Citations, Cacher
from sys  import argv, exit

# get input
if len( argv ) != 4 : exit( 'Usage: ' + argv[ 0 ] + " <carrel> <query> <depth>" )
carrel = argv[ 1 ]
query  = argv[ 2 ]
depth  = argv[ 3 ]

# initialize, search, get results, get sentences, and format
searcher  = Searcher()
results   = searcher.search( carrel, query, depth )
citations = Citations( results )
sentences = citations.to_sentences()
paragraph = ' '.join( sentences )

# cache the results
Cacher().cache( 'results', results )

# done
print( paragraph )
exit()
