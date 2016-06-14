#!/usr/bin/python3
import sys
import os
import glob

all_py_files = set( glob.glob( '*.py' )+glob.glob('../Common/*.py' ) )
all_py_files.remove( 'wb_scm_images.py' )

f = open( 'wb_files.tmp', 'wt' )
for py_file in all_py_files:
    f.write( '%s\n' % py_file )
f.close()

cmd = ('xgettext '
    '--files-from=wb_files.tmp '
    '--from-code=utf-8 '
    '--default-domain=scm_workbench '
    '--output=I18N/scm_workbench.current.pot '
    '--msgid-bugs-address=barry@barrys-emacs.org '
    '--copyright-holder="Barry Scott" '
    '--keyword=U_ '
    '--keyword=T_ '
    '--keyword=S_:1,2 '
    '--add-comments '
    '--no-wrap '
    '--width=2047 '
    '--add-comments=Translate '
    '--language=Python')

print( 'Info: %s' % (cmd,) )
rc = os.system( cmd )
sys.exit( rc )
