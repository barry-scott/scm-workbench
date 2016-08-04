'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_client.py

    called with argv[1:] as the prompt
    expects a single line output as response.

'''
import sys
import os
import ctypes

class WbGitAssPass:
    def __init__( self ):
        self.pipe_name = "\\\\.\\pipe\\SCM Workbench AskPass"

    def askPass( self, prompt ):
        print( 'qqq %r' % (prompt,) )
        prompt = prompt.encode( 'utf-8' )

        buf_size = ctypes.c_int( 256 )
        buf_result = ctypes.create_string_buffer( buf_size.value )

        rc = ctypes.windll.kernel32.CallNamedPipeW(
                self.pipe_name,
                prompt,
                len(prompt),
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
            with open( os.path.join( os.environ['USERPROFILE'], 'wb_scm_askpass.log' ), 'a' ) as f:
                f.write( 'Error: CallNamedPipeA rc=%d err=%d errmsg=%r\n' % (rc, err, errmsg) )

            return 1

        else:
            reply = buf_result.raw[:buf_size.value]

            print( reply[1:] )
            return int(reply[0])

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
    sys.exit( WbGitAssPass().askPass( sys.argv[1] ) )
