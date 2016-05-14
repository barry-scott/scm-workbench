'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_project.py

'''
import pathlib

import git
import git.index

class GitProject:
    def __init__( self, app, prefs_project ):
        self.app = app
        self._debug = self.app._debugGitProject

        self.prefs_project = prefs_project
        self.repo = git.Repo( str( prefs_project.path ) )
        self.index = None

        self.tree = GitProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.all_file_state = {}

        self.__dirty_index = False
        self.__stale_index = False

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<GitProject: %s>' % (self.prefs_project.name,)

    def projectName( self ):
        return self.prefs_project.name

    def path( self ):
        return self.prefs_project.path

    def headRefName( self ):
        try:
            return self.repo.head.name

        except _pygit2.GitError:
            return ''

    def saveChanges( self ):
        self._debug( 'saveChanges() __dirty_index %r __stale_index %r' % (self.__dirty_index, self.__stale_index) )
        assert self.__dirty_index or self.__stale_index, 'Only call saveChanges if something was changed'

        if self.__dirty_index:
            self.repo.index.write()
            self.__dirty_index = False

        self.__stale_index = False

        self.updateState()

    def updateState( self ):
        self._debug( 'updateState()' )
        assert not self.__dirty_index, 'repo is dirty, forgot to call saveChanges?'

        # rebuild the tree
        self.tree = GitProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        self.__calculateStatus()

        for path in self.all_file_state:
            self.__updateTree( path )

    def __calculateStatus( self ):
        self.index = git.index.IndexFile( self.repo )

        head_vs_index = self.index.diff( self.repo.head.commit )
        index_vs_working = self.index.diff( None )
        # each ref to self.repo.untracked_files creates a new object
        # cache the value once/update
        untracked_files = self.repo.untracked_files

        self.all_file_state = {}
        for entry in self.index.entries.values():
            self.all_file_state[ entry.path ] = WbGitFileState( self.repo, entry )

        for diff in head_vs_index:
            if diff.b_path not in self.all_file_state:
                self.all_file_state[ diff.b_path ] = WbGitFileState( self.repo, None )
            self.all_file_state[ diff.b_path ]._addStaged( diff )

        for diff in index_vs_working:
            if diff.a_path not in self.all_file_state:
                self.all_file_state[ diff.a_path ] = WbGitFileState( self.repo, None )
            self.all_file_state[ diff.a_path ]._addUnstaged( diff )

        for path in untracked_files:
            if path not in self.all_file_state:
                self.all_file_state[ path ] = WbGitFileState( self.repo, None )

            self.all_file_state[ path ]._setUntracked()

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
    def getFileState( self, filename ):
        # status only has enties for none CURRENT status files
        return self.all_file_state[ str(filename) ]

    def getReportStagedFiles( self ):
        all_staged_files = []
        for filename, status in self.all_file_state.items():
            if (status&pygit2.GIT_STATUS_INDEX_NEW) != 0:
                all_staged_files.append( (T_('new file'), filename) )

            elif (status&pygit2.GIT_STATUS_INDEX_MODIFIED) != 0:
                all_staged_files.append( (T_('modified'), filename) )

            elif (status&pygit2.GIT_STATUS_INDEX_DELETED) != 0:
                all_staged_files.append( (T_('deleted'), filename) )

        return all_staged_files

    def getReportUntrackedFiles( self ):
        all_ubntracked_files = []
        for filename, status in self.all_file_state.items():
            if (status&pygit2.GIT_STATUS_WT_NEW) != 0:
                all_ubntracked_files.append( (T_('new file'), filename) )

            elif (status&pygit2.GIT_STATUS_WT_MODIFIED) != 0:
                all_ubntracked_files.append( (T_('modified'), filename) )

            elif (status&pygit2.GIT_STATUS_WT_DELETED) != 0:
                all_ubntracked_files.append( (T_('deleted'), filename) )

        return all_ubntracked_files


    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the git <cmd> in behavior
    #
    #------------------------------------------------------------
    def cmdStage( self, filename ):
        self._debug( 'cmdStage( %r )' % (filename,) )

        self.repo.git.add( filename )
        self.__stale_index = True

    def cmdUnstage( self, rev, filename ):
        self._debug( 'cmdUnstage( %r )' % (filename,) )

        self.repo.git.reset( 'HEAD', filename, mixed=True )
        self.__stale_index = True

    def cmdRevert( self, rev, filename ):
        self._debug( 'cmdRevert( %r )' % (filename,) )

        self.repo.git.checkout( 'HEAD', filename )
        self.__stale_index = True

    def cmdDelete( self, filename ):
        (self.prefs_project.path / filename).unlink()
        self.__stale_index = True

    def cmdCommit( self, message ):
        author = self.repo.default_signature
        comitter = self.repo.default_signature

        tree = self.repo.index.write_tree()

        last_commit = self.repo.revparse_single( 'HEAD' )

        commit_id = self.repo.create_commit(
            self.repo.head.name,            # branch to commit to
            author,
            comitter,
            message,
            tree,                           # tree in the new state
            [last_commit.id]                # the previous commit in the history
            )

        return commit_id

    def cmdCommitLogForRepository( self, limit=None, since=None, until=None ):
        all_commit_logs = []

        kwds = {}
        if limit is not None:
            kwds['max_count'] = limit
        if since is not None:
            kwds['since'] = since
        if since is not None:
            kwds['until'] = until

        for commit in self.repo.iter_commits( None, **kwds ):
            all_commit_logs.append( GitCommitLogNode( commit ) )

        self.__addCommitChangeInformation( all_commit_logs )
        return all_commit_logs

    def cmdCommitLogForFile( self, filename, limit=None, since=None, until=None ):
        all_commit_logs = []

        kwds = {}
        if limit is not None:
            kwds['max_count'] = limit
        if since is not None:
            kwds['since'] = since
        if since is not None:
            kwds['until'] = until

        for commit in self.repo.iter_commits( None, str(filename), **kwds ):
            all_commit_logs.append( GitCommitLogNode( commit ) )

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

class WbGitFileState:
    def __init__( self, repo, index_entry ):
        self.repo = repo
        self.index_entry = index_entry
        self.unstaged_diff = None
        self.staged_diff = None
        self.untracked = False

        # from the above calculate the following
        self.__state_calculated = False

        self.__staged_is_modified = False
        self.__unstaged_is_modified = False

        self.__staged_abbrev = None
        self.__unstaged_abbrev = None

        self.__head_blob = None
        self.__staged_blob = None

    def _addStaged( self, diff ):
        self.staged_diff = diff

    def _addUnstaged( self, diff ):
        self.unstaged_diff = diff

    def _setUntracked( self ):
        self.untracked = True

    # from the provided info work out
    # interesting properies
    def __calculateState( self ):
        if self.__state_calculated:
            return

        if self.staged_diff is None:
            self.__staged_abbrev = ''

        else:
            if self.staged_diff.renamed:
                self.__staged_abbrev = 'R'

            elif self.staged_diff.deleted_file:
                self.__staged_abbrev = 'A'

            elif self.staged_diff.new_file:
                self.__staged_abbrev = 'D'

            else:
                self.__staged_abbrev = 'M'
                self.__staged_is_modified = True
                self.__head_blob = self.staged_diff.b_blob
                self.__staged_blob = self.staged_diff.a_blob

        if  self.unstaged_diff is None:
            self.__unstaged_abbrev = ''

        else:
            if self.unstaged_diff.deleted_file:
                self.__unstaged_abbrev = 'D'

            elif self.unstaged_diff.new_file:
                self.__unstaged_abbrev = 'A'

            else:
                self.__unstaged_abbrev = 'M'
                self.__unstaged_is_modified = True
                if self.__head_blob is None:
                    self.__head_blob = self.unstaged_diff.a_blob

        self.__state_calculated = True

    def getStagedAbbreviatedStatus( self ):
        self.__calculateState()
        return self.__staged_abbrev

    def getUnstagedAbbreviatedStatus( self ):
        self.__calculateState()
        return self.__unstaged_abbrev
        return self.__unstaged_abbrev

    def isUntracked( self ):
        return self.untracked

    def canDiffHeadVsStaged( self ):
        return self.__staged_is_modified

    def canDiffStagedVsWorking( self ):
        return self.__unstaged_is_modified and self.__staged_is_modified

    def canDiffHeadVsWorking( self ):
        return self.__unstaged_is_modified

    def getTextLinesWorking( self ):
        path = pathlib.Path( self.repo.working_tree_dir ) / self.unstaged_diff.a_path
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ):
        blob = self.getHeadBlob()
        data = blob.data_stream.read()
        text = data.decode( 'utf-8' )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def getTextLinesStaged( self ):
        blob = self.getStagedBlob()
        data = blob.data_stream.read()
        text = data.decode( 'utf-8' )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def getHeadBlob( self ):
        return self.__head_blob

    def getStagedBlob( self ):
        return self.__staged_blob

class GitCommitLogNode:
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

    def getStatusEntry( self, name ):
        path = self.all_files[ name ]
        if path in self.project.all_file_state:
            entry = self.project.all_file_state[ path ]
        else:
            entry = WbGitFileState( self.project.repo, None )

        return entry
