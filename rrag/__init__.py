'''A retrieval-augmented generation (RAG) system applied against Distant Reader study carrels'''

# Eric Lease Morgan <emorgan@nd.edu>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June  2, 2026 - first investigations
# June 11, 2026 - added bunches o' stuff in previous days; made Reformatter work


# configure prompts
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSUMMARIZE = 'Summarize: %s. Respond in plain text only, no markdown formatting.'
PROMPTSYSTEM    = 'You are %s, and you respond in %s.'

# configure models
LLM      = 'minimax-m3:cloud'
EMBEDDER = 'locusai/multi-qa-minilm-l6-cos-v1'

# configure path names
RRAGETC   = 'etc'
RRAGCACHE = 'cache'

# configure file names
CACHEDCARREL    = 'cached-carrel.txt'
CACHEDLENGTH    = 'cached-length.txt'
CACHEDPERSONA   = 'cached-persona.txt'
CACHEDQUERY     = 'cached-query.txt'
CACHEDQUESTION  = 'cached-question.txt'
CACHEDSENTENCES = 'cached-sentences.txt'
CACHEDPROMPT    = 'system-prompt.txt'
CACHEDRESULTS   = 'cached-results.csv'
DATABASE        = 'sentences.db'
INDEXJSON       = 'index.json'
LENGTHS         = 'lengths.txt'
PERSONAS        = 'personas.txt'
LIBRARY         = 'localLibrary'

# require
from os.path                  import dirname
from pandas                   import DataFrame, read_csv
from pathlib                  import Path
from rdr                      import configuration, ETC
from typing                   import List
import numpy                  as     np

# initialize
cwd     = Path( dirname( __file__ ) )
library = configuration ( LIBRARY )


class Settings :

	def __init__( self ) : return( None )

	def set( self, type, value ) :
	
		if type == 'persona' :
			with open( cwd/RRAGCACHE/CACHEDPERSONA, 'w' ) as handle : handle.write( value )

		if type == 'length' :
			with open( cwd/RRAGCACHE/CACHEDLENGTH, 'w' ) as handle : handle.write( value )

	def get( self, type ) :
	
		if type == 'persona' :
			with open( cwd/RRAGCACHE/CACHEDPERSONA ) as handle : result = handle.read().rstrip()
		
		elif type == 'length' :
			with open( cwd/RRAGCACHE/CACHEDLENGTH ) as handle : result = handle.read().rstrip()
				
		return( result )
		
			
class Summarizer :

	def __init__( self ) : return( None )

	def summarize( self ) : 
	
		# require
		from ollama import generate

		# initialize
		sentences  = Citations( read_csv( cwd/RRAGCACHE/CACHEDRESULTS ) ).to_sentences()
		paragraphs = ' '.join( sentences )
		prompt     = PROMPTSUMMARIZE % ( paragraphs )
		system     = PROMPTSYSTEM % ( Settings().get( 'persona' ), Settings().get( 'length' ) )
		
		# do the work, get the response, and done
		result   = generate( LLM, prompt, system=system )
		response = result[ 'response' ]
		return( response  )


class Elaborate :

	def __init__( self ) : return( None )

	def elaborate( self, request ) : 
	
		# require
		from ollama import generate

		# initialize
		sentences  = Citations( read_csv( cwd/RRAGCACHE/CACHEDRESULTS ) ).to_sentences()
		paragraphs = ' '.join( sentences )
		prompt     = PROMPTELABORATE % ( request, paragraphs )
		system     = PROMPTSYSTEM % ( Settings().get( 'persona' ), Settings().get( 'length' ) )
		
		# do the work, get the response, and done
		result   = generate( LLM, prompt, system=system )
		response = result[ 'response' ]
		return( response  )


class Cacher :

	def __init__( self ) : return( None )
	
	def cache( self, type, results ) :
	
		if type == 'results' : 
			with open( cwd/RRAGCACHE/CACHEDRESULTS, 'w' ) as handle : handle.write( results.to_csv( index = False ) )


class Searcher : 
	
	def __init__( self ) : return( None )
		
	def search( self, carrel, query, depth ) :
			
		# configure
		COLUMNS = [ 'titles', 'idx', 'sentences', 'distances' ]
		SELECT  = "SELECT title, idx, sentence, VEC_DISTANCE_L2(embedding, ?) AS distance FROM sentences ORDER BY distance LIMIT ?"
			
		# require
		from ollama     import embed
		from sqlite_vec import load as vecload
		from sqlite3    import connect
		from natsort    import natsorted
		
		# update
		self.query = query
		self.depth = depth
		
		# initialize
		database = connect( library/carrel/ETC/DATABASE, check_same_thread=False )
		database.enable_load_extension( True )
		vecload( database )
				
		# vectorize query and search; get a set of matching records
		query   = embed( model=EMBEDDER, input=query ).model_dump( mode='json' )[ 'embeddings' ][ 0 ]
		records = database.execute( SELECT, [ self.serialize( query ), depth ] ).fetchall()
	
		# process each result; create a list of items
		items = []
		for record in records :
		
			# parse
			title    = record[ 0 ]
			idx      = record[ 1 ]
			sentence = record[ 2 ]
			distance = record[ 3 ]
			
			# update
			items.append( [ title, idx, sentence, distance ] )
		
		# create a dataframe of the sentences, sort by title
		items = DataFrame( items, columns=COLUMNS )
		items = items.sort_values( [ 'titles', 'idx' ] )

		# cache the results and return them
		Cacher().cache( 'results', items )
		return( items )


	def serialize( self, vector: List[float]) -> bytes : 
		'''Serialize a list of floats into a compact "raw bytes" format'''
		from struct                   import pack
		return pack( "%sf" % len( vector ), *vector )
	
		
