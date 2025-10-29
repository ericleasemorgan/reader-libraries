#!/usr/bin/env python

# rag-against-one-and-summarize.py - given a key, a name, and a query, search and summarize

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 26, 2025 - in a fit of creativity
# October 28, 2025 - updated for the updated version of the underlying module


# configure
DEPTH           = 8
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSYSTEM    = 'You are a university professor, and you respond in four sentences.'

# require
from reader_libraries import Carrel, Searcher, Citations
from ollama           import generate
from sys              import argv, exit

# get input
if len( argv ) != 4 : exit( "Usage: " + argv[ 0 ] + " <key> <name> <query>" )
key   = argv[ 1 ]
name  = argv[ 2 ]
query = argv[ 3 ]

# initialize output
print( '   journal: %s' % ( name ) )
print( '     query: %s' % ( query ) )

# initialize
journal = Carrel( key, name )

# search, get the results, and transform them into a paragraph
results   = Searcher().search( journal, query, DEPTH )
paragraph = Citations( results ).to_paragraph()

# summarize the paragraph
prompt  = PROMPTSUMMARIZE % ( paragraph )
summary = generate( LLM, prompt, system=PROMPTSYSTEM )
	
# output and done
print( '   summary: %s' % ( summary[ 'response' ] ) )
exit()
