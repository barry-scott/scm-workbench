#!/usr/bin/python3
import sys
import os

import git

git.Git.GIT_PYTHON_TRACE = 'full'

url = 'https://github.com/barry-scott/git-workbench.git'

target = os.path.join( os.environ['HOME'], 'tmpdir/clone' )

class QqqRemoteProgress(git.RemoteProgress):
    def __init__( self, fn ):
        super().__init__()
        self.fn = fn

    def update( self, op_code, cur_count, max_count=None, message='' ):
        self.fn( op_code, cur_count, max_count, message )

stages = [
    (git.RemoteProgress.BEGIN, 'BEGIN'),
    (git.RemoteProgress.END, 'END'),
    (git.RemoteProgress.COUNTING, 'COUNTING'),
    (git.RemoteProgress.COMPRESSING, 'COMPRESSING'),
    (git.RemoteProgress.WRITING, 'WRITING'),
    (git.RemoteProgress.RECEIVING, 'RECEIVING'),
    (git.RemoteProgress.RESOLVING, 'RESOLVING'),
    (git.RemoteProgress.FINDING_SOURCES, 'FINDING_SOURCES'),
    (git.RemoteProgress.CHECKING_OUT, 'CHECKING_OUT'),
    ]

def opCodeToString( op_code ):
    all_names = []
    for mask, name in stages:
        if (op_code&mask) != 0:
            all_names.append( name )

    return ', '.join( all_names )

def progFunc( op_code, cur_count, max_count, message ):
    print( opCodeToString( op_code ), cur_count, max_count, message )

c = QqqRemoteProgress( progFunc )

# (url, to_path, progress=None, env=None, **kwargs)
print( git )
print( git.Repo.clone_from )
x = git.Repo.clone_from( url, target, progress=c )
print( x )
