'''In the form of local HTTP (Web/Flask) application, an interactive index to 3,000 scholarly journal articles on the topic of digital libraries'''

# Eric Lease Morgan <emorgan@nd.edu>
# (c) Infomotions, LLC; distributed under a GNU Public License

# August     3, 2025 - first investigations; rooted in the non-lite version so I can share and demonstrate
# August     9, 2025 - added more things than I can count, but as of now, all functions work
# August    11, 2025 - modified so the whole thing is a package; I'm learning
# September 29, 2025 - removed "Nex steps"; while "commencing" here in the Sainte-Geneviève Library, Paris
# October   20, 2025 - added response length, I think
# October   23, 2025 - enhanced cites
# October   25, 2025 - started abstracting so I can write a command-line interface
# October   28, 2025 - making good headway
# October   31, 2025 - I think I'm done; famous last words


# configure prompts
PROMPTELABORATE = 'Answer the question "%s", and use only the following as the source of the answer: %s'
PROMPTSUMMARIZE = 'Summarize: %s'
PROMPTSYSTEM    = 'You are %s, and you respond in %s.'

# configure models
LLM      = 'deepseek-v3.1:671b-cloud'
EMBEDDER = 'nomic-embed-text'

# configure path names
CARRELS = 'carrels'
ETC     = 'etc'
STATIC  = 'static'
CACHE   = 'cache'

# configure file names
CACHEDCARREL    = 'cached-carrel.txt'
CACHEDLENGTH    = 'cached-length.txt'
CACHEDPERSONA   = 'cached-persona.txt'
CACHEDQUERY     = 'cached-query.txt'
CACHEDQUESTION  = 'cached-question.txt'
CACHEDSENTENCES = 'cached-sentences.txt'
CACHEDPROMPT    = 'system-prompt.txt'
CACHEDRESULTS   = 'cached-results.csv'
CATALOG         = 'catalog.csv'
DATABASE        = 'sentences.db'
INDEXJSON       = 'index.json'
LENGTHS         = 'lengths.txt'
PERSONAS        = 'personas.txt'

# require
from flask                    import Flask, render_template, request
from json                     import load as jsonload
from math                     import exp
from ollama                   import embed, generate
from os.path                  import dirname
from pandas                   import DataFrame, read_csv
from pathlib                  import Path
from re                       import sub
from scipy.signal             import argrelextrema
from sklearn.metrics.pairwise import cosine_similarity
from sqlite_vec               import load as vecload
from sqlite3                  import connect
from struct                   import pack
from typing                   import List
import numpy                  as     np

# initialize
reader  = Flask( __name__ )
cwd     = Path( dirname( __file__ ) )
library = cwd/STATIC/CARRELS

@reader.route( "/" )
def home() :
	'''Return the application's home page'''
	
	return render_template('home.htm' )


@reader.route( "/search/" )
def search() :
	'''Given a carrel, a query, and a depth, return a paragraph of sentences; this is the system's workhorse'''
	
	# initailize
	catalog            = Catalog().read()
	previousCarrelKey  = open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 0 ]
	previousCarrelName = open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 1 ]
	previousQuery      = open( cwd/ETC/CACHEDQUERY ).read().split('\t')[ 0 ]
	previousDepth      = open( cwd/ETC/CACHEDQUERY ).read().split('\t')[ 1 ]
		
	# get input
	carrel= request.args.get( 'carrel', '' )
	query = request.args.get( 'query', '' )
	depth = request.args.get( 'depth', '' )
	if not carrel or not query or not depth : return render_template('search-form.htm', catalog=catalog, name=previousCarrelName, previous=previousCarrelKey, query=previousQuery, depth=previousDepth )
			
	# split the returned carrel value (kinda dumb), create a carrel object, and search
	carrel    = Carrel( carrel.split( '--' )[ 0 ], carrel.split( '--' )[ 1 ] )
	searcher  = Searcher()
	results   = searcher.search( carrel, query, depth )
	citations = Citations( results )
	sentences = citations.to_sentences()
	paragraph = ' '.join( sentences )

	# cache things and done
	with open( cwd/ETC/CACHEDCARREL, 'w' )  as handle : handle.write( '\t'.join( [ carrel.key, carrel.name ] ) )
	with open( cwd/ETC/CACHEDQUERY, 'w' )   as handle : handle.write( '\t'.join( [ searcher.query, str( searcher.depth ) ] ) )
	with open( cwd/ETC/CACHEDRESULTS, 'w' ) as handle : handle.write( results.to_csv( index = False ) )
	return render_template( 'search.htm', carrel=carrel, query=query, paragraph=paragraph, depth=depth )


