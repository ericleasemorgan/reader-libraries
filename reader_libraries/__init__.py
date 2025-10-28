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


# configure prompts
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTSYSTEM    = 'You are %s, and you respond in %s.'

# configure models
LLM      = 'deepseek-v3.1:671b-cloud'
EMBEDDER = 'nomic-embed-text'

# configure caches
CACHEDCARREL   = 'cached-carrel.txt'
CACHEDCITES    = 'cached-cites.txt'
CACHEDLENGTH   = 'cached-length.txt'
CACHEDPERSONA  = 'cached-persona.txt'
CACHEDQUERY    = 'cached-query.txt'
CACHEDQUESTION = 'cached-question.txt'
CACHEDRESULTS  = 'cached-results.txt'
CACHEDPROMPT   = 'system-prompt.txt'

# configure path names
CARRELS = 'carrels'
ETC     = 'etc'
STATIC  = 'static'

# configure file names
CATALOG   = 'catalog.csv'
DATABASE  = 'sentences.db'
INDEXJSON = 'index.json'
LENGTHS   = 'lengths.txt'
PERSONAS  = 'personas.txt'

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


@reader.route( "/" )
def home() :
	'''Return the Reader's home page'''
	
	return render_template('home.htm' )


@reader.route( "/search/" )
def search() :
	'''Given a carrel, a query, and a depth, return a paragraph of sentences'''
	
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
		
	# search and cache
	citations = searcher.search( carrel, query, depth )
	paragraph = Citations( citations ).to_paragraph()
	
	# cache things; maintain state sans cookies
	carrel.cache()
	searcher.cache()
	citations = Citations( citations )
	citations.cacheSentences()
	citations.cacheCites()

	# done
	return render_template( 'search.htm', carrel=carrel.name, query=query, results=paragraph, depth=depth )


@reader.route("/ask/")
def ask() :
	'''Given a question, search the cached carrel, and apply the question to the results'''
	
	# configure
	DEPTH = '8'
	
	# initialize; search
	carrel   = Carrel()
	result   = carrel.read()
	question = request.args.get( 'question', '' )
	persona  = open( cwd/ETC/CACHEDPERSONA ).read()
	
	# search and cache question
	searcher  = Searcher()
	citations = searcher.search( carrel, question, DEPTH )
	paragraph = Citations( citations ).to_paragraph()
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )

	# initialize some more
	paragraph = open( cwd/ETC/CACHEDRESULTS ).read()
	system    = open( cwd/ETC/CACHEDPROMPT ).read()
	prompt    = ( PROMPTELABORATE % ( question, paragraph ) )

	# do the work, reformat the results, and done
	result = generate( LLM, prompt, system=system )
	response = sub( '\n\n', '</p><p>', result[ 'response' ] ) 
	response = '<p>' + response + '</p>'
	return render_template('elaborate.htm', results=response, question=question, persona=persona )

	
@reader.route("/question/")
def question() :
	'''Randomly select and return a question from the cached carrel's database'''
	
	# configure
	SELECT = 'SELECT sentence FROM sentences WHERE sentence LIKE "%?" ORDER BY RANDOM() LIMIT 1'

	# initialize
	carrel = Carrel()
	result = carrel.read()
	key    = carrel.key
	name   = carrel.name
	
	library  = cwd/STATIC/CARRELS	
	database = connect( library/key/ETC/DATABASE, check_same_thread=False )
	database.enable_load_extension( True )
	load( database )
	
	# do the work and done
	question = database.execute( SELECT ).fetchone()[ 0 ]
	return render_template( 'question.htm', name=name, key=key, question=question )


@reader.route( "/review/" )
def review() : 
	'''Simply echo the search results'''
	
	# read the cache and done
	carrel  = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )
	query   = open( cwd/ETC/CACHEDQUERY ).read().split( '\t' )
	results = open( cwd/ETC/CACHEDRESULTS ).read().splitlines()
	return render_template('search.htm', results=' '.join( results ), carrel=carrel, query=query[ 0 ], depth=query[ 1 ] )


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


@reader.route( "/elaborate/" )
def elaborate() :
	'''Address the given question to the cached search address'''
	
	# initialize
	previousQuestion = open( cwd/ETC/CACHEDQUESTION ).read()
	paragraph        = open( cwd/ETC/CACHEDRESULTS ).read()
	system           = open( cwd/ETC/CACHEDPROMPT ).read()
	persona          = open( cwd/ETC/CACHEDPERSONA ).read()
	
	# get input and update the cache
	question = request.args.get( 'question', '' )
	if not question : return render_template('elaborate-form.htm', question=previousQuestion )
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )

	# configure, do the work, reformat, and done
	prompt      = PROMPTELABORATE % ( question, paragraph )
	elaboration = Elaborator().elaborate( LLM, prompt, system )
	elaboration = sub( '\n\n', '</p><p>', elaboration[ 'response' ] ) 
	elaboration = '<p>' + elaboration + '</p>'
	return render_template('elaborate.htm', results=elaboration, question=question, persona=persona )


@reader.route("/summarize/")
def summarize() :
	'''Using previously cached configurations, abridge the cached results'''
	
	# initialize
	prompt  = PROMPTSUMMARIZE % ( open( cwd/ETC/CACHEDRESULTS ).read() )
	system  = open( cwd/ETC/CACHEDPROMPT ).read()
	persona = open( cwd/ETC/CACHEDPERSONA ).read()

	# do the work, reformat the results, and done
	summary = Summarizer().summarize( LLM, prompt, system )
	summary = sub( '\n\n', '</p><p>', summary[ 'response' ] ) 
	summary = '<p>' + summary + '</p>'
	return render_template( 'summarize.htm', results=summary, persona=persona )


