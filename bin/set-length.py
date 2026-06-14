#!/usr/bin/env python

# set-length.py

LENGTHS = 'lengths.txt'
ETC     = 'etc'

from pathlib import Path
from rrag    import Settings

def choose(lines):
    print("\nChoose a length:\n")
    for i, line in enumerate(lines, 1): print(f"  {i}. {line}")
    while True:
        try:
            choice = int(input("\nEnter your choice (number): "))
            if 1 <= choice <= len(lines): return lines[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(lines)}")
        except ValueError:
            print("Please enter a valid number")

# read the personas, and display a menu of choices
with open( Path( ETC )/LENGTHS ) as handle : lengths = handle.read().splitlines()
length = choose( lengths )

# do the work and done
Settings().set( 'length', length )
exit()

