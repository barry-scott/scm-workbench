import sys

import wb_scm_version

spec_name = sys.argv[1]

with open( '%s.template' % (spec_name,), 'r', encoding='utf-8' ) as f:
    contents = f.read()

contents = contents.replace( 'SPEC-FILE-VERSION',
                            '%d.%d.%d' % (wb_scm_version.major
                                         ,wb_scm_version.minor
                                         ,wb_scm_version.patch) )

with open( spec_name, 'w', encoding='utf-8' ) as f:
    f.write( contents )
