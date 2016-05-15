#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )

head = r.head

print( head )
for name in dir( head ):
    print( '%s: %r' % (name, getattr( head, name )) )


for name in dir( head.ref ):
    print( '%s: %r' % (name, getattr( head.ref, name )) )

