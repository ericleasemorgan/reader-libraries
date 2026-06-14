#!/usr/bin/env python

# txt2xml.py - given a plain text file, output a paragraphized version in TEI

# Eric Lease Morgan <eric_morgan@infomotions.com>
# (c) Infomotions, LLC; distributed under a GNU Public License

# June 12, 2026 - rooted in the TEI Toolbox of November 2018


# configure
SLUG     = '•'
TEMPLATE = './etc/template.xml'

# require
from re  import sub
from sys import argv, exit

# get input
if len( argv ) != 3 : exit( 'Usage: ' + argv[ 0 ] + " <file> <key>" )
file = argv[ 1 ]
key  = argv[ 2 ]

# read the given file
with open( file ) as handle : text = handle.read()

# paragraph-ize
text = sub( r'\n\n\n+', SLUG,   text )
text = sub( r'\n+',     ' ',    text )
text = sub( r'\s',      ' ',    text )
text = sub( r' +',      ' ',    text )
text = sub( SLUG,       '\n\n', text )
text = sub( '\n +',     '\n',   text )

# escape
text = sub( '&', '&amp;', text )
text = sub( '<', '&lt;',  text )
text = sub( '>', '&gt;',  text )

# ininitialize mark-up process
lines             = text.splitlines()
xml_lines         = [ '<body>' ]
in_paragraph      = False
current_paragraph = []

# process each line; create rudimentary mark-up
for line in lines:
    stripped_line = line.strip()
    # If we hit a blank line, it's the end of a paragraph
    if not stripped_line:
        if in_paragraph and current_paragraph:
            # Join the collected lines and wrap them in a <p> tag
            paragraph_text = ' '.join(current_paragraph)
            xml_lines.append(f'<p>{paragraph_text}</p>')
            current_paragraph = []
            in_paragraph = False
    else:
        current_paragraph.append(stripped_line)
        in_paragraph = True

# process the last paragraph
if current_paragraph:
    paragraph_text = ' '.join(current_paragraph)
    xml_lines.append(f'<p>{paragraph_text}</p>')

# close the markup
xml_lines.append('</body>')

# read the configured template, and do the substitutions
with open( TEMPLATE ) as handle : xml = handle.read()
xml = xml.replace( '##BODY##', '\n\n'.join( xml_lines ) )
xml = xml.replace( '##IDNO##', key )

# output and done
print( xml )
exit()

