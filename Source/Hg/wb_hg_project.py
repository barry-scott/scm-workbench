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

    def __calculateStatus( self ):
        self.all_file_state = {}

        repo_root = self.path()

        hg_dir = repo_root / '.hg'

        all_folders = set( [repo_root] )
        while len(all_folders) > 0:
            folder = all_folders.pop()

            print( 'qqq __calculateStatus folder %r' % (folder,) )

            for filename in folder.iterdir():
                abs_path = folder / filename

                print( 'qqq __calculateStatus abs_path %r' % (abs_path,) )

                repo_relative = abs_path.relative_to( repo_root )

                if abs_path.is_dir():
                    if abs_path != hg_dir:
                        all_folders.add( abs_path )

                        self.all_file_state[ str(repo_relative) ] = WbHgFileState( self, repo_relative )
                        self.all_file_state[ str(repo_relative) ].setIsDir()

                else:
                    self.all_file_state[ str(repo_relative) ] = WbHgFileState( self, repo_relative )
            
        print( '__calculateStatus manifest()' )
        for nodeid, permission, executable, symlink, filepath in self.repo.manifest():
            filepath = filepath.decode( sys.getfilesystemencoding() )
            print( '__calculateStatus manifest() filepath %r' % (filepath,) )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, pathlib.Path( filepath ) )

            self.all_file_state[ filepath ].setManifest( nodeid, permission, executable, symlink )

        print( '__calculateStatus status()' )
        for state, filepath in self.repo.status( all=True, ignored=True ):
            state = state.decode( 'utf-8' )
            filepath = filepath.decode( sys.getfilesystemencoding() )
            print( '__calculateStatus status() filepath %r' % (filepath,) )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbHgFileState( self, pathlib.Path( filepath ) )

            self.all_file_state[ filepath ].setState( state )

            if state in 'AMR':
                self.__num_uncommitted_files += 1

    def __updateTree( self, path ):
        path_parts = path.split( '/' )

        print( 'qqq __updateTree %r' % (path,) )


        node = self.tree
        for depth in range( len(path_parts) - 1 ):
            node_name = path_parts[ depth ]
            if node_name in node.all_folders:
                node = node.all_folders[ node_name ]

            else:
                new_node = HgProjectTreeNode( self, node_name, pathlib.Path( '/'.join( path_parts[0:depth+1] ) ) )
                node.all_folders[ node_name ] = new_node
                node = new_node

        node.all_files[ path_parts[-1] ] = path

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def getFileState( self, filename ):
        # status only has enties for none CURRENT status files
        return self.all_file_state[ str(filename) ]

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
    def cmdStage( self, filename ):
        self._debug( 'cmdStage( %r )' % (filename,) )
        return

        self.repo.hg.add( filename )
        self.__stale_status = True

    def cmdUnstage( self, rev, filename ):
        self._debug( 'cmdUnstage( %r )' % (filename,) )
        return

        self.repo.hg.reset( 'HEAD', filename, mixed=True )
        self.__stale_status = True

    def cmdRevert( self, rev, filename ):
        self._debug( 'cmdRevert( %r )' % (filename,) )
        return

        self.repo.hg.checkout( 'HEAD', filename )
        self.__stale_status = True

    def cmdDelete( self, filename ):
        return
        (self.prefs_project.path / filename).unlink()
        self.__stale_status = True

    def cmdCommit( self, message ):
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
        print( 'qqq WbHgFileState( %r )' % (filepath,) )
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
        path = pathlib.Path( self.__project.path() ) / self.unstaged_diff.a_path
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ):
        abs_path = self.__project.path() / self.__filepath
        text = self.__project.repo.cat( str(abs_path) )
        text = data.decode( 'utf-8' )
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
        self.all_folders = {}
        self.all_files = {}

    def __repr__( self ):
        return '<HgProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def isNotEqual( self, other ):
        return (self.__path != other.__path
            or self.project.isNotEqual( other.project ))

    def __lt__( self, other ):
        return self.name < other.name

    def relativePath( self ):
        return self.__path

    def absolutePath( self ):
        return self.project.path() / self.__path

    def getStatusEntry( self, name ):
        path = self.all_files[ name ]
        if path in self.project.all_file_state:
            entry = self.project.all_file_state[ path ]
        else:
            entry = WbHgFileState( self.project, None )

        return entry
