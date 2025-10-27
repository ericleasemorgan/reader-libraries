# reader-libraries.py - an interactive index to 3,000 scholarly journal articles on the topic of digital libraries

# Eric Lease Morgan <emorgan@nd.edu>
# (c) Infomotions, LLC; distributed under a GNU Public License

# August     3, 2025 - first investigations; rooted in the non-lite version so I can share and demonstrate
# August     9, 2025 - added more things than I can count, but as of now, all functions work
# August    11, 2025 - modified so the whole thing is a package; I'm learning
# September 29, 2025 - removed "Nex steps"; while "commencing" here in the Sainte-Geneviève Library, Paris
# October   20, 2025 - added response length, I think
# October   23, 2025 - enhanced cites
# October   25, 2025 - started abstracting so I can write a command-line interface


# configure
CACHEDCARREL    = 'cached-carrel.txt'
CACHEDCITES     = 'cached-cites.txt'
CACHEDLENGTH    = 'cached-length.txt'
CACHEDPERSONA   = 'cached-persona.txt'
CACHEDQUERY     = 'cached-query.txt'
CACHEDQUESTION  = 'cached-question.txt'
CACHEDRESULTS   = 'cached-results.txt'
CARRELS         = 'carrels'
CATALOG         = 'catalog.csv'
DATABASE        = 'sentences.db'
EMBEDDER        = 'nomic-embed-text'
ETC             = 'etc'
INDEXJSON       = 'index.json'
LENGTHS         = 'lengths.txt'
LLM             = 'deepseek-v3.1:671b-cloud'
PERSONAS        = 'personas.txt'
STATIC          = 'static'
SYSTEMPROMPT    = 'system-prompt.txt'

# require
from flask                    import Flask, render_template, request
from math                     import exp
from ollama                   import embed, generate
from os.path                  import dirname
from pandas                   import DataFrame, read_csv, array
from pathlib                  import Path
from re                       import sub
from scipy.signal             import argrelextrema
from sklearn.metrics.pairwise import cosine_similarity
from sqlite_vec               import load
from sqlite3                  import connect
from struct                   import pack
from typing                   import List
import json
import numpy                  as     np

# initialize
reader = Flask( __name__ )
cwd    = Path( dirname( __file__ ) )

# home
@reader.route( "/" )
def home() : return render_template('home.htm' )

# search
@reader.route( "/search/" )
def search() :

	# get the catalog as a list of lists
	catalog = getCatalog( cwd/ETC/CATALOG )
	
	# read the cached carrel values
	carrel = Carrel()
	carrel.read()
	previousCarrel = carrel.key

	# read the cached searches values
	searcher = Searcher()
	searcher.read()
	previousQuery = searcher.query
	previousDepth = searcher.depth
		
	# get input
	carrel = request.args.get( 'carrel', '' )
	query  = request.args.get( 'query', '' )
	depth  = request.args.get( 'depth', '' )

	# return the search form
	if not carrel or not query or not depth : return render_template('search-form.htm', catalog=catalog, carrel=previousCarrel, query=previousQuery, depth=previousDepth )
			
	# split the returned carrel value (kinda dumb), create a carrel object, and cache it
	key    = carrel.split( '--' )[ 0 ]
	name   = carrel.split( '--' )[ 1 ]
	carrel = Carrel()
	carrel.configure( key, name )	
	carrel.cache()
		
	# search and cache
	citations = searcher.search( carrel, query, depth )
	paragraph = Citations( citations ).to_paragraph()
	
	# cache the search and the results
	searcher.cache()
	
	# done
	return render_template( 'search.htm', carrel=carrel.name, query=query, results=paragraph, depth=depth )



# ask; kinda messy
@reader.route("/ask/")
def ask() :

	# configure
	DEPTH = '8'
	
	# initialize; search
	carrel   = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )
	question = request.args.get( 'question', '' )
	with open( cwd/ETC/CACHEDPERSONA ) as handle : persona = handle.read()
	results  = search( carrel[ 0 ], question, DEPTH )
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )

	# initialize some more
	context = open( cwd/ETC/CACHEDRESULTS ).read()
	system  = open( cwd/ETC/SYSTEMPROMPT ).read()
	prompt  = ( PROMPTELABORATE % ( question, context ) )

	# do the work
	result = generate( LLM, prompt, system=system )

	# reformat the results
	response = sub( '\n\n', '</p><p>', result[ 'response' ] ) 
	response = '<p>' + response + '</p>'

	# done
	return render_template('elaborate.htm', results=response, question=question, persona=persona )

	
