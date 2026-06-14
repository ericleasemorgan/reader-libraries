#!/usr/bin/env python

# vectorize.py - given a carrel, create a database of sentences and their embeddings
# see: https://github.com/asg017/sqlite-vec/

# Eric Lease Morgan <emorgan@nd.edu>
# (c) University of Notre Dame; distributed under a GNU Public License

# May   16, 2025 - with a lack of hearing, a FOC, and because the CRC machines were under maintence
# May   17, 2025 - migrated to Euclidian (VEC_DISTANCE_L2) distances
# May   22, 2025 - added title of item and item (sentence) number to database
# June   7, 2025 - normalized sentences so they are always strings
# July   4, 2025 - using a new embedder; actually moved to Ollama
# March 30, 2026 - started caching vectors as a file
# March 31, 2026 - started caching vectors in the database
# April  2, 2026 - scaled back to older embedder because nomic mysteriously broke;cached vectors to a file
 

# MODEL:SIZE - locusai/multi-qa-minilm-l6-cos-v1:768:384
# MODEL:SIZE - nomic-embed-text:768

# configure
MODEL    = 'locusai/multi-qa-minilm-l6-cos-v1'
CREATE   = "CREATE TABLE sentences (title TEXT, idx TEXT, sentence TEXT, embedding FLOAT[384] CHECK (TYPEOF(embedding)=='blob' AND VEC_LENGTH(embedding)==384))"
INSERT   = "INSERT INTO sentences (title, idx, sentence, embedding) VALUES (?, ?, ?, ?)"
PATTERN  = '*.snt'
LIBRARY  = 'localLibrary'
DATABASE = 'sentences.db'
CACHE    = 'sentences'
VECTORS  = 'vectors.pkl'

# require
from numpy      import array
from ollama     import embed, ResponseError
from pandas     import read_csv
from pathlib    import Path
from pickle     import dump
from rdr        import configuration, ETC
from re         import sub
from sqlite_vec import load
from sqlite3    import connect
from struct     import pack
from sys        import stderr, argv, exit
from typing     import List

# get input
if len( argv ) != 2 : exit( 'Usage: ' + argv[ 0 ] + " <carrel>" )
carrel = argv[ 1 ]

# serializes a list of floats into a compact "raw bytes" format; makes things more efficient?
def serialize( vector: List[ float ] ) -> bytes : return pack( "%sf" % len( vector ), *vector )

# initialize
stderr.write( "Initializing\n" )
cache = configuration( LIBRARY )/carrel/CACHE

# (re-)create database
stderr.write( "Creating database\n" )
database = configuration( LIBRARY )/carrel/ETC/DATABASE
database.unlink( missing_ok=True )
database = connect( database )
database.enable_load_extension( True )
load( database )
database.execute( CREATE )

# process each text in the given carrel
stderr.write( "Indexing texts\n" )
count = 0
for index, file in enumerate( cache.glob( PATTERN ) ):
	
	# increment and debug
	title =  file.stem
	count += 1
	stderr.write( '  %s (%s)\n' % ( file, str( count ) ) )
		
	# re-initialize and normalize
	records   = read_csv( file )
	sentences = list( records[ 'sentence' ] )
	sentences = [ str( sentence ) for sentence in sentences ]
	indexes   = list( records[ 'idx' ] )
	indexes   = [ str( index ) for index in indexes ]
	
	# vectorize the sentences; cpu-intensive
	try :
	
		# do the work
		embeddings = embed( model=MODEL, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]
	
		# process each sentence/embeddding combination
		#item = 0
		for sentence, index, embedding in zip( sentences, indexes, embeddings ) :
			
			# do the inserts
			#item += 1
			database.execute( INSERT, [ title, index, sentence, serialize( embedding ) ] )	

	except ResponseError as e:

		stderr.write(f"Status Code: {e.status_code}; Error: {e.error}; Call Eric?\n")
		continue
	
# commit and close
database.commit()
database.close()

# cache vectors to the carrel as a file; the etc directory is becoming bloated
#with open( configuration( LIBRARY )/carrel/ETC/VECTORS, 'wb' ) as handle : dump( array( embeddings ), handle )

# done
exit()

