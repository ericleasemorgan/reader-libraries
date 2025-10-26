#!/usr/bin/env python

# rag.py - given (quite) a number of configurations, search an index and report on the results

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# October 26, 2025 - in a fit of creativity


# configure
KEY             = 'dlib'
NAME            = 'DLib Magazine'
QUERY           = 'library catalogs discovery systems'
DEPTH           = 32
LLM             = 'deepseek-v3.1:671b-cloud'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSYSTEM    = 'You are %s, and you respond in %s.'
PERSONA         = 'a sophmoric college student'
LENGTH          = 'one paragraph'
QUESTION        = 'What are the differences between library catalogs and discovery systems?'

# require
from reader_libraries import carrel, searcher, citations, summarizer, elaborator

# initialize, search, and get paragraphs
carrel    = carrel( KEY, NAME )
searcher  = searcher()
results   = searcher.search( carrel, QUERY, DEPTH )
paragraph = citations( results ).to_paragraph()

# summarize
prompt  = PROMPTSUMMARIZE % ( paragraph )
system  = PROMPTSYSTEM % ( PERSONA, LENGTH )
summary = summarizer().summarize( LLM, prompt, system  )

# elaborate
prompt      = PROMPTELABORATE % ( QUESTION, paragraph )
system      = PROMPTSYSTEM % ( PERSONA, LENGTH )
elaboration = elaborator().elaborate( LLM, prompt, system )

# output and done
print( 'Journal - %s\n' % ( carrel.name ) )
print( 'Query - %s\n' % ( searcher.query ) )
print( 'Depth - %s\n' % ( searcher.depth ) )
print( 'Sentences - %s\n' % ( paragraph ) )
print( 'Summary - %s\n' % ( summary[ 'response' ] ) )
print( 'Question - %s\n'% ( QUESTION ) )
print( 'Answer - %s\n'% ( elaboration[ 'response' ] ) )
exit()
