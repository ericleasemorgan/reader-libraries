#!/usr/bin/env python

# summary-to-kaiku.py - given a few input, output a poem

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 27, 2025 - in yet another fit of creativity; 'bought a house today
# October 28, 2025 - while washing a $300,000 load of laundry
# October 31, 2025 - updated to use "finished" library


# configure
DEPTH           = 32
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTSYSTEM    = 'You are child in the eight grade, and you respond in the form of a haiku.'

# require
from reader_libraries import Carrel, Searcher, Citations
from ollama           import generate
from sys              import argv, exit

# get input
if len( argv ) != 4 : exit( "Usage: " + argv[ 0 ] + " <key> <name> <query>" )
key    = argv[ 1 ]
name   = argv[ 2 ]
query  = argv[ 3 ]

# initialize
journal = Carrel( key, name )

# search, get the results, and transform them into a paragraph
results   = Searcher().search( journal, query, DEPTH )
sentences = Citations( results ).to_sentences()
paragraph = ' '.join( sentences )

# summarize the paragraph
prompt  = PROMPTSUMMARIZE % ( paragraph )
system  = PROMPTSYSTEM
summary = generate( LLM, prompt, system=system  )
	
# output and done
print( ( summary[ 'response' ] ) )
exit()
