#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_main.py

'''
import sys
MIN_SUPPORTED_PYTHON_VERSION = (3, 5)
if sys.version_info < MIN_SUPPORTED_PYTHON_VERSION:
    print( 'Error: Must be run using pthon %d.%d or newer' % MIN_SUPPORTED_PYTHON_VERSION )
    sys.exit( 9 )

import wb_main
import wb_scm_app

if __name__ == '__main__':
    sys.exit( wb_main.main( wb_scm_app.WbScmApp, sys.argv ) )
