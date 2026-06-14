#!/usr/bin/env python

# morphadorn.py - given a TEI file, mark-up sentences complete with words, lemmas, and parts-of-speech

# Eric Lease Morgan <eric_morgan@infomotions.com>
# November 24, 2018 - first cut but took all day to write
# December  1, 2018 - added lemma and pos to punctuation; added identifiers; on a plane to Oslo
# June     12, 2026 - migrating to the Reader, sort of

# configure
MODEL    = 'en_core_web_sm'
ENCODING = 'UTF-8'
TMP      = './tmp'
STYLE    = './etc/add-id.xsl'
MAX      = 1600000

# require
from lxml import etree
import spacy
import sys
import os
import random
import string

# sanity check
if len( sys.argv ) != 2 :
	sys.stderr.write( 'Usage: ' + sys.argv[ 0 ] + " <file>\n" )
	exit()

# initialize
file = sys.argv[ 1 ] 
tei = etree.parse( file )
nlp = spacy.load( MODEL )
nlp.max_length = MAX

sys.stderr.write( file + '\n' )

# process each paragraph
for paragraph in tei.xpath( '//body//p | //body//l' ) :

	# re-initialize
	document       = nlp( paragraph.text )
	paragraph.text = ''
	
	# process each sentence in the given paragraph
	for sentence in document.sents :

		# re-)initialize
		sentence = sentence.as_doc()
		s        = etree.SubElement( paragraph, 's' )
		s.text   = sentence.text
					
# write out to a temporary file, add id attributes, format, and done; hacky
tmp = TMP + '/' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + '.xml'
tei.write( tmp, xml_declaration=True, encoding=ENCODING )
os.system( "xsltproc %s %s > %s" % ( STYLE, tmp, file ) ) 
exit()
