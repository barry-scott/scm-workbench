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

# point size and face need to chosen for platform
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

diff_colour_normal = '#000000'
diff_colour_header = '#1919c0'

diff_colour_insert_line = '#008200'
diff_colour_delete_line = '#dc143c'
diff_colour_change_line = '#0000ff'

diff_colour_insert_char = '#008200'
diff_colour_delete_char = '#dc143c'
diff_colour_change_char = '#0000ff'
