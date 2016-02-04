'''
 ====================================================================
 Copyright (c) 2003-2015 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    be_config.py

    Based on code from git WorkBench

'''
import sys

# point size and face need to choosen for platform
if sys.platform.startswith( 'win' ):
    face = 'Courier New'
    point_size = 8

elif sys.platform == 'darwin':
    face = 'Monaco'
    point_size = 12

else:
    # for unix systems
    face = 'Courier'
    point_size = 12
