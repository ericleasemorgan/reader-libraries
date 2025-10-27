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
DEPTH           = 32
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSYSTEM    = 'You are a university professor, and you respond in one or two sentences.'

# require
from reader_libraries import carrel, searcher, citations, summarizer, elaborator
from sys              import argv, exit

# get input
if len( argv ) != 3 : exit( "Usage: " + argv[ 0 ] + " <query> <question>" )
query    = argv[ 1 ]
question = argv[ 2 ]

# initialize output
print( 'Question - %s\n' % ( question ) )

# loop through each carrel
for item in CARRELS :

	# initialize
	journal = carrel( item[ 'key' ], item[ 'name' ] )

	# search, get the results, and transform them into a paragraph
	engine    = searcher()
	results   = engine.search( journal, query, DEPTH )
	paragraph = citations( results ).to_paragraph()
	
	# summarize the paragraph
	prompt  = PROMPTSUMMARIZE % ( paragraph )
	summary = summarizer().summarize( LLM, prompt, PROMPTSYSTEM  )
	
	# elaborate on the paragraph by addressing a question against it
	prompt      = PROMPTELABORATE % ( question, paragraph )
	elaboration = elaborator().elaborate( LLM, prompt, PROMPTSYSTEM )
	
	# output and done
	print( '  %s\n' % ( journal.name ) )
	print( '    Summary - %s\n' % ( summary[ 'response' ] ) )
	print( '    Answer - %s\n'% ( elaboration[ 'response' ] ) )
		
# done
exit()