# question
@reader.route("/question/")
def question() :

	# configure
	SELECT = 'SELECT sentence FROM sentences WHERE sentence LIKE "%?" ORDER BY RANDOM() LIMIT 1'

	# initialize
	library  = cwd/STATIC/CARRELS	
	carrel   = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )
	database = connect( library/carrel[ 0 ]/DATABASE, check_same_thread=False )
	database.enable_load_extension( True )
	load( database )
	
	# do the work
	question = database.execute( SELECT ).fetchone()[ 0 ]
	
	# done
	return render_template( 'question.htm', carrel=carrel, question=question )


'''# the system's work horse
def search( carrel, query, depth ) :

	# configure
	COLUMNS  = [ 'titles', 'items', 'sentences', 'distances' ]
	SELECT   = "SELECT title, item, sentence, VEC_DISTANCE_L2(embedding, ?) AS distance FROM sentences ORDER BY distance LIMIT ?"

	# initialize
	library  = cwd/STATIC/CARRELS		
	database = connect( library/carrel/ETC/DATABASE, check_same_thread=False )
	database.enable_load_extension( True )
	load( database )

	# cache the query for possible future reference
	with open( cwd/ETC/CACHEDQUERY, 'w' ) as handle : handle.write( '\t'.join( [ query, depth ] ) )

	# vectorize query and search; get a set of matching records
	query   = embed( model=EMBEDDER, input=query ).model_dump( mode='json' )[ 'embeddings' ][ 0 ]
	records = database.execute( SELECT, [ serialize( query ), depth ] ).fetchall()
	
	# process each result; create a list of sentences
	sentences = []
	for record in records :
	
		# parse
		title    = record[ 0 ]
		item     = record[ 1 ]
		sentence = record[ 2 ]
		distance = record[ 3 ]
		
		# update
		sentences.append( [ title, item, sentence, distance ] )
	
	# create a dataframe of the sentences and sort by title
	sentences = DataFrame( sentences, columns=COLUMNS )
	sentences = sentences.sort_values( [ 'titles', 'items' ] )

	# process/output each sentence; along the way, create a cache
	results = []
	cites   = []
	for index, result in sentences.iterrows() :
	
		# parse
		title    = result[ 'titles' ]
		item     = result[ 'items' ]
		sentence = result[ 'sentences' ]
		
		# update the caches
		results.append( sentence )
		cites.append( '\t'.join( [ title, str( item ) ] ) )
		
	# cache citres, results, and query; retain state, sort of
	with open( cwd/ETC/CACHEDCITES, 'w' )   as handle : handle.write( '\n'.join( cites ) )
	with open( cwd/ETC/CACHEDRESULTS, 'w' ) as handle : handle.write( '\n'.join( results ) )

	# format the result and done
	results = ' '.join( results )
	return( results )'''
	

# review
@reader.route( "/review/" )
def review() : 

	# read and join previously found results
	with open( cwd/ETC/CACHEDRESULTS ) as handle : results = handle.read().splitlines()
	results = ' '.join( results )

	carrel = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )
	query  = open( cwd/ETC/CACHEDQUERY ).read().split( '\t' )

	# done
	return render_template('search.htm', results=results, carrel=carrel, query=query[ 0 ], depth=query[ 1 ] )



# elaborate
@reader.route( "/cites/" )
def cites() :

	# configure
	NAMES  = [ 'items', 'sentences' ]
	CACHE  = 'cache'

	# initialize
	carrel = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ]
	cache  = '/'.join( [ STATIC, CARRELS, carrel, CACHE ] )
		
	# get the citations and their counts
	cites = read_csv( cwd/ETC/CACHEDCITES, sep='\t', names=NAMES )
	cites = cites.groupby( [ 'items' ], as_index=False )[ 'sentences' ].count()
	cites = cites.sort_values( 'sentences', ascending=False )
	cites = [ row.tolist() for index, row in cites.iterrows() ]	

	# process each citation; create a more expressive version of the citations; poor data structure design, probably
	items = []
	with open ( cwd/STATIC/CARRELS/carrel/INDEXJSON ) as handle : bibliographics = json.load( handle )
	for cite in cites :
	
		# parse
		id    = str( cite[ 0 ] )
		count = cite[ 1 ]
		
		# loop through all bhe bibliogrpahics; ought to be a dictionary, not a list
		for bibliographic in bibliographics :
		
			# match
			if bibliographic[ 'id' ] == id :
				
				# parse, update, and break
				author       = bibliographic[ 'author' ]
				title        = bibliographic[ 'title' ]
				date         = bibliographic[ 'date' ]
				summary      = bibliographic[ 'summary' ]
				keywords     = bibliographic[ 'keywords' ]
				extension    = bibliographic[ 'extension' ]
				items.append( { 'id':id, 'author':author, 'title': title, 'date':date, 'summary':summary, 'keywords':keywords, 'extension':extension, 'count':count } )
				break
					
	# done
	return render_template('cites.htm',  cache=cache, items=items )