@reader.route( "/cites/" )
def cites() :

	# initialize
	carrel = Carrel( open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ], open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 1 ] )
	cache  = '/'.join( [ STATIC, CARRELS, carrel.key, CACHE ] )
	
	# do the work and done
	citations = Citations( read_csv( cwd/ETC/CACHEDRESULTS ) ).to_citations( carrel )
	return render_template( 'cites.htm',  cache=cache, citations=citations )


@reader.route( "/review/" )
def review() : 
	'''Simply echo the search results'''
	
	# read the caches and done
	carrel    = Carrel( open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ], open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 1 ] )
	query     = open( cwd/ETC/CACHEDQUERY ).read().split( '\t' )
	sentences = Citations( read_csv( cwd/ETC/CACHEDRESULTS ) ).to_sentences()
	paragraph = ' '.join( sentences )
	return render_template('search.htm', paragraph=paragraph, carrel=carrel, query=query[ 0 ], depth=query[ 1 ] )


@reader.route("/summarize/")
def summarize() :
	'''Using previously cached configurations, abridge the cached results'''
	
	# initialize
	sentences  = Citations( read_csv( cwd/ETC/CACHEDRESULTS ) ).to_sentences()
	paragraphs = ' '.join( sentences )
	prompt     = PROMPTSUMMARIZE % ( paragraphs )
	system     = open( cwd/ETC/CACHEDPROMPT ).read()
	persona    = open( cwd/ETC/CACHEDPERSONA ).read()

	# do the work, reformat the results, and done
	summary = generate( LLM, prompt, system=system )
	summary = sub( '\n\n', '</p><p>', summary[ 'response' ] ) 
	summary = '<p>' + summary + '</p>'
	return render_template( 'summarize.htm', results=summary, persona=persona )


@reader.route( "/elaborate/" )
def elaborate() :
	'''Address the given question to the cached search address'''
	
	# initialize
	previousQuestion = open( cwd/ETC/CACHEDQUESTION ).read()
	sentences        = Citations( read_csv( cwd/ETC/CACHEDRESULTS ) ).to_sentences()
	paragraph        = ' '.join( sentences )
	system           = open( cwd/ETC/CACHEDPROMPT ).read()
	persona          = open( cwd/ETC/CACHEDPERSONA ).read()
	
	# get input and update the cache
	question = request.args.get( 'question', '' )
	if not question : return render_template( 'elaborate-form.htm', question=previousQuestion )
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )

	# configure, do the work, reformat, and done
	prompt      = PROMPTELABORATE % ( question, paragraph )
	elaboration = generate( LLM, prompt, system=system )
	elaboration = sub( '\n\n', '</p><p>', elaboration[ 'response' ] ) 
	elaboration = '<p>' + elaboration + '</p>'
	return render_template( 'elaborate.htm', results=elaboration, question=question, persona=persona )


@reader.route("/ask/")
def ask() :
	'''Given a question, search the cached carrel, and apply the question to the results'''
	
	# configure
	DEPTH = '8'
	
	# initialize
	carrel  = Carrel( open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 0 ], open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 1 ] )
	persona = open( cwd/ETC/CACHEDPERSONA ).read()
	
	# search
	question = request.args.get( 'question', '' )
	searcher = Searcher()
	results  = searcher.search( carrel, question, DEPTH )

	# reformat results
	sentences = Citations( results ).to_sentences()
	paragraph = ' '.join( sentences )
	
	# cache
	with open( cwd/ETC/CACHEDQUERY, 'w' )   as handle : handle.write( '\t'.join( [ searcher.query, str( searcher.depth ) ] ) )
	with open( cwd/ETC/CACHEDRESULTS, 'w' ) as handle : handle.write( results.to_csv( index = False ) )
	with open( cwd/ETC/CACHEDQUESTION, 'w' ) as handle : handle.write( question )
	
	# initialize some more
	prompt = PROMPTELABORATE % ( question, paragraph )
	system = open( cwd/ETC/CACHEDPROMPT ).read()

	# do the work, reformat the results, and done
	elaboration = generate( LLM, prompt, system=system )
	elaboration = sub( '\n\n', '</p><p>', elaboration[ 'response' ] ) 
	elaboration = '<p>' + elaboration + '</p>'
	return render_template( 'elaborate.htm', results=elaboration, question=question, persona=persona )

	
