#!/usr/bin/python
import sys
import os

localedir = sys.argv[1]

all_lang = ['en', 'de', 'hu']

for lang in all_lang:
    mo_output_dir = '%s/%s/LC_MESSAGES' % (localedir, lang)
    os.makedirs( mo_output_dir )

    if lang == 'en':
        po_file = 'I18N/git_workbench_en.current.po'
    else:
        po_file = 'I18N/git_workbench_%s.po' % lang

    rc = os.system( 'msgfmt '
        '%s '
        '--check-format '
        '--output-file=%s/git_workbench.mo' %
            (po_file, mo_output_dir) )
    if rc != 0:
        sys.exit( rc )

    print 'Info: %s/git_workbench.mo' % mo_output_dir
sys.exit( 0 )
