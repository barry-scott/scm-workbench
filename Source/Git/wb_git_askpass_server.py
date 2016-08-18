'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_server.py

'''
import wb_platform_specific

if wb_platform_specific.isWindows():
    from wb_git_askpass_server_win32 import *

else:
    # works for linux and macOS
    from wb_git_askpass_server_unix import *
