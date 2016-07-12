'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_project.py

'''
import pathlib
import sys
import tempfile

import pysvn

import wb_svn_utils
import wb_read_file

ClientError = pysvn.ClientError

class SvnProject:
    svn_depth_empty = pysvn.depth.empty
    svn_depth_infinity = pysvn.depth.infinity

    svn_rev_head = pysvn.Revision( pysvn.opt_revision_kind.head )
    svn_rev_base = pysvn.Revision( pysvn.opt_revision_kind.base )
    svn_rev_working = pysvn.Revision( pysvn.opt_revision_kind.working )

    def __init__( self, app, prefs_project ):
        self.app = app

        self._debug = self.app._debugSvnProject
        self._debugUpdateTree = self.app._debugSvnUpdateTree

        self.__notification_of_files_in_conflict = 0

        self.prefs_project = prefs_project
        self.client_fg = pysvn.Client()
        self.client_fg.exception_style = 1
        self.client_fg.commit_info_style = 2
        self.client_fg.callback_notify = self.svnCallbackNotify

        self.client_bg = pysvn.Client()
        self.client_bg.exception_style = 1
        self.client_bg.commit_info_style = 2
        self.client_bg.callback_notify = self.svnCallbackNotify

        self.tree = SvnProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = SvnProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.all_file_state = {}
        self.__stale_status = False

        self.__num_uncommitted_files = 0

    def scmType( self ):
        return 'svn'

    def getBranchName( self ):
        return ''

    # return a new SvnProject that can be used in another thread
    def newInstance( self ):
        return SvnProject( self.app, self.prefs_project )

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<SvnProject: %s>' % (self.prefs_project.name,)

    def projectName( self ):
        return self.prefs_project.name

    def projectPath( self ):
        return self.prefs_project.path

    def headRefName( self ):
        return 'unknown'

    def numUncommittedFiles( self ):
        return self.__num_uncommitted_files

    def updateState( self ):
        self._debug( 'updateState() is_stale %r' % (self.__stale_status,) )

        self.__stale_status = False

        # rebuild the tree
        self.tree = SvnProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = SvnProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        self.__calculateStatus()

        for path in self.all_file_state:
            self.__updateTree( path, self.all_file_state[ path ].isDir() )

        #self.dumpTree()

    def __calculateStatus( self ):
        self.all_file_state = {}
        self.__num_uncommitted_files = 0

        repo_root = self.projectPath()

        svn_dir = repo_root / '.svn'

        all_folders = set( [repo_root] )
        while len(all_folders) > 0:
            folder = all_folders.pop()

            for filename in folder.iterdir():
                abs_path = folder / filename
                repo_relative = abs_path.relative_to( repo_root )

                if abs_path.is_dir():
                    if abs_path != svn_dir:
                        all_folders.add( abs_path )

                        self.all_file_state[ repo_relative ] = WbSvnFileState( self, repo_relative )
                        self.all_file_state[ repo_relative ].setIsDir()

                else:
                    self.all_file_state[ repo_relative ] = WbSvnFileState( self, repo_relative )

        for state in self.client_fg.status2( str(self.projectPath()) ):
            filepath = self.pathForWb( state.path )

            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbSvnFileState( self, filepath )

            self.all_file_state[ filepath ].setState( state )
            if state.kind == pysvn.node_kind.dir:
                self.all_file_state[ filepath ].setIsDir()

            if state.node_status in (pysvn.wc_status_kind.added, pysvn.wc_status_kind.modified, pysvn.wc_status_kind.deleted):
                self.__num_uncommitted_files += 1

    def __updateTree( self, path, is_dir ):
        self._debugUpdateTree( '__updateTree path %r' % (path,) )
        node = self.tree

        self._debugUpdateTree( '__updateTree path.parts %r' % (path.parts,) )

        if is_dir:
            parts = path.parts[:]

        else:
            parts = path.parts[0:-1]

        for index, name in enumerate( parts ):
            self._debugUpdateTree( '__updateTree name %r at node %r' % (name, node) )

            if not node.hasFolder( name ):
                node.addFolder( name, SvnProjectTreeNode( self, name, pathlib.Path( *path.parts[0:index+1] ) ) )

            node = node.getFolder( name )

        self._debugUpdateTree( '__updateTree addFile %r to node %r' % (path, node) )
        if not is_dir:
            node.addFileByName( path )

        self.flat_tree.addFileByPath( path )

    def dumpTree( self ):
        self.tree._dumpTree( 0 )

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def clientErrorToStrList( self, e ):
        client_error = []
        for message, _ in e.args[1]:
            client_error.append( message )

        return client_error

    def hasFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        return filename in self.all_file_state
        
    def getFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        # status only has enties for none CURRENT status files
        return self.all_file_state[ filename ]

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the svn <cmd> in behavior
    #
    #------------------------------------------------------------
    def pathForSvn( self, path ):
        assert isinstance( path, pathlib.Path )
        # return abs path
        return str( self.projectPath() / path )

    def pathForWb( self, str_path ):
        assert type( str_path ) == str
        wb_path = pathlib.Path( str_path )
        if wb_path.is_absolute():
            wb_path = wb_path.relative_to( self.projectPath() )

        return wb_path

    # ------------------------------------------------------------
    def cmdAdd( self, filename ):
        self._debug( 'cmdAdd( %r )' % (filename,) )

        self.client_fg.add( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdRevert( self, filename ):
        self._debug( 'cmdRevert( %r )' % (filename,) )

        self.client_fg.revert( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdDelete( self, filename ):
        self._debug( 'cmdDelete( %r )' % (filename,) )
        self.client_fg.delete( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdDiffFolder( self, folder, head=False ):
        self._debug( 'cmdDiffFolder( %r )' % (folder,) )
        abs_folder = self.pathForSvn( folder )

        if head:
            old_rev = self.svn_rev_head

        else:
            old_rev = self.svn_rev_base

        diff_text = self.client_fg.diff(
            tempfile.gettempdir(),
            abs_folder, old_rev,
            abs_folder, self.svn_rev_working,
            recurse=True,
            relative_to_dir=str( self.projectPath() ),
            use_git_diff_format=True
            )

        return diff_text

    def cmdPropList( self, filename ):
        prop_list = self.client_fg.proplist( self.pathForSvn( filename ),
                            revision=self.svn_rev_working )

        if len(prop_list) == 0:
            prop_dict = {}

        else:
            Q, prop_dict = prop_list[0]

        return prop_dict

    def cmdPropDel( self, prop_name, filename ):
        self.client_fg.propdel( prop_name, self.pathForSvn( filename ) )

    def cmdPropSet( self, prop_name, prop_value, filename ):
        self.client_fg.propset( prop_name, prop_value, self.pathForSvn( filename ) )

    def cmdInfo( self, filename ):
        info = self.client_fg.info2( self.pathForSvn( filename ), recurse=False )
        # info is list of (path, entry)
        return info[0][1]

    def cmdCommitBg( self, message, all_filenames=None ):
        if all_filenames is None:
            # checkin all changes in the working copy
            all_revisions = self.client_fg.checkin(
                self.pathForSvn( self.projectPath() ),
                message,
                recurse=True )

        else:
            # checkin selected files only
            all_revisions = self.client_bg.checkin(
                [self.pathForSvn( path ) for path in all_filenames],
                message,
                recurse=False )

        self.__stale_status = True

        return 'R%d' % (all_revisions[0].revision.number,)

    def cmdUpdateBg( self, filename, revision, depth ):
        self._debug( 'cmdUpdateBg( %r, %r, %r )' % (filename, revision, depth) )
        all_revisions = self.client_bg.update(
                self.pathForSvn( filename ),
                revision=revision,
                depth=depth )

        return all_revisions

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

        for commit in self.client_fg.iter_commits( None, **kwds ):
            all_commit_logs.append( SvnCommitLogNode( commit ) )

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

        for commit in self.client_fg.iter_commits( None, str(filename), **kwds ):
            all_commit_logs.append( SvnCommitLogNode( commit ) )

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

    def svnCallbackNotify( self, arg_dict ):
        # svnCallbackNotify typically is running on the background thread
        # for commands like update and checkin.
        #
        # update progress via the foreground thread to avoid calling Qt
        # on the background thread.
        #

        #print( 'QQQ Notify: %r' % (arg_dict,) )

        # nothing to print if no path
        if arg_dict['path'] == '':
            return

        action = arg_dict['action']
        if( action == pysvn.wc_notify_action.commit_postfix_txdelta
        or action == pysvn.wc_notify_action.annotate_revision ):
            self.app.runInForeground( self.app.top_window.progress.incEventCount, () )
            return

        if action in [pysvn.wc_notify_action.failed_lock,
                        pysvn.wc_notify_action.failed_unlock]:
            self.app.runInForeground( self.app.top_window.progress.incEventCount, () )
            return

        # see if we want to handle this action
        if wb_svn_utils.wcNotifyTypeLookup( arg_dict['action'] ) is None:
            return

        # reject updates for paths that have no change
        if( action == pysvn.wc_notify_action.update_update
        and arg_dict['content_state'] == pysvn.wc_notify_state.unknown
        and arg_dict['prop_state'] == pysvn.wc_notify_state.unknown ):
            return

        if wb_svn_utils.wcNotifyTypeLookup( action ) == 'U':
            # count the interesting update event
            self.app.runInForeground( self.app.top_window.progress.incEventCount, () )

        # count the number of files in conflict
        action_letter = wb_svn_utils.wcNotifyTypeLookup( action )
        if( arg_dict['content_state'] == pysvn.wc_notify_state.conflicted
        or arg_dict['prop_state'] == pysvn.wc_notify_state.conflicted ):
            action_letter = 'C'
            self.app.runInForeground( self.app.top_window.progress.incInConflictCount, () )

        # print anything that gets through the filter
        
        path = arg_dict['path']

        self.app.log.info( u'%s %s\n' % (action_letter, path) )

    def initNotificationOfFilesInConflictCount( self ):
        self.__notification_of_files_in_conflict = 0

    def getNotificationOfFilesInConflictCount( self ):
        return self.__notification_of_files_in_conflict

class WbSvnFileState:
    def __init__( self, project, filepath ):
        self.__project = project
        self.__filepath = filepath

        self.__is_dir = False

        self.__state = None

    def setState( self, state ):
        self.__state = state.decode('utf-8')

    def __repr__( self ):
        return ('<WbSvnFileState: %s %s %s>' %
                (self.__filepath, self.__state, self.__nodeid))

    def filePath( self ):
        return self.__filepath

    def setIsDir( self ):
        self.__is_dir = True

    def isDir( self ):
        return self.__is_dir

    def setState( self, state ):
        self.__state = state

    def getAbbreviatedStatus( self ):
        return wb_svn_utils.svnStatusFormat( self.__state )

    def getStagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return ''

    def getUnstagedAbbreviatedStatus( self ):
        # QQQ here for Git compat - bad OO design here
        return self.getAbbreviatedStatus()

    # ------------------------------------------------------------
    def isControlled( self ):
        return self.__state is not None and self.__state.is_versioned

    def isUncontrolled( self ):
        return self.__state is None or self.__state.node_status == pysvn.wc_status_kind.unversioned

    def isIgnored( self ):
        return self.__state is None or self.__state.node_status == pysvn.wc_status_kind.ignored

    # --------------------
    def isAdded( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.add

    def isModified( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.modified

    def isDeleted( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.deleted

    # ------------------------------------------------------------
    def canDiffHeadVsWorking( self ):
        return self.isModified()

    def getTextLinesWorking( self ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesBase( self ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        all_content_lines = self.__project.client_fg.cat(
                                    url_or_path=str(path),
                                    revision=self.svn_rev_base )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' ) 

        return all_content_lines

    def getTextLinesHead( self ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        all_content_lines = self.__project.client_fg.cat(
                                    url_or_path=str(path),
                                    revision=self.svn_rev_head )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' ) 

        return all_content_lines

class SvnCommitLogNode:
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

class SvnProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.is_by_path = False
        self.__path = path
        self.__all_folders = {}
        self.__all_files = {}

    def __repr__( self ):
        return '<SvnProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def isByPath( self ):
        return self.is_by_path

    def addFileByName( self, path ):
        assert path.name != ''
        self.__all_files[ path.name ] = path

    def addFileByPath( self, path ):
        assert isinstance( path, pathlib.Path )
        self.is_by_path = True
        path = path
        self.__all_files[ path ] = path

    def getAllFileNames( self ):
        return self.__all_files.keys()

    def addFolder( self, name, node ):
        assert type(name) == str, 'name %r, node %r' % (name, node)
        assert isinstance( node, SvnProjectTreeNode )

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
        return self.project.projectPath() / self.__path

    def getStatusEntry( self, name ):
        path = self.__all_files[ name ]

        if path in self.project.all_file_state:
            entry = self.project.all_file_state[ path ]

        else:
            entry = WbSvnFileState( self.project, None )

        return entry
