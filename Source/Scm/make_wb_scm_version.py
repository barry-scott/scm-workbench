import sys
import subprocess

v = {}

with open( sys.argv[1], 'r' ) as f:
    for line in f:
        line = line.strip()
        if line == '':
            continue

        if line.startswith( '#' ):
            continue

        key, value = line.split( '=', 1 )
        v[ key.strip() ] = value.strip()

result = subprocess.run( ['git', 'show-ref', '--head', '--hash', 'head'], stdout=subprocess.PIPE )

with open( sys.argv[2], 'w' ) as f:
    f.write( 'commit="%s"\n' % (result.stdout.strip(),) )
    for key in sorted( v.keys() ):
        f.write( '%s=%s\n' % (key, v[ key ]) )