def cache_length( length ) :
	'''Save the given lenght and create a system prompt along the way'''

	# initialize and do the work
	persona = open( cwd/ETC/CACHEDPERSONA ).read()
	with open( cwd/ETC/CACHEDPROMPT, 'w' ) as handle : handle.write( PROMPTSYSTEM % ( persona, length ) )
	with open( cwd/ETC/CACHEDLENGTH, 'w' ) as handle : handle.write( length )


def cache_persona( persona ) :
	'''Save the given persona and create a system prompt along the way'''
		
	# initialize and do the work
	length = open( cwd/ETC/CACHEDLENGTH ).read()
	with open( cwd/ETC/CACHEDPROMPT, 'w' )  as handle : handle.write( ( PROMPTSYSTEM % ( persona, length ) ) )
	with open( cwd/ETC/CACHEDPERSONA, 'w' ) as handle : handle.write( persona )
	

@reader.route("/persona/")
def persona() :
	'''Get and set a persona for the system prompt'''
	
	# initialize
	personas = open( cwd/ETC/PERSONAS ) .read().splitlines()
	selected = open( cwd/ETC/CACHEDPERSONA ).read()

	# get input, do the work, and done
	persona = request.args.get( 'persona', '' )
	if not persona : return render_template( 'persona-form.htm', personas=personas, selected=selected )
	cache_persona( persona )
	return render_template('persona.htm', persona=persona )


@reader.route("/length/")
def length() :
	'''Get and set a length for the system prompt'''

	# initialize
	lengths  = open( cwd/ETC/LENGTHS ).read().splitlines()
	selected = open( cwd/ETC/CACHEDLENGTH ).read()

	# get input, cache the result, and done
	length = request.args.get( 'length', '' )
	if not length : return render_template( 'length-form.htm', lengths=lengths, selected=selected )
	cache_length( length )
	return render_template('length.htm', length=length )
	

@reader.route("/choose/")
def choose() :
	'''Get and set a carrel from content will be analyzed'''

	# get all the carrels as well as the most recently used carrel
	catalog  = getCatalog( cwd/ETC/CATALOG )
	selected = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ]

	# get input, split the result (dumb), cache, and done
	carrel = request.args.get( 'carrel', '' )
	if not carrel : return render_template('carrel-form.htm', carrels=catalog, selected=selected )
	carrel = carrel.split( '--' )
	with open( cwd/ETC/CACHEDCARREL, 'w' ) as handle : handle.write( '\t'.join( carrel ) )
	return render_template( 'carrel.htm', carrel=carrel )
	

@reader.route("/reformat/")
def reformat() :
	'''Given a long paragraph, return a set of shorter paragraphs, hopefully'''
	
	# configure
	PSIZE = 16
	ORDER = 2

	# initialize
	sentences = open( cwd/ETC/CACHEDRESULTS ).read().splitlines()
	
	# vectorize and activate similaritites; for longer sentences increase the value of PSIZE
	embeddings = embed( model=EMBEDDER, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]

	# try to compute similarities
	try               : similarities = activate_similarities( cosine_similarity(embeddings), p_size=PSIZE )
	except ValueError : return render_template('format-error.htm' )

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

	# do the tiniest bit of normalization
	text = sub( ' +', ' ', text ) 
	text = '<p>' + sub( '\n\n', '</p><p>', text ) + '</p>'

	# done
	return render_template( 'format.htm', results=text )


def serialize( vector: List[float]) -> bytes : 
	'''Serialize a list of floats into a compact "raw bytes" format'''
	
	return pack( "%sf" % len( vector ), *vector )


def rev_sigmoid( x:float )->float :
	''''Don't understand what this function does'''
	
	return ( 1 / ( 1 + exp( 0.5*x ) ) )


def activate_similarities( similarities:np.array, p_size=10 )->np.array :
	''''Don't really understand what this function does'''

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


def getCatalog( catalog ) :
	'''Return a list of lists describing the carrels this system uses to do its work'''
	
	# initialize and done
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
	
		# create a list of sentences and done
		sentences = []
		for index, row in self.dataframe.iterrows() : sentences.append( row[ 'sentences' ] )
		return( sentences )
		
		
	def to_paragraph( self ) : return( ' '.join( self.to_sentences() ) )
	def cacheSentences( self ) :
	
		# do the work and done
		sentences = self.to_sentences()
		with open( cwd/ETC/CACHEDRESULTS, 'w' ) as handle : handle.write( '\n'.join( sentences ) )
		return( True )

	def cacheCites( self ) :
	
		# do the work and done
		cites = self.to_cites()
		with open( cwd/ETC/CACHEDCITES, 'w' ) as handle : handle.write( '\n'.join( cites ) )
		return( True )

	def to_cites( self ) :
	
		# process each citation
		cites = []
		for index, cite in self.dataframe.iterrows() :
		
			# parse and update
			title    = cite[ 'titles' ]
			item     = cite[ 'items' ]
			cites.append( '\t'.join( [ title, str( item ) ] ) )
			
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
	def summarize( self, llm, prompt, system ) : return( generate( llm, prompt, system=system ) )


class Elaborator :
		
	def __init__( self ) : return( None )
	def elaborate( self, llm, prompt, system ) : return( generate( llm, prompt, system=system ) )


