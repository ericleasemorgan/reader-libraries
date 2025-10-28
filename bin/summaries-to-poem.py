#!/usr/bin/env python

# rag.py - given (quite) a number of configurations, search an index and report on the results

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 26, 2025 - in a fit of creativity


# configure
DEPTH           = 64
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTSYSTEM    = 'You are a university professor, and you respond in %s.'

# require
from reader_libraries import Carrel, Searcher, Citations, Summarizer, Elaborator
from sys              import argv, exit

# get input
if len( argv ) != 5 : exit( "Usage: " + argv[ 0 ] + " <key> <name> <query> <length>" )
key    = argv[ 1 ]
name   = argv[ 2 ]
query  = argv[ 3 ]
length = argv[ 4 ]

# initialize
journal = Carrel()
journal.configure( key, name )

# search, get the results, and transform them into a paragraph
engine    = Searcher()
results   = engine.search( journal, query, DEPTH )
paragraph = Citations( results ).to_paragraph()

# summarize the paragraph
prompt  = PROMPTSUMMARIZE % ( paragraph )
system  = PROMPTSYSTEM % ( length) 
summary = Summarizer().summarize( LLM, prompt, system  )
	
# output and done
print( ( summary[ 'response' ] ) )
exit()
