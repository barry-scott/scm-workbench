'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_project.py

'''
import pathlib
import pygit2

class GitProject:
    def __init__( self, prefs_project ):
        self.prefs_project = prefs_project
        self.repo = pygit2.Repository( str( prefs_project.path / '.git' ) )

        self.tree = GitProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.status = {}

        self.__dirty = False

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<GitProject: %s>' % (self.prefs_project.name,)

    def path( self ):
        return self.prefs_project.path

    def saveChanges( self ):
        assert self.__dirty, 'Only call saveChanges if something was changed'
        self.__dirty = False
        self.repo.index.write()
        self.updateState()

    def updateState( self ):
        assert not self.__dirty, 'repo is dirty, forgot to call saveChanges?'

        # rebuild the tree
        self.tree = GitProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        self.repo.index.read( False )

        for entry in self.repo.index:
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

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def getStatus( self, filename ):
        return self.status[ str(filename) ]

    def getDiffObjects( self, filename ):
        state = self.status[ str(filename) ]

        # The id representing the filename contents at HEAD
        if (state&pygit2.GIT_STATUS_INDEX_NEW) != 0:
            head_id = None

        else:
            commit = self.repo.revparse_single( 'HEAD' )
            tree = commit.peel( pygit2.GIT_OBJ_TREE )
            tree_entry = self.__findFileInTree( tree, filename )
            head_id = tree_entry.id

        # The id representing the filename contents that is staging
        if( (state&pygit2.GIT_STATUS_INDEX_NEW) != 0
        or  (state&pygit2.GIT_STATUS_INDEX_MODIFIED) != 0 ):
            index_entry = self.repo.index[ str( filename ) ]
            staged_id = index_entry.id

        elif (state&pygit2.GIT_STATUS_INDEX_DELETED) != 0:
            staged_id = None

        else:
            staged_id = None

        # the path to the working copy
        working_path = self.path() / filename

        return WbGitDiffObjects( filename, state, head_id, staged_id, working_path )

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the git <cmd> in behavior
    #
    #------------------------------------------------------------
    def cmdStage( self, filename ):
        state = self.status[ str(filename) ]

        if (pygit2.GIT_STATUS_WT_DELETED&state) != 0:
            self.repo.index.remove( str(filename) )

        elif( (pygit2.GIT_STATUS_WT_MODIFIED&state) != 0
        or    (pygit2.GIT_STATUS_WT_NEW&state) != 0 ):
            self.repo.index.add( str(filename) )

        self.__dirty = True

    def cmdUnstage( self, rev, filename, reset_type ):
        state = self.status[ str(filename) ]

        if (state&pygit2.GIT_STATUS_INDEX_NEW) != 0:
            # new file just needs to be remove() from the index
            self.repo.index.remove( str(filename) )

        else:
            # modified or delete file needs
            # to be added back into index with there old value
            commit = self.repo.revparse_single( rev )
            tree = commit.peel( pygit2.GIT_OBJ_TREE )
            tree_entry = self.__findFileInTree( tree, filename )

            reset_entry = pygit2.IndexEntry( str(filename), tree_entry.id, tree_entry.filemode )
            self.repo.index.add( reset_entry )

        self.__dirty = True

    def cmdRevert( self, rev, filename ):
        # either a modified file or a deleted file
        # read the blob from HEAD and wite to disk

        commit = self.repo.revparse_single( rev )
        tree = commit.peel( pygit2.GIT_OBJ_TREE )
        tree_entry = self.__findFileInTree( tree, filename )

        blob = self.repo.get( tree_entry.id )

        with (self.prefs_project.path / filename).open( 'wb' ) as f:
            f.write( blob.data )

        self.__dirty = True

    def __findFileInTree( self, tree, filename ):
        # match all the folders
        for name in filename.parts[:-1]:
            for entry in tree:
                if name == entry.name:
                    if entry.filemode == pygit2.GIT_FILEMODE_TREE:
                        tree = self.repo.get( entry.id )
                    else:
                        raise KeyError( 'folder not in tree' )

        for entry in tree:
            if filename.name == entry.name and entry.filemode in (pygit2.GIT_FILEMODE_BLOB, pygit2.GIT_FILEMODE_BLOB_EXECUTABLE):
                return entry

        raise KeyError( 'file not in tree' )

class GitProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.__path = path
        self.all_folders = {}
        self.all_files = {}

    def __repr__( self ):
        return '<GitProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def isNotEqual( self, other ):
        return (self.__path != other.__path
            or self.project.isNotEqual( other.project ))

    def __lt__( self, other ):
        return self.name < other.name

    def relativePath( self ):
        return self.__path

    def absolutePath( self ):
        return self.project.path() / self.__path

    def state( self, name ):
        try:
            mode = self.project.repo.index[ self.all_files[ name ] ].mode

        except KeyError:
            mode = 0

        state = self.project.status.get( self.all_files[ name ], 0 )

        return (mode, state)

class WbGitDiffObjects:
    def __init__( self, filename, status, head_id, staged_id, working_path ):
        self.filename = filename
        self.status = status
        self.head_id = head_id
        self.staged_id = staged_id
        self.working_path = working_path

    def canDiffStaged( self ):
        return (self.status&(pygit2.GIT_STATUS_INDEX_NEW|pygit2.GIT_STATUS_INDEX_MODIFIED|pygit2.GIT_STATUS_INDEX_DELETED)) != 0

    def canDiffWorking( self ):
        return (self.status&(pygit2.GIT_STATUS_WT_MODIFIED|pygit2.GIT_STATUS_WT_DELETED)) != 0
