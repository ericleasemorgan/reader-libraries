#!/usr/bin/env python

# list-carrels.py - simply output the study carrels in this system

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributeted under a GNU Public License

# November 1, 2025 - first investigation


# configure
HEADER = [ 'key', 'name', 'url' ]

# require
from reader_libraries import Catalog

# initialize output
print( '\t'.join( HEADER ) )

# do the work, output some more, and done
for journal in Catalog().read() : print( '\t'.join( journal ) )
exit

