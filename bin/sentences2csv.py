#!/usr/bin/env python

# sentences2csv.py - given a TEI file, output a CSV file of sentences

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - first cut
# June 13, 2026 - output to the file system; blazingly fast!?


# configure
COLUMNS = [ 'item', 'idx', 'sentence' ]
CACHE     = 'sentences'
EXTENSION = '.snt'
LIBRARY   = 'localLibrary'
PATTERN   = '*.xml'
XML       = 'xml'

# require
from lxml    import etree
from pathlib import Path
from sys     import stderr, argv, exit
from pandas  import DataFrame
from rdr     import configuration, TXT
from shutil  import rmtree

# get input
if len( argv ) != 2 : exit( 'Usage: ' + argv[ 0 ] + " <carrel>" )
carrel = argv[ 1 ]

# initialize
carrel = configuration( LIBRARY )/carrel
cache  = carrel/CACHE

# make sane
rmtree( cache, ignore_errors=True )
cache.mkdir()

# find and process each file in the given carrel
for file in ( carrel/XML ).glob( PATTERN ) :

	# debug
	stderr.write( str( file ) + '\n' )
	
	# initialize
	item = Path( file ).stem
	xml  = etree.parse( file )

	# find and process each sentence in the given file; create a list of records
	records = []
	for sentence in xml.xpath( '//body//s' ) :

		# update the list of records
		records.append( [ item, sentence.xpath( './@xml:id' )[ 0 ], sentence.text ] )
			
	# create a dataframe from the records, output, and done
	sentences = DataFrame( records, columns=COLUMNS )
	with open( cache/( item + EXTENSION ), 'w' ) as handle : handle.write( sentences.to_csv( index=False ) )

# done
exit()


