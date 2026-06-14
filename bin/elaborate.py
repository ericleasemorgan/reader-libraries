#!/usr/bin/env python

# elaborate.py - given a question/command, elaborate on the results

# require
import rrag
from sys  import argv, exit

# get input
if len( argv ) != 2 : exit( 'Usage: ' + argv[ 0 ] + " <question/command>" )
query = argv[ 1 ]

# do the work and done
print( rrag.Elaborate().elaborate( query ) )
exit()
