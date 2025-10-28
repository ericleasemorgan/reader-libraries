#!/usr/bin/env python

# summary-to-kaiku.py - given a few input, output a poem

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 27, 2025 - in yet another fit of creativity; 'bought a house today


# configure
DEPTH           = 128
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTSYSTEM    = 'You are a very helpful librarian, and you respond in the form of a haiku.'

# require
from reader_libraries import Carrel, Searcher, Citations, Summarizer, Elaborator
from sys              import argv, exit

# get input
if len( argv ) != 4 : exit( "Usage: " + argv[ 0 ] + " <key> <name> <query>" )
key    = argv[ 1 ]
name   = argv[ 2 ]
query  = argv[ 3 ]

# initialize
journal = Carrel()
journal.configure( key, name )

# search, get the results, and transform them into a paragraph
engine    = Searcher()
results   = engine.search( journal, query, DEPTH )
paragraph = Citations( results ).to_paragraph()

# summarize the paragraph
prompt  = PROMPTSUMMARIZE % ( paragraph )
system  = PROMPTSYSTEM
summary = Summarizer().summarize( LLM, prompt, system  )
	
# output and done
print( ( summary[ 'response' ] ) )
exit()
