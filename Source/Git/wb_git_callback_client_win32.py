'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_callback_client_win32.py

    called with argv[1:] as the prompt
    expects a single line output as response.

'''
import sys
import os
import ctypes

class WbGitcallback:
    def __init__( self ):
        self.pipe_name = r'\\.\pipe\SCM Workbench GIT callback'

    def callback( self, argv ):
        if argv[1] == 'askpass':
            return self.askPass( argv[2] )

        elif argv[1] == 'editor':
            return self.editor( argv[2] )

        elif argv[1] == 'sequence-editor':
            return self.sequenceEditor( argv[2] )

        else:
            print( 'Error: Unknown callback command: %r' % (argv[1:],) )
            return 1

    def askPass( self, prompt ):
        rc, reply = self.callback( 'askpass', prompt )
        if reply is not None:
            print( reply )
        return rc

    def callback( self, facility, request ):
        message = '%s\0%s' % (facility, request)
        message = message.encode( 'utf-8' )

        buf_size = ctypes.c_int( 256 )
        buf_result = ctypes.create_string_buffer( buf_size.value )

        rc = ctypes.windll.kernel32.CallNamedPipeW(
                self.pipe_name,
                request,
                len(request),
                buf_result,
                buf_size,
                ctypes.byref( buf_size ),
                0
                )
        if rc == 0:
            err = ctypes.windll.kernel32.GetLastError()
            if err == 2:
                return None

            errmsg  = self.__getErrorMessage( err )
            with open( os.path.join( os.environ['USERPROFILE'], 'wb_scm_git_callback.log' ), 'a' ) as f:
                f.write( 'Error: CallNamedPipeA rc=%d err=%d errmsg=%r\n' % (rc, err, errmsg) )

            return 1, None

        else:
            reply = buf_result.raw[:buf_size.value].decode( 'utf-8' )
            return int(reply[0]), reply[1:]

    def __getErrorMessage( self, err ):
        FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
        FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

        errmsg_size = ctypes.c_int( 256 )
        errmsg = ctypes.create_string_buffer( errmsg_size.value + 1 )

        rc = ctypes.windll.kernel32.FormatMessageA(
            FORMAT_MESSAGE_FROM_SYSTEM|FORMAT_MESSAGE_IGNORE_INSERTS, # __in      DWORD dwFlags,
            None,           # __in_opt  LPCVOID lpSource,
            err,            # __in      DWORD dwMessageId,
            0,              # __in      DWORD dwLanguageId,
            errmsg,         # __out     LPTSTR lpBuffer,
            errmsg_size,    # __in      DWORD nSize,
            None            # __in_opt  va_list *Arguments
            )
        if rc == 0:
            return 'error 0x%8.8x' % (err,)

        return errmsg.value

if __name__ == '__main__':
    sys.exit( WbGitcallback().callback( sys.argv ) )
