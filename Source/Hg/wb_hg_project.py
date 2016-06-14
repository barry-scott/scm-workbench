'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_project.py

'''
import pathlib
import sys

import hglib

class HgProject:
    def __init__( self, app, prefs_project ):
        self.app = app
        self._debug = self.app._debugHgProject

        self.prefs_project = prefs_project
        self.repo = hglib.open( str( prefs_project.path ) )

        self.tree = HgProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.all_file_state = {}
        self.__stale_status = False

        self.__num_uncommitted_files = 0

    def scmType( self ):
        return 'hg'

    def getBranchName( self ):
        return '-- TBD --' # QQQ missing code

    # return a new HgProject that can be used in another thread
    def newInstance( self ):
        return HgProject( self.app, self.prefs_project )

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<HgProject: %s>' % (self.prefs_project.name,)

    def projectName( self ):
        return self.prefs_project.name

    def path( self ):
        return self.prefs_project.path

    def headRefName( self ):
        return 'unknown'

    def numUncommittedFiles( self ):
        return self.__num_uncommitted_files

    def updateState( self ):
        self._debug( 'updateState() is_stale %r' % (self.__stale_status,) )

        self.__stale_status = False

        # rebuild the tree
        self.tree = HgProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        self.__calculateStatus()

        for path in self.all_file_state:
            self.__updateTree( path )

        #self.dumpTree()

    def __calculateStatus( self ):
        self.all_file_state = {}

        repo_root = self.path()

        hg_dir = repo_root / '.hg'

        all_folders = set( [repo_root] )
        while len(all_folders) > 0:
            folder = all_folders.pop()

            for filename in folder.iterdir():
                abs_path = folder / filename

                repo_relative = abs_path.relative_to( repo_root )

                if abs_path.is_dir():
                    if abs_path != hg_dir:
                        all_folders.add( abs_path )

                        self.all_file_state[ repo_relative ] = WbHgFileState( self, repo_relative )
                        self.all_file_state[ repo_relative ].setIsDir()

                else:
                    self.all_file_state[ repo_relative ] = WbHgFileState( self, repo_relative )
            
        for nodeid, permission, executable, symlink, filepath in self.repo.manifest():
            filepath = self.pathForWb( filepath )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, filepath )

            self.all_file_state[ filepath ].setManifest( nodeid, permission, executable, symlink )

        for state, filepath in self.repo.status( all=True, ignored=True ):
            state = state.decode( 'utf-8' )
            filepath = self.pathForWb( filepath )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, filepath )

            self.all_file_state[ filepath ].setState( state )

            if state in ('A', 'M', 'R'):
                self.__num_uncommitted_files += 1

    def __updateTree( self, path ):
        self._debug( '__updateTree path %r' % (path,) )
        node = self.tree

        self._debug( '__updateTree path.parts %r' % (path.parts,) )

        for index, name in enumerate( path.parts[0:-1] ):
            self._debug( '__updateTree name %r at node %r' % (name,node) )

            if not node.hasFolder( name ):
                node.addFolder( name, HgProjectTreeNode( self, name, pathlib.Path( *path.parts[0:index+1] ) ) )

            node = node.getFolder( name )

        self._debug( '__updateTree addFile %r to node %r' % (path, node) )
        node.addFile( path )

    def dumpTree( self ):
        self.tree._dumpTree( 0 )

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def getFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        # status only has enties for none CURRENT status files
        return self.all_file_state[ filename ]

    def getReportStagedFiles( self ):
        all_staged_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isStagedNew():
                all_staged_files.append( (T_('New file'), filename) )

            elif file_state.isStagedModified():
                all_staged_files.append( (T_('Modified'), filename) )

            elif file_state.isStagedDeleted():
                all_staged_files.append( (T_('Deleted'), filename) )

        return all_staged_files

    def getReportUntrackedFiles( self ):
        all_untracked_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isUntracked():
                all_untracked_files.append( (T_('New file'), filename) )

            elif file_state.isUnstagedModified():
                all_untracked_files.append( (T_('Modified'), filename) )

            elif file_state.isUnstagedDeleted():
                all_untracked_files.append( (T_('Deleted'), filename) )

        return all_untracked_files

    def canPush( self ):
        return False
        for commit in self.repo.iter_commits( None, max_count=1 ):
            commit_id = commit.hexsha

            for remote in self.repo.remotes:
                for ref in remote.refs:
                    remote_id = ref.commit.hexsha

                    return commit_id != remote_id

        return False

    def getUnpushedCommits( self ):
        return []

        last_pushed_commit_id = ''
        for remote in self.repo.remotes:
            for ref in remote.refs:
                last_pushed_commit_id = ref.commit.hexsha

        all_unpushed_commits = []
        for commit in self.repo.iter_commits( None ):
            commit_id = commit.hexsha

            if last_pushed_commit_id == commit_id:
                break

            all_unpushed_commits.append( commit )

        return all_unpushed_commits

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the hg <cmd> in behavior
    #
    #------------------------------------------------------------
    def pathForHg( self, path ):
        assert isinstance( path, pathlib.Path )
        # return abs path
        return str( self.path() / path ).encode( sys.getfilesystemencoding() )

    def pathForWb( self, bytes_path ):
        assert type( bytes_path ) == bytes
        return pathlib.Path( bytes_path.decode( sys.getfilesystemencoding() ) )

    def cmdCat( self, filename ):
        path = self.pathForHg( filename )
        byte_result = self.repo.cat( [path] )
        return byte_result.decode( 'utf-8' )

    def cmdAdd( self, filename ):
        self._debug( 'cmdAdd( %r )' % (filename,) )
        return

        self.repo.add( self.pathForHg( filename ) )
        self.__stale_status = True

    def cmdRevert( self, filename ):
        self._debug( 'cmdRevert( %r )' % (filename,) )
        return

        self.repo.revert( self.pathForHg( filename ) )
        self.__stale_status = True

    def cmdDelete( self, filename ):
        return

        self.repo.delete( self.pathForHg( filename ) )

        self.__stale_status = True

    def cmdCommit( self, message ):
        return

        self.__stale_status = True
        return self.index.commit( message )

    def cmdCommitLogForRepository( self, limit=None, since=None, until=None ):
        return []

        all_commit_logs = []

        kwds = {}
        if limit is not None:
            kwds['max_count'] = limit
        if since is not None:
            kwds['since'] = since
        if since is not None:
            kwds['until'] = until

        for commit in self.repo.iter_commits( None, **kwds ):
            all_commit_logs.append( HgCommitLogNode( commit ) )

        self.__addCommitChangeInformation( all_commit_logs )
        return all_commit_logs

    def cmdCommitLogForFile( self, filename, limit=None, since=None, until=None ):
        return []

        all_commit_logs = []

        kwds = {}
        if limit is not None:
            kwds['max_count'] = limit
        if since is not None:
            kwds['since'] = since
        if since is not None:
            kwds['until'] = until

        for commit in self.repo.iter_commits( None, str(filename), **kwds ):
            all_commit_logs.append( HgCommitLogNode( commit ) )

        self.__addCommitChangeInformation( all_commit_logs )
        return all_commit_logs

    def __addCommitChangeInformation( self, all_commit_logs ):
        # now calculate what was added, deleted and modified in each commit
        for offset in range( len(all_commit_logs) ):
            new_tree = all_commit_logs[ offset ].commitTree()
            old_tree = all_commit_logs[ offset ].commitPreviousTree()

            all_new = {}
            self.__treeToDict( new_tree, all_new )
            new_set = set(all_new)

            if old_tree is None:
                all_commit_logs[ offset ]._addChanges( new_set, set(), [], set() )

            else:
                all_old = {}
                self.__treeToDict( old_tree, all_old )

                old_set = set(all_old)

                all_added = new_set - old_set
                all_deleted = old_set - new_set

                all_renamed = []

                if len(all_added) > 0:
                    all_old_id_to_name = {}
                    for name, id_ in all_old.items():
                        all_old_id_to_name[ id_ ] = name

                    for name in list(all_added):
                        id_ = all_new[ name ]

                        if id_ in all_old_id_to_name:
                            all_added.remove( name )
                            all_deleted.remove( all_old_id_to_name[ id_ ] )
                            all_renamed.append( (name, all_old_id_to_name[ id_ ]) )

                all_modified = set()

                for key in all_new:
                    if( key in all_old
                    and all_new[ key ] != all_old[ key ] ):
                        all_modified.add( key )

                all_commit_logs[ offset ]._addChanges( all_added, all_deleted, all_renamed, all_modified )

    def __treeToDict( self, tree, all_entries ):
        for blob in tree:
            if blob.type == 'blob':
                all_entries[ blob.path ] = blob.hexsha

        for child in tree.trees:
            self.__treeToDict( child, all_entries )

    def cmdPull( self, progress_callback, info_callback ):
        self._debug( 'cmdPull()' )
        return

        for remote in self.repo.remotes:
            for info in remote.pull( progress=Progress( progress_callback ) ):
                info_callback( info )

    def cmdPush( self, progress_callback, info_callback ):
        self._debug( 'cmdPush()' )
        return

        for remote in self.repo.remotes:
            for info in remote.push( progress=Progress( progress_callback ) ):
                info_callback( info )

class WbHgFileState:
    def __init__( self, project, filepath ):
        self.__project = project
        self.__filepath = filepath

        self.__is_dir = False

        self.__state = ''

        self.__nodeid = None
        self.__permission = None
        self.__executable = None
        self.__symlink = None

    def setState( self, state ):
        self.__state = state.decode('utf-8')

    def __repr__( self ):
        return ('<WbHgFileState: %s %s %s>' %
                (self.__filepath, self.__state, self.__nodeid))

    def setIsDir( self ):
        self.__is_dir = True

    def isDir( self ):
        return self.__is_dir

    def setManifest( self, nodeid, permission, executable, symlink ):
        self.__nodeid = nodeid.decode('utf-8')
        self.__permission = permission
        self.__executable = executable
        self.__symlink = symlink

    def setState( self, state ):
        self.__state = state

    def getAbbreviatedStatus( self ):
        return self.__state

    def getStagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return ''

    def getUnstagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return self.getAbbreviatedStatus()

    def isTracked( self ):
        return self.__nodeid is not None

    def isNew( self ):
        return self.__state == 'A'

    def isModified( self ):
        return self.__state == 'M'

    def isDeleted( self ):
        return self.__state == 'R'

    def isUntracked( self ):
        return self.__state == '?'

    def canDiffHeadVsWorking( self ):
        return self.isModified()

    def getTextLinesWorking( self ):
        path = pathlib.Path( self.__project.path() ) / self.__filepath
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ):
        text = self.__project.cmdCat( self.__filepath )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

class HgCommitLogNode:
    def __init__( self, commit ):
        self.__commit = commit
        self.__all_changes = []

    def _addChanges( self, all_added, all_deleted, all_renamed, all_modified ):
        for name in all_added:
            self.__all_changes.append( ('A', name, '' ) )

        for name in all_deleted:
            self.__all_changes.append( ('D', name, '' ) )

        for name, old_name in all_renamed:
            self.__all_changes.append( ('R', name, old_name ) )

        for name in all_modified:
            self.__all_changes.append( ('M', name, '' ) )

    def commitTree( self ):
        return self.__commit.tree

    def commitPreviousTree( self ):
        if len(self.__commit.parents) == 0:
            return None

        previous_commit = self.__commit.parents[0]
        return previous_commit.tree

    def commitTreeDict( self ):
        all_entries = {}
        self.__treeToDict( self.commitTree(), all_entries )
        return all_entries

    def commitPreviousTreeDict( self ):
        all_entries = {}

        tree = self.commitPreviousTree()
        if tree is not None:
            self.__treeToDict( tree, all_entries )

        return all_entries

    def commitIdString( self ):
        return self.__commit.hexsha

    def commitAuthor( self ):
        return self.__commit.author.name

    def commitAuthorEmail( self ):
        return self.__commit.author.email

    def commitDate( self ):
        return self.__commit.committed_datetime

    def commitMessage( self ):
        return self.__commit.message

    def commitFileChanges( self ):
        return self.__all_changes

class HgProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.__path = path
        self.__all_folders = {}
        self.__all_files = {}

    def __repr__( self ):
        return '<HgProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def addFile( self, path ):
        assert path.name != ''
        self.__all_files[ path.name ] = path

    def getAllFileNames( self ):
        return self.__all_files.keys()

    def addFolder( self, name, node ):
        assert type(name) == str and name != '', 'name %r, node %r' % (name, node)
        assert isinstance( node, HgProjectTreeNode )
        self.__all_folders[ name ] = node

    def getFolder( self, name ):
        assert type(name) == str
        return self.__all_folders[ name ]

    def getAllFolderNodes( self ):
        return self.__all_folders.values()

    def getAllFolderNames( self ):
        return self.__all_folders.keys()

    def hasFolder( self, name ):
        assert type(name) == str
        return name in self.__all_folders

    def _dumpTree( self, indent ):
        self.project._debug( 'dump: %*s%r' % (indent, '', self) )

        for file in sorted( self.__all_files ):
            self.project._debug( 'dump %*s   file: %r' % (indent, '', file) )

        for folder in sorted( self.__all_folders ):
            self.__all_folders[ folder ]._dumpTree( indent+4 )

    def isNotEqual( self, other ):
        return (self.relativePath() != other.relativePath()
            or self.project.isNotEqual( other.project ))

    def __lt__( self, other ):
        return self.name < other.name

    def relativePath( self ):
        return self.__path

    def absolutePath( self ):
        return self.project.path() / self.__path

    def getStatusEntry( self, name ):
        path = self.__all_files[ name ]

        if path in self.project.all_file_state:
            entry = self.project.all_file_state[ path ]

        else:
            entry = WbHgFileState( self.project, None )

        return entry
