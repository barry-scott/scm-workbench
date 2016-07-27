import sys

spec_name = sys.argv[1]
version = sys.argv[2]

with open( '%s.template' % (spec_name,), 'r', encoding='utf-8' ) as f:
    contents = f.read()

contents = contents.replace( 'SPEC-FILE-VERSION', version )

with open( spec_name, 'w', encoding='utf-8' ) as f:
    f.write( contents )
