import sys
import subprocess

def main( argv ):
    v = {}

    with open( argv[1], 'r' ) as f:
        for line in f:
            line = line.strip()
            if line == '':
                continue

            if line.startswith( '#' ):
                continue

            key, value = line.split( '=', 1 )
            v[ key.strip() ] = value.strip()

    result = subprocess.run( ['git', 'show-ref', '--head', '--hash', 'head'], stdout=subprocess.PIPE )

    with open( argv[2], 'w' ) as f:
        f.write( 'commit="%s"\n' % (result.stdout.decode('utf-8').strip(),) )
        for key in sorted( v.keys() ):
            f.write( '%s=%s\n' % (key, v[ key ]) )

    if len(argv) == 4:
        with open( argv[3], 'w' ) as f:
            f.write( 'set WB_SCM_VERSION=%s.%s.%s\n' % (v['major'], v['minor'], v['patch']) )

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )
