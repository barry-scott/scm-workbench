'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_callback_server.py

'''
import sys

if sys.platform == 'win32':
    from wb_git_callback_server_win32 import *

else:
    # works for linux and macOS
    from wb_git_callback_server_unix import *
