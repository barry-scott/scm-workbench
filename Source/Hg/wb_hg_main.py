#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_main.py

'''
import sys

import wb_main
import wb_hg_app

if __name__ == '__main__':
    sys.exit( wb_main.main( wb_hg_app.WbHgApp, sys.argv ) )