# elaborate
def elaborate( question ) :
	'''Use the previously saved search results to address the given question.'''
	
	# configure
	PROMPT = 'Answer the question "%s", and use only the following as the source of the answer: %s'

	# initialize
	context = open( cwd/ETC/CACHEDRESULTS ).read()
	system  = open( cwd/ETC/SYSTEMPROMPT ).read()
	prompt  = ( PROMPT % ( question, context ) )

	# do the work and done
	results = generate( LLM, prompt, system=system )
	return( results )


# elaborate
@reader.route( "/elaborate/" )
def get_elaboration() :

	# initialize
	previousQuestion = open( cwd/ETC/CACHEDQUESTION ).read()
	with open( cwd/ETC/CACHEDPERSONA ) as handle : persona = handle.read()

	# get input
	question = request.args.get( 'question', '' )
	if not question : return render_template('elaborate-form.htm', question=previousQuestion )

	# cache the question
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )

	# do the work
	result = elaborate( question )
	
	# reformat the results
	response = sub( '\n\n', '</p><p>', result[ 'response' ] ) 
	response = '<p>' + response + '</p>'

	# done
	return render_template('elaborate.htm', results=response, question=question, persona=persona )

# summarize
def summarize() :

	# configure
	PROMPT = 'Summarize: %s'

	# initialize
	context = open( cwd/ETC/CACHEDRESULTS ).read()
	system  = open( cwd/ETC/SYSTEMPROMPT ).read()
	prompt  = ( PROMPT % ( context ) )

	# try to get a responese
	try: summary = generate( LLM, prompt, system=system )
	except ConnectionError : exit( 'Ollama is probably not running. Start it. Otherwise, call Eric.' )

	# done
	return( summary )
	
	
# summarize
@reader.route("/summarize/")
def get_summary() :

	# initialize
	with open( cwd/ETC/CACHEDPERSONA ) as handle : persona = handle.read()

	# do the work
	summary = summarize()
	
	# normalize a bit
	response = sub( '\n\n', '</p><p>', summary[ 'response' ] ) 
	results = '<p>' + response + '</p>'

	# done
	return render_template( 'summarize.htm', results=results, persona=persona )


# persona
def cache_persona( persona ) :
	'''Save the given persona and create a system prompt along the way'''
	
	# configure
	TEMPLATE = 'You are %s, and you respond in %s.'
	
	# initialize
	length = open( cwd/ETC/CACHEDLENGTH ).read()

	# do the work and done
	with open( cwd/ETC/SYSTEMPROMPT, 'w' )  as handle : handle.write( ( TEMPLATE % ( persona, length ) ) )
	with open( cwd/ETC/CACHEDPERSONA, 'w' ) as handle : handle.write( persona )
	

# persona
@reader.route("/persona/")
def get_persona() :

	# initialize
	with open( cwd/ETC/PERSONAS ) as handle : personas = handle.read().splitlines()
	selected = open( cwd/ETC/CACHEDPERSONA ).read()

	# get input
	persona = request.args.get( 'persona', '' )
	if not persona : return render_template( 'persona-form.htm', personas=personas, selected=selected )

	# save
	cache_persona( persona )
	return render_template('persona.htm', persona=persona )
	

def cache_length( length ) :

	# configure
	TEMPLATE = 'You are %s, and you respond in %s.'

	persona  = open( cwd/ETC/CACHEDPERSONA ).read()

	with open( cwd/ETC/SYSTEMPROMPT, 'w' ) as handle : handle.write( TEMPLATE % ( persona, length ) )
	with open( cwd/ETC/CACHEDLENGTH, 'w' ) as handle : handle.write( length )


# response lengths
@reader.route("/length/")
def get_length() :

	# initialize
	with open( cwd/ETC/LENGTHS ) as handle : lengths = handle.read().splitlines()
	selected = open( cwd/ETC/CACHEDLENGTH ).read()

	# get input
	length = request.args.get( 'length', '' )
	if not length : return render_template( 'length-form.htm', lengths=lengths, selected=selected )

	# save
	cache_length( length )
	return render_template('length.htm', length=length )
	

