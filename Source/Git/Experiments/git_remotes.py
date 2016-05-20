#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )

print( r.remotes )

for rem in r.remotes:
    for name in dir(rem):
        if name[0] != '_':
            v = getattr( rem, name )
            if not callable( v ):
                print( 'remote %-15s: %r' % (name, v) )


    for ref in rem.refs:
        for name in dir(ref):
            if name[0] != '_' and name not in ('ref','reference'):
                v = getattr( ref, name )
                if not callable( v ):
                    print( 'ref %-15s: %r' % (name, getattr( ref, name )) )
        print( '-----' )
        print( '    ref.name', ref.name )
        print( '    ref.commit', ref.commit )
