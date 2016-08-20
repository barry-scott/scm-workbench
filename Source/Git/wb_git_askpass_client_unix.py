'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_client_unix.py

    called with argv[1:] as the prompt
    expects a single line output as response.


    On macOS will be run by python2.7
    On Linux we can use python3

'''
import sys
import os
import os.path
import pwd
import stat
import tempfile
import select

class WbGitAskPass:
    fifo_name_client = '.ScmWorkbench.client'
    fifo_name_server = '.ScmWorkbench.server'

    def __init__( self ):
        pass

    def askPass( self, prompt ):
        e = pwd.getpwuid( os.geteuid() )
        fifo_dir = os.path.join( tempfile.gettempdir(), e.pw_name )

        client_fifo = os.path.join( fifo_dir, self.fifo_name_client )
        server_fifo = os.path.join( fifo_dir, self.fifo_name_server )

        try:
            error_msg = 'Error: failed to open fifo - %s'
            fd_server = os.open( server_fifo, os.O_WRONLY|os.O_NONBLOCK )

            error_msg = 'Error: failed to open fifo - %s'
            fd_client = os.open( client_fifo, os.O_RDONLY|os.O_NONBLOCK )

            prompt = prompt.encode( 'utf-8' )

            error_msg = 'Error: failed to write cmd to server - %s'
            size = os.write( fd_server, prompt )
            if size != len(prompt):
                print( 'Error: failed to write cmd to server' )
                return 1

            error_msg = 'Error: failed to close server fifo - %s'
            os.close( fd_server )

            error_msg = 'Error: failed to read client fifo - %s'

            # wait for write to fd
            select.select( [fd_client], [], [], None )

            reply = os.read( fd_client, 1024 )

            os.close( fd_client )

            reply = reply.decode( 'utf-8' )
            print( reply[1:] )
            return int(reply[0])

        except IOError as e:
            print( error_msg % (e,) )
            return 1

if __name__ == '__main__':
    sys.exit( WbGitAskPass().askPass( sys.argv[1] ) )