# carrel
@reader.route("/choose/")
def choose() :

	# get all the carrels as well as the most recently used carrel
	catalog = getCatalog( cwd/ETC/CATALOG )
	selected = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ]

	# get input
	carrel = request.args.get( 'carrel', '' )
	if not carrel : return render_template('carrel-form.htm', carrels=catalog, selected=selected )
	
	# split the input into an array; kinda dumb
	carrel = carrel.split( '--' )
			
	# save
	with open( cwd/ETC/CACHEDCARREL, 'w' ) as handle : handle.write( '\t'.join( carrel ) )
	return render_template( 'carrel.htm', carrel=carrel )
	

# format
@reader.route("/reformat/")
def reformat() :

	# configure
	PSIZE = 16

	# initialize
	sentences = open( cwd/ETC/CACHEDRESULTS ).read().splitlines()
	
	# vectorize and activate similaritites; for longer sentences increase the value of PSIZE
	embeddings = embed( model=EMBEDDER, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]

	# try to compute similarities
	try               : similarities = activate_similarities( cosine_similarity(embeddings), p_size=PSIZE )
	except ValueError : return render_template('format-error.htm' )

	# compute minmimas
	minmimas = argrelextrema( similarities, np.less, order=2 )

	# Get the order number of the sentences which are in splitting points
	splits = [ minmima for minmima in minmimas[ 0 ] ]

	# Create empty string
	text = ''
	for index, sentence in enumerate( sentences ) :
	
		# check if sentence is a minima (splitting point)
		if index in splits : text += f'\n\n{sentence} '
		else               : text += f'{sentence} '

	# do the tiniest bit of normalization
	text = sub( ' +', ' ', text ) 
	text = '<p>' + sub( '\n\n', '</p><p>', text ) + '</p>'

	# done
	return render_template('format.htm', results=text )


# serializes a list of floats into a compact "raw bytes" format; makes things more efficient?
def serialize( vector: List[float]) -> bytes : return pack( "%sf" % len( vector ), *vector )


def rev_sigmoid( x:float )->float : return ( 1 / ( 1 + exp( 0.5*x ) ) )


def activate_similarities( similarities:np.array, p_size=10 )->np.array :
        
        # To create weights for sigmoid function we first have to create space. P_size will determine number of sentences used and the size of weights vector.
        x = np.linspace( -10, 10, p_size )
 
        # Then we need to apply activation function to the created space
        y = np.vectorize(rev_sigmoid) 
 
        # Because we only apply activation to p_size number of sentences we have to add zeros to neglect the effect of every additional sentence and to match the length ofvector we will multiply
        activation_weights = np.pad(y(x),(0,similarities.shape[0]-p_size))
 
        ### 1. Take each diagonal to the right of the main diagonal
        diagonals = [similarities.diagonal(each) for each in range(0,similarities.shape[0])]
 
        ### 2. Pad each diagonal by zeros at the end. Because each diagonal is different length we should pad it with zeros at the end
        diagonals = [np.pad(each, (0,similarities.shape[0]-len(each))) for each in diagonals]
 
        ### 3. Stack those diagonals into new matrix
        diagonals = np.stack(diagonals)

        ### 4. Apply activation weights to each row. Multiply similarities with our activation.
        diagonals = diagonals * activation_weights.reshape(-1,1)
 
        ### 5. Calculate the weighted sum of activated similarities
        activated_similarities = np.sum(diagonals, axis=0)

        # done
        return( activated_similarities )


# get catalog
def getCatalog( catalog ) :
	
	catalog = read_csv( cwd/ETC/CATALOG )
	catalog = [ row.tolist() for index, row in catalog.iterrows() ]	

	return( catalog )
	
	
class Carrel :
	
	def __init__( self ) : return( None )

	def configure( self, key, name ) :
	
		self.key  = key
		self.name = name

	def read( self ) :
	
		# read
		with open( cwd/ETC/CACHEDCARREL ) as handle : data = handle.read()
		
		# parse and done
		self.key  = data.split( '\t' )[ 0 ]
		self.name = data.split( '\t' )[ 1 ]
		
	def cache( self ) :
		
		# do the work and done
		with open( cwd/ETC/CACHEDCARREL, 'w' ) as handle : handle.write( '\t'.join( [ self.key, self.name ] ) )
				

