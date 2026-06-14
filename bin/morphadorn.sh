#!/usr/bin/env bash

# morphadorn.sh - a front-end to morphadorn.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - rooted in the TEI Toolbox of November 2018


# configure
XML='xml'
PATTERN='*.xml'
MORPHADORN='./bin/morphadorn.py'
PROCESSES=12

# get input
if [[ -z $1 ]]; then
	echo "Usage: $0 <carrel>" >&2
	exit
fi
CARREL=$1

# initialize
LIBRARY=$(rdr get)

# get and process each txt file
find "$LIBRARY/$CARREL/$XML" -name $PATTERN | xargs -n 1 -P $PROCESSES $MORPHADORN