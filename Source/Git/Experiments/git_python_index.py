#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )

index = r.index

for name in sorted( dir(index) ):
    print( '%s: %r' % (name, getattr( index, name )) )

print( index.__doc__ )

for entry in index.entries:
    print( '%r:' % (entry, ) )
    e = index.entries[ entry ]
    print( e.path, e.mode, e.flags )