class Searcher : 
	
		def __init__( self ) : return( None )
		
		def read( self ) :
		
			# read, parse, and done
			with open( cwd/ETC/CACHEDQUERY ) as handle : data = handle.read()
			self.query = data.split( '\t' )[ 0 ]
			self.depth = data.split( '\t' )[ 1 ]

		def cache( self ) :
		
			# do the work and done
			with open( cwd/ETC/CACHEDQUERY, 'w' ) as handle : handle.write( '\t'.join( [ self.query, str( self.depth ) ] ) )
			return( True )
		
		def search( self, carrel, query, depth ) :
		
			# update
			self.query = query
			self.depth = depth
			
			# configure
			COLUMNS = [ 'titles', 'items', 'sentences', 'distances' ]
			SELECT  = "SELECT title, item, sentence, VEC_DISTANCE_L2(embedding, ?) AS distance FROM sentences ORDER BY distance LIMIT ?"
				
			# initialize
			library  = cwd/STATIC/CARRELS
			key      = carrel.key
			database = connect( library/key/ETC/DATABASE, check_same_thread=False )
			database.enable_load_extension( True )
			load( database )
			
			# vectorize query and search; get a set of matching records
			query   = embed( model=EMBEDDER, input=query ).model_dump( mode='json' )[ 'embeddings' ][ 0 ]
			records = database.execute( SELECT, [ serialize( query ), depth ] ).fetchall()
									
			# process each result; create a list of items
			items = []
			for record in records :
			
				# parse
				title    = record[ 0 ]
				item     = record[ 1 ]
				sentence = record[ 2 ]
				distance = record[ 3 ]
				
				# update
				items.append( [ title, item, sentence, distance ] )
			
			# create a dataframe of the sentences, sort by title, and done
			items = DataFrame( items, columns=COLUMNS )
			items = items.sort_values( [ 'titles', 'items' ] )
			return( items )
						

class Citations :

	def __init__( self, results ) : self.dataframe = results
	
	def to_sentences( self ) :
	
		# process each result; create a list of sentences
		sentences = []
		for index, row in self.dataframe.iterrows() :
		
			# parse and update
			sentences.append( row[ 'sentences' ] )

		# done
		return( sentences )

	def to_paragraph( self ) : return( ' '.join( self.to_sentences() ) )

	def to_cites( self ) :
	
		# process each citation
		cites = []
		for index, cite in self.dataframe.iterrows() :
		
			# parse and update
			title    = cite[ 'titles' ]
			item     = cite[ 'items' ]
			cites.append( [ title, str( item ) ] )
			
		# done
		return( cites )

	def to_bibliographics( self, carrel ) :
	
		# configure
		COLUMNS = [ 'items', 'sentences' ]
		
		# initalize
		cites  = self.to_cites()
		carrel = carrel.key
		
		# create a dataframe and create a sorted list
		cites = DataFrame( cites, columns=COLUMNS )
		cites = cites.groupby( [ 'items' ], as_index=False )[ 'sentences' ].count()
		cites = cites.sort_values( 'sentences', ascending=False )
		cites = [ row.tolist() for index, row in cites.iterrows() ]	
		
		with open ( cwd/STATIC/CARRELS/carrel/INDEXJSON ) as handle : bibliographics = json.load( handle )
		items = []
		for cite in cites :
		
			# parse
			id    = str( cite[ 0 ] )
			count = cite[ 1 ]
			
			# loop through all bhe bibliogrpahics; ought to be a dictionary, not a list
			for bibliographic in bibliographics :
			
				# match
				if bibliographic[ 'id' ] == id :
					
					# parse, update, and break
					author       = bibliographic[ 'author' ]
					title        = bibliographic[ 'title' ]
					date         = bibliographic[ 'date' ]
					summary      = bibliographic[ 'summary' ]
					keywords     = bibliographic[ 'keywords' ]
					extension    = bibliographic[ 'extension' ]
					items.append( { 'id':id, 'author':author, 'title': title, 'date':date, 'summary':summary, 'keywords':keywords, 'extension':extension, 'count':count } )
					break

		# done
		return (items )


class Summarizer :

	def __init__( self ) : return( None )
	def summarize( self, llm, prompt, system ) : return( generate( LLM, prompt, system=system ) )


class Elaborator :
		
	def __init__( self ) : return( None )
	def elaborate( self, llm, prompt, system ) : return( generate( LLM, prompt, system=system ) )
