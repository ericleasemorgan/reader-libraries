#!/usr/bin/env python

# reformat.py - given a list of sentences, output an "essay"; good for summarization
# see: https://medium.com/@npolovinkin/how-to-chunk-text-into-paragraphs-using-python-8ae66be38ea6

# Eric Lease Morgan <emorgan@nd.edu>
# (c) University of Notre Dame; distributed under a GNU Public License

# May  25, 2025 - first cut; fun!
# June  6, 2025 - commented out shortenting and lengthening sentences
# July  4, 2025 - moved to Ollama and a different embedder


# configure
MODEL     = 'nomic-embed-text'
PSIZE     = 16

# require
from math                     import exp
from ollama                   import embed
from re                       import sub
from scipy.signal             import argrelextrema
from sklearn.metrics.pairwise import cosine_similarity
from sys                      import exit
import numpy                  as     np
from rrag                     import Reformatter, Citations


# get the sentences
sentences  = Citations( read_csv( cwd/RRAGCACHE/CACHEDRESULTS ) ).to_sentences()

print( sentences )

# vectorize and activated similaritites; for longer sentences increase the value of PSIZE
embeddings = embed( model=MODEL, input=sentences ).model_dump( mode='json' )[ 'embeddings' ]

try : similarities = activate_similarities( cosine_similarity(embeddings), p_size=PSIZE )
except ValueError as error : exit( "Number of sentences too small. If this error continues, call Eric.\n" )
	
# compute the minmimas -- the valleys between sentences
minmimas = argrelextrema( similarities, np.less, order=2 )

        
#Get the order number of the sentences which are in splitting points
splits = [ minmima for minmima in minmimas[ 0 ] ]

# Create empty string
text = ''
for index, sentence in enumerate( sentences ) :

    # Check if sentence is a minima (splitting point)
    if index in splits :
    
        # If it is than add a dot to the end of the sentence and a paragraph before it.
        text += f'\n\n{sentence} '

    else:
    
        # If it is a normal sentence just add a dot to the end and keep adding sentences.
        text += f'{sentence} '


# do the tiniest bit of normalization
text = sub( ' +', ' ', text ) 

# output and done
print( text )
exit()
       