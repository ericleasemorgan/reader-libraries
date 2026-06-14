#!/usr/bin/env python

# get-settings.py

SETTINGS = [ 'persona', 'length' ]

from rrag import Settings

# do the work and done
settings = {}
for setting in SETTINGS :

	settings[ setting ] = Settings().get( setting )
	
print( settings )