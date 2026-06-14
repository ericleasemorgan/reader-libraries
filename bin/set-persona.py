#!/usr/bin/env python

# set-persona.py

PERSONAS = 'personas.txt'
ETC      = 'etc'

from pathlib import Path
from rrag    import Settings

def choose(lines):
    print("\nChoose a persona:\n")
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
with open( Path( ETC )/PERSONAS ) as handle : personas = handle.read().splitlines()
persona = choose( personas )

# do the work and done
Settings().set( 'persona', persona )
exit()

