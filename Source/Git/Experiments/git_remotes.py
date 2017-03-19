#!/usr/bin/python3
import sys

import git

r = git.Repo( sys.argv[1] )
print( repr( r.remotes ) )
for rem in r.remotes:
    print( '=====' )
    for name in dir(rem):
        if name[0] != '_':
            v = getattr( rem, name )
            if not callable( v ):
                print( 'remote %-15s: %r' % (name, v) )
    print( '􏼠remote.urls', list( rem.urls ) )

    continue

    for ref in rem.refs:
        print( '    -----' )
        for name in dir(ref):
            if name[0] != '_' and name not in ('ref','reference'):
                v = getattr( ref, name )
                if not callable( v ):
                    print( '    ref %-15s: %r' % (name, getattr( ref, name )) )
        print( '    ref.name', ref.name )
        print( '    ref.commit', ref.commit )
