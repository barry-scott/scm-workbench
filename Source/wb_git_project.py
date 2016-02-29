'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_project.py

'''
import pathlib

import warnings
# pygit2 is emitting warning on import
with warnings.catch_warnings():
    warnings.simplefilter( 'ignore' )

    import pygit2

class GitProject:
    def __init__( self, prefs_project ):
        self.prefs_project = prefs_project
        self.repo = pygit2.Repository( str( prefs_project.path / '.git' ) )

        self.tree = GitProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.index = self.repo.index
        self.status = {}

    def path( self ):
        return self.prefs_project.path

    def update( self ):
        print( 'qqq: GitProject( %s ).update()' % (self.path(),) )
        self.index.read( False )

        for entry in self.index:
            self.__updateTree( entry.path )

        self.status = self.repo.status()

        for path in self.status:
            self.__updateTree( path )

    def __updateTree( self, path ):
        path_parts = path.split( '/' )

        node = self.tree
        for depth in range( len(path_parts) - 1 ):
            node_name = path_parts[ depth ]
            if node_name in node.all_folders:
                node = node.all_folders[ node_name ]

            else:
                new_node = GitProjectTreeNode( self, node_name, pathlib.Path( '/'.join( path_parts[0:depth+1] ) ) )
                node.all_folders[ node_name ] = new_node
                node = new_node

        node.all_files[ path_parts[-1] ] = path

class GitProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.__path = path
        self.all_folders = {}
        self.all_files = {}

    def __lt__( self, other ):
        return self.name < other.name

    def path( self ):
        return self.project.path() / self.__path

    def state( self, name ):
        try:
            mode = self.project.index[ self.all_files[ name ] ].mode

        except KeyError:
            mode = 0

        state = self.project.status.get( self.all_files[ name ], 0 )

        return (mode, state)
