import sys
import os
import pydoc

import hglib

repo = hglib.open( sys.argv[1] )
print( repo )

print( os.getcwd() )
with open( 'hglib-repo.html', 'w' ) as f:
    obj, name = pydoc.resolve( repo, True )

    f.write( pydoc.render_doc( obj, 'HGLIB %s', False, pydoc.html ) )

#help( obj )

print( '-- status ---' )
for x in repo.status():
    print( x )


print( '-- manifest ---' )
for x in repo.manifest():
    print( x )

print( '-- log ---' )
for x in repo.log():
    print( x )
