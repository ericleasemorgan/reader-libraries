#!/usr/bin/env bash

# txt2xml.sh - a front-end to txt2xml.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - rooted in the TEI Toolbox of November 2018


# configure
TXT='txt'
PATTERN='*.txt'
TXT2XML='./bin/txt2xml.py'
XML='xml'
EXTENSION='xml'

# get input
if [[ -z $1 ]]; then
	echo "Usage: $0 <carrel>" >&2
	exit
fi
CARREL=$1

# initialize
LIBRARY=$(rdr get)

# make sane
rm -rf "$LIBRARY/$CARREL/$XML"
mkdir "$LIBRARY/$CARREL/$XML"

# get and process each txt file
FILES=( $( find "$LIBRARY/$CARREL/$TXT" -name $PATTERN ) )
for FILE in "${FILES[@]}"; do

	# debug
	echo $FILE >&2
	
	# get key and output
	BASENAME=$( basename $FILE )
	BASENAME=${BASENAME%.*}
	OUTPUT="$LIBRARY/$CARREL/$XML/$BASENAME.$EXTENSION"
	
	# do the work; ought to figure out how to use xargs
	$TXT2XML $FILE $BASENAME > $OUTPUT

done
exit

