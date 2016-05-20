#!/usr/bin/python3
import sys
import os

import git

url = 'https://github.com/barry-scott/git-workbench.git'

target = os.path.join( os.environ['HOME'], 'tmpdir/clone' )

class QqqRemoteProgress(git.RemoteProgress):
    def __init__( self ):
        super().__init__()

    def update( self, op_code, cur_count, max_count=None, message='' ):
        self.prog_func( op_code, cur_count, max_count, message )
        print( '----------------------------------------' )
        print( 'op_code', op_code )
        print( 'cur_count', cur_count )
        print( 'max_count', max_count )
        print( 'message', message )

c = QqqRemoteProgress()

# (url, to_path, progress=None, env=None, **kwargs)
x = git.Repo.clone_from( url, target, progress=c )
print( x )