class Citations :

	def __init__( self, dataframe ) : self.original = dataframe
	
	def to_sentences( self ) :
	
		# create a list of sentences and done
		sentences = []
		for index, row in self.original.iterrows() : sentences.append( row[ 'sentences' ] )
		return( sentences )

			
	def to_citations( self, carrel ) :
			
		# require
		from json import load
		
		# initialize
		items = self.original
		
		# create a list of items sorted by the number of times they were cited
		items = items.groupby( [ 'titles' ], as_index=False )[ 'sentences' ].count()
		items = items.sort_values( 'sentences', ascending=False )
		items = [ row.tolist() for index, row in items.iterrows() ]	
				
		# process each item; transform the list of items into a list of pseudo-citations
		citations = []
		with open ( library/carrel/INDEXJSON ) as handle : bibliographics = load( handle )		
		for item in items :
		
			# parse
			id    = item[ 0 ]
			count = item[ 1 ]
						
			# loop through all bhe bibliogrpahics; ought to be a dictionary, not a list
			for bibliographic in bibliographics :
				
				# match
				if str( bibliographic[ 'id' ] ) == str( id ) :
					
					# parse, update, and break
					author    = bibliographic[ 'author' ]
					title     = bibliographic[ 'title' ]
					date      = bibliographic[ 'date' ]
					summary   = bibliographic[ 'summary' ]
					keywords  = bibliographic[ 'keywords' ]
					extension = bibliographic[ 'extension' ]
					citations.append( { 'id':id, 'author':author, 'title': title, 'date':date, 'summary':summary, 'keywords':keywords, 'extension':extension, 'count':count } )
					break
					
		# done
		return( citations )


class Reformatter :

	def __init__( self ) : return( None )

	def reformat( self ) :

		# configure
		PSIZE = 16
		ORDER = 2

		# require
		from ollama                   import embed
		from scipy.signal             import argrelextrema
		from sklearn.metrics.pairwise import cosine_similarity
		
		# read the cache
		sentences = Citations( read_csv( cwd/RRAGCACHE/CACHEDRESULTS ) ).to_sentences()
				
		# vectorize and activate similaritites; for longer sentences increase the value of PSIZE
		embeddings = embed( model=EMBEDDER, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]
	
		# try to compute similarities
		try               : similarities = self.activate_similarities( cosine_similarity(embeddings), p_size=PSIZE )
		except ValueError : return( None )
			
		# compute minmimas
		minmimas = argrelextrema( similarities, np.less, order=ORDER )
			
		# Get the order number of the sentences which are in splitting points
		splits = [ minmima for minmima in minmimas[ 0 ] ]
			
		# Create empty string
		text = ''
		for index, sentence in enumerate( sentences ) :
		
			# check if sentence is a minima (splitting point)
			if index in splits : text += f'\n\n{sentence} '
			else               : text += f'{sentence} '
	
		# done
		return( text )
		
		
	def activate_similarities( self, similarities:np.array, p_size=10 )->np.array :
		''''Don't really understand what this function does'''
	
		# To create weights for sigmoid function we first have to create space. P_size will determine number of sentences used and the size of weights vector.
		x = np.linspace( -10, 10, p_size )
	
		# Then we need to apply activation function to the created space
		y = np.vectorize(self.rev_sigmoid) 
	
		# Because we only apply activation to p_size number of sentences we have to add zeros to neglect the effect of every additional sentence and to match the length ofvector we will multiply
		activation_weights = np.pad(y(x),(0,similarities.shape[0]-p_size))
	
		# Take each diagonal to the right of the main diagonal
		diagonals = [similarities.diagonal(each) for each in range(0,similarities.shape[0])]
	
		# Pad each diagonal by zeros at the end. Because each diagonal is different length we should pad it with zeros at the end
		diagonals = [np.pad(each, (0,similarities.shape[0]-len(each))) for each in diagonals]
	
		# Stack those diagonals into new matrix
		diagonals = np.stack(diagonals)
	
		# Apply activation weights to each row. Multiply similarities with our activation.
		diagonals = diagonals * activation_weights.reshape(-1,1)
	
		# Calculate the weighted sum of activated similarities
		activated_similarities = np.sum(diagonals, axis=0)
	
		# done
		return( activated_similarities )

	def rev_sigmoid( self, x:float )->float :
		''''Don't understand what this function does'''
	
		from math  import exp

		return ( 1 / ( 1 + exp( 0.5*x ) ) )


