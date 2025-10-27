#!/usr/bin/env python

# rag.py - given (quite) a number of configurations, search an index and report on the results

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 26, 2025 - in a fit of creativity


# configure
CARRELS         = [
                    { 'key':'ital',     'name':'ITAL' },
                    { 'key':'ariadne',  'name':'Ariadne' },
                    { 'key':'dlib',     'name':'DLib Magazine' },
                    { 'key':'code4lib', 'name':'Code4Lib Journal' }
                  ]
DEPTH           = 64
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSYSTEM    = 'You are a university professor, and you respond in two or three paragraphs.'

# require
from reader_libraries import carrel, searcher, citations, summarizer, elaborator
from sys              import argv, exit

# get input
if len( argv ) != 4 : exit( "Usage: " + argv[ 0 ] + " <key> <name> <query>" )
key   = argv[ 1 ]
name  = argv[ 2 ]
query = argv[ 3 ]

# initialize output
print( 'Query - %s\n' % ( query ) )

# initialize
journal = carrel( key, name )

# search, get the results, and transform them into a paragraph
engine    = searcher()
results   = engine.search( journal, query, DEPTH )
paragraph = citations( results ).to_paragraph()

# summarize the paragraph
prompt  = PROMPTSUMMARIZE % ( paragraph )
summary = summarizer().summarize( LLM, prompt, PROMPTSYSTEM  )
	
# output and done
print( '  %s\n' % ( journal.name ) )
print( '    Summary - %s\n' % ( summary[ 'response' ] ) )
#print( '    Answer - %s\n'% ( elaboration[ 'response' ] ) )
	
# done
exit()
