'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_shell_commands.py

'''
import sys

if sys.platform == 'win32':
    from wb_shell_win32_commands import *

elif sys.platform == 'darwin':
    from wb_shell_macosx_commands import *

else:
    from wb_shell_unix_commands import *
