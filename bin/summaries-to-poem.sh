#!/usr/bin/env bash

# summaries-to-poem.sy - a front-end to summaries-to-poems.py

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# October 27, 2025 - first cut; 'bought a house today


# configure
SUMMARIESTOPOEM='./bin/summaries-to-poem.py'
LENGTHS=( "one word" "two words" "four words" "eigth words" "four words" "two words" "one word" )

# get input
if [[ -z $1 || -z $2 || -z $3 ]]; then
	echo "Usage $0 <key> <name> <query>" >&2
	exit
fi
KEY=$1
NAME=$2
QUERY=$3

# initialize
COLUMNS=$(tput cols) 

# create title and output
TITLE="On '$QUERY':"
printf "%*s\n" $(((${#TITLE}+$COLUMNS)/2)) "$TITLE"	
ATRIBUTION="A poem generated from $NAME"
printf "%*s\n" $(((${#ATRIBUTION}+$COLUMNS)/2)) "$ATRIBUTION"	
echo

# repeat for each length; output a summary
for LENGTH in "${LENGTHS[@]}"; do

	VERSE=$( $SUMMARIESTOPOEM "$KEY" "$NAME" "$QUERY" "$LENGTH" )
	printf "%*s\n" $(((${#VERSE}+$COLUMNS)/2)) "$VERSE"	

done