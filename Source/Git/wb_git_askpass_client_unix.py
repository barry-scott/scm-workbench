'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_askpass_client_unix.py

    called with argv[1:] as the prompt
    expects a single line output as response.

'''
import sys
import os
import pathlib
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
        fifo_dir = pathlib.Path( tempfile.gettempdir() ) / e.pw_name

        client_fifo = fifo_dir / self.fifo_name_client
        server_fifo = fifo_dir / self.fifo_name_server

        try:
            error_msg = 'Error: failed to open fifo - %s'
            fd_server = os.open( str(server_fifo), os.O_WRONLY|os.O_NONBLOCK )

            error_msg = 'Error: failed to open fifo - %s'
            fd_client = os.open( str(client_fifo), os.O_RDONLY|os.O_NONBLOCK )

            prompt = prompt.encode( 'utf-8' )

            error_msg = 'Error: failed to write cmd to server - %s'
            size = os.write( fd_server, prompt )
            if size != len(prompt):
                print( 'Error: failed to write cmd to server' )
                return 1

            error_msg = 'Error: failed to close server fifo - %s'
            os.close( fd_server )

            error_msg = 'Error: failed to read client fifo - %s'

            poll = select.poll()
            poll.register( fd_client, select.POLLIN )
            poll.poll()

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
