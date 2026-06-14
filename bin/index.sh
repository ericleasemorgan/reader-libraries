#!/usr/bin/env bash

# index.sh - make carrel searchable as well as search results verifyable; one script to rule many

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - first cut


# get input
if [[ -z $1 ]]; then
	echo "Usage: $0 <carrel>" >&2
	exit
fi
CARREL=$1

# create rudimentary XML filess
./bin/txt2xml.sh $CARREL

# markup the sentences in them
./bin/morphadorn.sh $CARREL

# save the sentences to sets of CSV files
./bin/sentences2csv.py $CARREL

# vectororize (index) them
./bin/vectorize.py $CARREL

# transform the XML into HTML
./bin/xml2htm.sh $CARREL

# done
exit

