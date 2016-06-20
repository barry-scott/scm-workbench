import sys

import pysvn

c = pysvn.Client()

def printState( state ):
    for name in sorted( state.keys() ):
        print( '%20s: %r' % (name, getattr( state, name )) )

state1 = c.status( sys.argv[1] )[0]
print( '--- status ---' )
printState( state1 )

state2 = c.status2( sys.argv[1] )[0]
print( '--- status2 ---' )
printState( state2 )
