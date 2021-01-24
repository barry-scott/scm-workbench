#!/usr/bin/env python
import sys
import re

import build_log
# turn on colour output
log = build_log.BuildLog()
log.setColour( True )

def main( argv ):
    all_copies = []
    for filename in argv[1:]:
        all_copies.append( open( filename, 'w' ) )

    colour = re.compile( r'\033\[[\d;]*m' )

    for line in sys.stdin:
        # allow colours to be shown seen
        sys.stdout.write( line )

        # remove colouring from log files.
        line = colour.sub( '', line )

        for copy in all_copies:
            copy.write( line )

    return 0

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )
