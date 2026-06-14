#!/usr/bin/env python

# rrag.py - a command-line interface used to do RAG against Distant Reader study carrels

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June  3, 2026 - started yesterday, and today embellished search
# June  4, 2026 - added lexicons to search
# June 11, 2026 - added reformat


# require
from rrag import Searcher, Citations, Cacher, Summarizer, Settings, Elaborate, Reformatter
import click


# search
@click.command()
@click.argument( 'carrel' )
@click.option( '--type',    '-t', default='simple', type=click.Choice( [ 'simple', 'keywords', 'unigrams', 'bigrams', 'semantics', 'lexicon' ] ) )
@click.option( '--query',   '-q', default='love' )
@click.option( '--depth',   '-d', default=1 )
@click.option( '--breadth', '-b', default=8 )
def search( carrel, type, query, breadth, depth ) :
	'''Search <carrel> with <query> and retrieve <depth> sentences'''
	
	# configure
	LIBRARY = 'localLibrary'
	
	# require
	import rdr

	if type == 'lexicon' :
	
		lexicon = rdr.configuration( LIBRARY )/carrel/( rdr.ETC )/( rdr.LEXICON )
		with open( lexicon ) as handle : lexicon = handle.read().splitlines()
		query = ' '.join( lexicon )
	
	if type == 'keywords' :
	
		keywords = rdr.keywords( carrel, count=True ).splitlines()[ :breadth ]
		keywords = [ keyword.split( '\t' )[ 0 ] for keyword in keywords ]
		query    = ' '.join( keywords )
	
	if type == 'unigrams' :
	
		unigrams = rdr.ngrams( carrel, size=1, count=True ).splitlines()[ :breadth ]
		unigrams = [ unigram.split( '\t' )[ 0 ] for unigram in unigrams ]
		query    = ' '.join( unigrams )
	
	if type == 'bigrams' :
	
		bigrams = rdr.ngrams( carrel, size=2, count=True ).splitlines()[ :breadth ]
		bigrams = [ bigram.split( '\t' )[ 0 ] for bigram in bigrams ]
		query    = ' '.join( bigrams )
	
	if type == 'semantics' :
	
		if ' ' in query :
		
			words = ''
			
			for word in query.split() :
				
				semantics = rdr.word2vec( carrel, type='similarity', query=word, topn=breadth ).splitlines()
				semantics = [ semantic.split( '\t' )[ 0 ] for semantic in semantics ]
				semantics.append( word )
				words = words + ' '.join( semantics )
			
			query = words
			
		else :
		
			semantics = rdr.word2vec( carrel, type='similarity', query=query, topn=breadth ).splitlines()
			semantics = [ semantic.split( '\t' )[ 0 ] for semantic in semantics ]
			semantics.append( query )
			query     = ' '.join( semantics )
		
	# search, get sentences, and format
	results   = Searcher().search( carrel, query, depth )
	sentences = Citations( results ).to_sentences()
	paragraph = ' '.join( sentences )
	
	# done
	click.echo( paragraph )


# summarize
@click.command()
def summarize() : 
	'''Distill search results'''
	click.echo( Summarizer().summarize() )


# reformat
@click.command()
def reformat() : 
	'''Create paragraphs from search results'''
	click.echo( Reformatter().reformat() )


# elaborate
@click.command()
@click.argument( 'question' )
def elaborate( question ) : 
	'''Apply <question/command> to search results'''
	click.echo( Elaborate().elaborate( question ) )


# get settings
@click.command()
def get() : 
	'''Get preferences'''
	
	# configure
	SETTINGS = [ 'persona', 'length' ]
	
	# require
	from json import dumps
	
	# create a list of all the settings
	settings = {}
	for setting in SETTINGS : settings[ setting ] = Settings().get( setting )
	
	# done
	click.echo( dumps( settings ) )


# set settings
@click.command()
@click.argument( 'setting', default='persona', type=click.Choice( [ 'persona', 'length' ] ) )
def set( setting ) : 
	'''Set preferences'''
	
	# configure
	PERSONAS = 'personas.txt'
	LENGTHS  = 'lengths.txt'
	ETC      = 'etc'

	# require
	from pathlib import Path

	# initialize
	if setting   == 'persona' : choices = PERSONAS
	elif setting == 'length'  : choices = LENGTHS
	
	# read, display, and get a setting
	with open( Path( ETC )/choices ) as handle : choices = handle.read().splitlines()
	choice = choose( choices, setting )
	
	# save and done
	Settings().set( setting, choice )
	click.echo( 'Success. The %s has been set to "%s".' % ( setting, choice ) )
	
	
def choose(lines, type):
    print("\nChoose a %s:\n" % type )
    for i, line in enumerate(lines, 1): print(f"  {i}. {line}")
    while True:
        try:
            choice = int(input("\nEnter your choice (number): "))
            if 1 <= choice <= len(lines): return lines[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(lines)}")
        except ValueError:
            print("Please enter a valid number")


@click.group()
def rrag(): pass


# build the commands
rrag.add_command(get)
rrag.add_command(elaborate)
rrag.add_command(search)
rrag.add_command(set)
rrag.add_command(summarize)
rrag.add_command(reformat)

# go
if __name__ == '__main__': rrag()

