#!/bin/sh
import sys
import os

import wb_scm_version
import datetime

args = {'WB_LOCALE': sys.argv[1]}

if os.path.exists( 'scm_workbench_%(WB_LOCALE)s.po' % args ):
    print( 'Info: Update %(WB_LOCALE)s from scm_workbench.current.pot' % args )
    rc = os.system( 'msginit '
        '--input=scm_workbench.current.pot '
        '--locale=${WB_LOCALE} '
        '--no-wrap '
        '--no-translator '
        '--output-file=scm_workbench_%(WB_LOCALE)s.tmp.po' % args )
    if rc != 0:
        sys.exit( rc )

    rc = os.system( 'msgmerge '
        'scm_workbench_%(WB_LOCALE)s.po '
        'scm_workbench_%(WB_LOCALE)s.tmp.po '
        '--quiet '
        '--no-wrap '
        '--output-file=scm_workbench_%(WB_LOCALE)s.current.po' % args )
    if rc != 0:
        sys.exit( rc )

else:
    print( 'Info: Create %(WB_LOCALE)s from scm_workbench.current.pot' % args )
    rc = os.system( 'msginit '
        '--input=scm_workbench.current.pot '
        '--locale=%(WB_LOCALE)s.UTF-8 '
        '--no-wrap '
        '--no-translator '
        '--output-file=scm_workbench_%(WB_LOCALE)s.current.po' % args )
    if rc != 0:
        sys.exit( rc )

print( 'Info: Version brand %(WB_LOCALE)s from scm_workbench.current.pot' % args )
po_filename = 'scm_workbench_%(WB_LOCALE)s.current.po' % args
all_po_lines = open( po_filename, 'r', encoding='utf-8' ).readlines()

for index, line in enumerate( all_po_lines ):
    if line.startswith( '"Project-Id-Version:' ):
        all_po_lines[ index ] = ('"Project-Id-Version: SCM Workbench %d.%d.%d %s\\n"\n' % 
            (wb_scm_version.major
            ,wb_scm_version.minor
            ,wb_scm_version.patch
            ,wb_scm_version.commit))

    elif line.startswith( '"PO-Revision-Date:' ):
        all_po_lines[ index ] = '"PO-Revision-Date: %s\\n"\n' % (datetime.datetime.now().isoformat(' '),)

    elif line.startswith( '"Content-Type: text/plain; charset=' ):
        all_po_lines[ index ] = '"Content-Type: text/plain; charset=UTF-8\\n"\n'

with open( po_filename, 'w', encoding='utf-8' ) as f:
    f.write( ''.join( all_po_lines ) )

sys.exit( 0 )
