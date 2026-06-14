#!/usr/bin/env bash

# xml2htm.sh - transform TEI files into HTML files

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - rooted in the TEI Toolbox of November 2018


# configure
PATTERN='*.xml'
XML='xml'
EXTENSION='htm'
HTM='htm'
XML2HTML='./etc/xml2html.xsl'

# get input
if [[ -z $1 ]]; then
	echo "Usage: $0 <carrel>" >&2
	exit
fi
CARREL=$1

# initialize
LIBRARY=$(rdr get)

# make sane
rm -rf "$LIBRARY/$CARREL/$HTM"
mkdir "$LIBRARY/$CARREL/$HTM"

# get and process each txt file
FILES=( $( find "$LIBRARY/$CARREL/$XML" -name $PATTERN ) )
for FILE in "${FILES[@]}"; do

	# debug
	echo $FILE >&2
			
	# get key and output
	BASENAME=$( basename $FILE )
	BASENAME=${BASENAME%.*}
	OUTPUT="$LIBRARY/$CARREL/$HTM/$BASENAME.$EXTENSION"
	
	# do the work; ought to figure out how to use xargs
	xsltproc $XML2HTML $FILE > $OUTPUT

done
exit

