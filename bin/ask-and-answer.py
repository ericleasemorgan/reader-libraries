#!/usr/bin/env python

# ask-and-answer.py - given a few configurations, address a given question

# Eric Lease Morgan <emorgan@nd.edu>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 25, 2025 - first cut; while Douglas is visiting


# configure
CARREL   = 'ital'
QUERY    = 'library catalogs discovery systems'
DEPTH    = '64'
QUESTION = 'How are library catalogs different from discovery systems?'
PERSONA  = 'a child in the eigth grade'
LENGTH   = 'a single paragraph'

# require
from reader_libraries import search, summarize, elaborate, cache_persona, cache_length

# set up the work
sentences = search( CARREL, QUERY, DEPTH )
cache_persona( PERSONA )
cache_length( LENGTH )

# do the work
answer = elaborate( QUESTION )

# output and done
print( '%s\n\n%s\n' % ( QUESTION, answer[ 'response' ] ) )
exit()