@reader.route("/question/")
def question() :
	'''Randomly select and return a question from the cached carrel's database'''
	
	# configure
	SELECT = 'SELECT sentence FROM sentences WHERE sentence LIKE "%?" ORDER BY RANDOM() LIMIT 1'

	# initialize
	key  = open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 0 ]
	name = open( cwd/ETC/CACHEDCARREL ).read().split('\t')[ 1 ]
	
	database = connect( library/key/ETC/DATABASE, check_same_thread=False )
	database.enable_load_extension( True )
	vecload( database )
	
	# do the work and done
	question = database.execute( SELECT ).fetchone()[ 0 ]
	return render_template( 'question.htm', name=name, key=key, question=question )


def cache_length( length ) :
	'''Save the given length and create a system prompt along the way'''

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
	'''Get and set a carrel from which analysis will be done'''

	# get all the carrels as well as the most recently used carrel
	catalog = Catalog().read()
	key     = open( cwd/ETC/CACHEDCARREL ).read().split( '\t' )[ 0 ]

	# get input, split the result (dumb), cache, and done
	carrel = request.args.get( 'carrel', '' )
	if not carrel : return render_template('carrel-form.htm', carrels=catalog, selected=key )
	carrel = carrel.split( '--' )
	with open( cwd/ETC/CACHEDCARREL, 'w' ) as handle : handle.write( '\t'.join( carrel ) )
	return render_template( 'carrel.htm', carrel=carrel )
	

@reader.route("/reformat/")
def reformat() :
	'''Given a long paragraph, return a set of shorter paragraphs, hopefully'''
	
	# initialize
	sentences = Citations( read_csv( cwd/ETC/CACHEDRESULTS ) ).to_sentences() 
	
	# do the work, reformat a bit, and done
	text = Reformatter().reformat( sentences, EMBEDDER )
	if text == None : return render_template( 'format-error.htm' )
	text = sub( ' +', ' ', text ) 
	text = '<p>' + sub( '\n\n', '</p><p>', text ) + '</p>'
	return render_template( 'format.htm', results=text )


class Catalog :

	def __init__( self ) : return( None )
	
	def read( self ) :
	
		# read, update, and done
		items      = read_csv( cwd/ETC/CATALOG )
		items      = [ row.tolist() for index, row in items.iterrows() ]	
		self.items = items	
		return( items )
		

class Carrel :
	
	def __init__( self, key, name ) :

		self.key  = key
		self.name = name	
				

class Searcher : 
	
	def __init__( self ) : return( None )
		
	def search( self, carrel, query, depth ) :
	
		# update
		self.query = query
		self.depth = depth
		
		# configure
		COLUMNS = [ 'titles', 'items', 'sentences', 'distances' ]
		SELECT  = "SELECT title, item, sentence, VEC_DISTANCE_L2(embedding, ?) AS distance FROM sentences ORDER BY distance LIMIT ?"
			
		# initialize
		database = connect( library/carrel.key/ETC/DATABASE, check_same_thread=False )
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
			item     = record[ 1 ]
			sentence = record[ 2 ]
			distance = record[ 3 ]
			
			# update
			items.append( [ title, item, sentence, distance ] )
		
		# create a dataframe of the sentences, sort by title, and done
		items = DataFrame( items, columns=COLUMNS )
		items = items.sort_values( [ 'titles', 'items' ] )
		return( items )


	def serialize( self, vector: List[float]) -> bytes : 
		'''Serialize a list of floats into a compact "raw bytes" format'''
	
		return pack( "%sf" % len( vector ), *vector )
	

class Citations :

	def __init__( self, dataframe ) : self.original = dataframe
	
	def to_sentences( self ) :
	
		# create a list of sentences and done
		sentences = []
		for index, row in self.original.iterrows() : sentences.append( row[ 'sentences' ] )
		return( sentences )

			
	def to_citations( self, carrel ) :
			
		# initialize
		items = self.original
		key   = carrel.key
		
		# create a list of items sorted by the number of times they were cited
		items = items.groupby( [ 'titles' ], as_index=False )[ 'sentences' ].count()
		items = items.sort_values( 'sentences', ascending=False )
		items = [ row.tolist() for index, row in items.iterrows() ]	
				
		# process each item; transform the list of items into a list of pseudo-citations
		citations = []
		with open ( library/key/INDEXJSON ) as handle : bibliographics = jsonload( handle )		
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

	def reformat( self, sentences, embedder ) :

		# configure
		PSIZE = 16
		ORDER = 2

		# vectorize and activate similaritites; for longer sentences increase the value of PSIZE
		embeddings = embed( model=embedder, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]
	
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

	def rev_sigmoid( self, x:float )->float :
		''''Don't understand what this function does'''
	
		return ( 1 / ( 1 + exp( 0.5*x ) ) )



