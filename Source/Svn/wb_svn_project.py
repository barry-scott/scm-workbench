'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_project.py

'''
import pathlib
import tempfile
import pysvn

import wb_date
import wb_read_file
import wb_annotate_node
import wb_background_thread
import wb_svn_utils

ClientError = pysvn.ClientError

class SvnProject:
    svn_depth_empty = pysvn.depth.empty
    svn_depth_infinity = pysvn.depth.infinity

    svn_rev_head = pysvn.Revision( pysvn.opt_revision_kind.head )
    svn_rev_base = pysvn.Revision( pysvn.opt_revision_kind.base )
    svn_rev_working = pysvn.Revision( pysvn.opt_revision_kind.working )
    svn_rev_r0 = pysvn.Revision( pysvn.opt_revision_kind.number, 0 )

    def __init__( self, app, prefs_project, ui_components ):
        self.app = app
        self.ui_components = ui_components

        self._debug = self.app._debug_options._debugSvnProject
        self._debugUpdateTree = self.app._debug_options._debugSvnUpdateTree

        self.__notification_of_files_in_conflict = 0

        self.prefs_project = prefs_project
        self.__client_fg = pysvn.Client()
        self.__client_fg.exception_style = 1
        self.__client_fg.commit_info_style = 2
        self.__client_fg.callback_notify = self.svnCallbackNotify
        self.__client_fg.callback_get_login = self.ui_components.svnGetLogin
        self.__client_fg.callback_ssl_server_trust_prompt = self.ui_components.svnSslServerTrustPrompt

        self.__client_bg = pysvn.Client()
        self.__client_bg.exception_style = 1
        self.__client_bg.commit_info_style = 2
        self.__client_bg.callback_notify = self.svnCallbackNotify
        self.__client_bg.callback_get_login = wb_background_thread.GetReturnFromCallingFunctionOnMainThread( self.app, self.ui_components.svnGetLogin )
        self.__client_bg.callback_ssl_server_trust_prompt = wb_background_thread.GetReturnFromCallingFunctionOnMainThread( self.app, self.ui_components.svnSslServerTrustPrompt )

        if prefs_project is not None:
            self.tree = SvnProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )
            self.flat_tree = SvnProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

            self.all_file_state = {}
            self.__stale_status = False

            self.__num_uncommitted_files = 0

    def client( self ):
        if self.app.isForegroundThread():
            return self.__client_fg
        else:
            return self.__client_bg

    def scmType( self ):
        return 'svn'

    def switchToBranch( self, branch ):
        pass

    def getBranchName( self ):
        return ''

    def getAllBranchNames( self ):
        return [self.getBranchName()]

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

        if not self.projectPath().exists():
            self.app.log.error( T_('Project %(name)s folder %(folder)s has been deleted') %
                            {'name': self.projectName()
                            ,'folder': self.projectPath()} )

            self.all_file_state = {}
            self.__num_uncommitted_files = 0

        else:
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

        for state in self.client().status2( str(self.projectPath()) ):
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
    def logClientError( self, e, msg=None ):
        if msg is not None:
            self.app.log.error( msg )

        for line in self.clientErrorToStrList( e ):
            self.app.log.error( line )

    def clientErrorToStrList( self, e ):
        client_error = [e.args[0]]
        if len(e.args) >= 2:
            for message, _ in e.args[1]:
                # avoid duplicate error lines
                if message != e.args[0]:
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
    def cmdCheckout( self, url, wc_path ):
        assert self.prefs_project is None, 'Checkout is not allowed for an existing project'
        return self.client().checkout( url, str( wc_path ) )

    def cmdCleanup( self ):
        self._debug( 'cmdCleanup()' )
        self.client().cleanup( str( self.projectPath() ) )

    def cmdMkdir( self, filename ):
        self._debug( 'cmdMkdir()' )
        self.client().mkdir( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdAdd( self, filename, depth=None, force=False ):
        self._debug( 'cmdAdd( %r )' % (filename,) )

        self.client().add( self.pathForSvn( filename ), depth=depth, force=force )
        self.__stale_status = True

    def cmdRevert( self, filename, depth=None ):
        self._debug( 'cmdRevert( %r, %r )' % (filename, depth) )
        self._debug( 'cmdRevert 2 ( %r, %r )' % (self.pathForSvn( filename ), depth) )

        self.client().revert( self.pathForSvn( filename ), depth=depth )
        self.__stale_status = True

    def cmdResolved( self, filename ):
        self._debug( 'cmdResolved( %r )' % (filename,) )

        self.client().resolved( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdDelete( self, filename ):
        self._debug( 'cmdDelete( %r )' % (filename,) )
        self.client().remove( self.pathForSvn( filename ) )
        self.__stale_status = True

    def cmdRename( self, filename, new_filename ):
        filestate = self.getFileState( filename )
        if filestate.isControlled():
            self.client().move( self.pathForSvn( filename ), self.pathForSvn( new_filename ) )

        else:
            abs_path = filestate.absolutePath()
            new_abs_path = self.prefs_project.path / new_filename
            try:
                abs_path.rename( new_abs_path )

            except IOError as e:
                self.app.log.error( 'Renamed failed - %s' % (e,) )

        self.__stale_index = True

    def cmdDiffFolder( self, folder, head=False ):
        self._debug( 'cmdDiffFolder( %r )' % (folder,) )
        abs_folder = self.pathForSvn( folder )

        if head:
            old_rev = self.svn_rev_head

        else:
            old_rev = self.svn_rev_base

        diff_text = self.client().diff(
            tempfile.gettempdir(),
            abs_folder, old_rev,
            abs_folder, self.svn_rev_working,
            recurse=True,
            relative_to_dir=str( self.projectPath() ),
            use_git_diff_format=True
            )

        return diff_text

    def cmdDiffRevisionVsRevision( self, filename, old_rev, new_rev ):
        self._debug( 'cmdDiffRevisionVsRevision( %r )' % (filename,) )
        abs_filename = self.pathForSvn( filename )

        diff_text = self.client().diff(
            tempfile.gettempdir(),
            abs_filename, old_rev,
            abs_filename, new_rev,
            recurse=True,
            relative_to_dir=str( self.projectPath() ),
            use_git_diff_format=True
            )

        return diff_text

    def cmdPropList( self, filename ):
        prop_list = self.client().proplist( self.pathForSvn( filename ),
                            revision=self.svn_rev_working )

        if len(prop_list) == 0:
            prop_dict = {}

        else:
            Q, prop_dict = prop_list[0]

        return prop_dict

    def getTextLinesForRevisionFromUrl( self, url, rev_num ):
        all_content_lines = self.client().cat(
                                    url_or_path=url,
                                    revision=pysvn.Revision( pysvn.opt_revision_kind.number, rev_num ) )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' )

        return all_content_lines

    def cmdPropDel( self, prop_name, filename ):
        self.client().propdel( prop_name, self.pathForSvn( filename ) )

    def cmdPropSet( self, prop_name, prop_value, filename ):
        self.client().propset( prop_name, prop_value, self.pathForSvn( filename ) )

    def cmdInfo( self, filename ):
        info = self.client().info2( self.pathForSvn( filename ), depth=self.svn_depth_empty )
        # info is list of (path, entry)
        return info[0][1]

    def cmdLock( self, filename, message, force ):
        self.client().lock( self.pathForSvn( filename ), message, force=force )

    def cmdUnlock( self, filename, force ):
        self.client().unlock( self.pathForSvn( filename ), force=force )

    def cmdCommit( self, message, all_filenames=None ):
        if all_filenames is None:
            # checkin all changes in the working copy
            all_revisions = self.client().checkin(
                self.pathForSvn( self.projectPath() ),
                message,
                recurse=True )

        else:
            # checkin selected files only
            all_revisions = self.client().checkin(
                [self.pathForSvn( path ) for path in all_filenames],
                message,
                recurse=False )

        self.__stale_status = True

        return 'r%d' % (all_revisions[0].revision.number,)

    def cmdUpdate( self, filename, revision, depth ):
        self._debug( 'cmdUpdate( %r, %r, %r )' % (filename, revision, depth) )
        all_revisions = self.client().update(
                self.pathForSvn( filename ),
                revision=revision,
                depth=depth )

        return all_revisions

    def cmdCommitLogForFile( self, filename, limit=None, since=None, until=None ):
        if limit is None:
            limit = 0

        if until is not None:
            rev_start = pysvn.Revision( pysvn.opt_revision_kind.date, until )
        else:
            rev_start = self.svn_rev_head

        if since is not None:
            rev_end = pysvn.Revision( pysvn.opt_revision_kind.date, since )
        else:
            rev_end = self.svn_rev_r0

        all_logs = self.client().log(
                        self.pathForSvn( filename ),
                        revision_start=rev_start,
                        revision_end=rev_end,
                        limit=limit,
                        discover_changed_paths=True )

        return all_logs

    def cmdTagsForFile( self, filename, oldest_revision=0 ):
        tags_url = self.__tagsUrlForFile( filename )
        if tags_url is None:
            return {}

        all_tag_names = set()
        all_tag_logs = []

        for log in self.client().log( tags_url, discover_changed_paths=True ):
            for changed_path in log.changed_paths:
                if( changed_path.copyfrom_revision is not None
                and changed_path.copyfrom_revision.number >= oldest_revision ):
                    tag_name = changed_path.path.split( '/' )[-1]
                    if tag_name not in all_tag_names:
                        all_tag_names.add( tag_name )

                        log.is_tag = True
                        log.tag_name = tag_name
                        all_tag_logs.append( log )

        return all_tag_logs

    def __tagsUrlForFile( self, filename ):
        info = self.cmdInfo( filename )
        return self.expandTagsUrl( self.prefs_project.tags_url, info['URL'] )

    def expandTagsUrl( self, tags_url, filename_url ):
        if tags_url is None or tags_url == '':
            return  None

        tags_url_parts = tags_url.split('/')
        wild_parts = 0
        while tags_url_parts[-1] == '*':
            del tags_url_parts[-1]
            wild_parts += 1

        if wild_parts == 0:
            return tags_url

        top_url = self.cmdInfo( self.projectPath() )['URL']

        # replace wild_part dirs from the filename_url
        assert filename_url[0:len(top_url)] == top_url

        suffix_parts = filename_url[len(top_url)+1:].split('/')
        tags_url_parts.extend( suffix_parts[0:wild_parts] )

        return '/'.join( tags_url_parts )

    def cmdAnnotationForFile( self, filename ):
        rev_start = self.svn_rev_r0
        rev_end = self.svn_rev_head

        all_svn_annotation_nodes = self.client().annotate2(
                        self.pathForSvn( filename ),
                        revision_start=rev_start,
                        revision_end=rev_end )

        all_annotation_nodes = []

        for node in all_svn_annotation_nodes:
            all_annotation_nodes.append( wb_annotate_node.AnnotateNode(
                    node['number']+1,
                    node['line'],
                    node['revision'].number ) )

        return all_annotation_nodes

    def cmdCommitLogForAnnotateFile( self, filename, rev_start_num, rev_end_num ):
        rev_start = pysvn.Revision( pysvn.opt_revision_kind.number, rev_start_num )
        rev_end = pysvn.Revision( pysvn.opt_revision_kind.number, rev_end_num )

        all_logs = self.client().log(
                        self.pathForSvn( filename ),
                        revision_start=rev_start,
                        revision_end=rev_end,
                        strict_node_history=False,      # follow copy and move
                        discover_changed_paths=False )

        return dict( [(log['revision'].number, SvnCommitLogNode( log )) for log in all_logs] )

    def svnCallbackNotify( self, arg_dict ):
        # svnCallbackNotify typically is running on the background thread
        # for commands like checkout, update and checkin.
        #
        # update progress via the foreground thread to avoid calling Qt
        # on the background thread.
        #

        # nothing to print if no path
        if arg_dict['path'] == '':
            return

        action = arg_dict['action']

        if action in (pysvn.wc_notify_action.commit_postfix_txdelta
                      ,pysvn.wc_notify_action.commit_modified
                      ,pysvn.wc_notify_action.commit_added
                      ,pysvn.wc_notify_action.commit_copied
                      ,pysvn.wc_notify_action.commit_copied_replaced
                      ,pysvn.wc_notify_action.commit_deleted
                      ,pysvn.wc_notify_action.commit_replaced
                      ,pysvn.wc_notify_action.annotate_revision):
            self.app.runInForeground( self.app.top_window.progress.incEventCount, () )
            return

        if action == pysvn.wc_notify_action.failed_lock:
            self.app.log.error( T_('Failed to lock') )
            return

        if action == pysvn.wc_notify_action.failed_unlock:
            self.app.log.error( T_('Failed to unlock') )
            return

        # see if we want to handle this action
        if wb_svn_utils.wcNotifyTypeLookup( action ) is None:
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

        self.app.log.info( u'%s   %s' % (action_letter, path) )

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

    def __repr__( self ):
        return ('<WbSvnFileState: %s %s>' %
                (self.__filepath, self.__state))

    def relativePath( self ):
        return self.__filepath

    def absolutePath( self ):
        return self.__project.projectPath() / self.__filepath

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

    def canCommit( self ):
        return (self.__state is not None
                and self.__state.node_status in (pysvn.wc_status_kind.added, pysvn.wc_status_kind.modified, pysvn.wc_status_kind.deleted))

    # --------------------
    def isAdded( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.added

    def isModified( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.modified

    def isDeleted( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.deleted

    def isConflicted( self ):
        return self.__state is not None and self.__state.node_status == pysvn.wc_status_kind.conflicted

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
        all_content_lines = self.__project.client().cat(
                                    url_or_path=str(path),
                                    revision=self.__project.svn_rev_base )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' )

        return all_content_lines

    def getTextLinesHead( self ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        all_content_lines = self.__project.client().cat(
                                    url_or_path=str(path),
                                    revision=self.__project.svn_rev_head )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' )

        return all_content_lines

    def getTextLinesForRevision( self, revision ):
        path = pathlib.Path( self.__project.projectPath() ) / self.__filepath
        all_content_lines = self.__project.client().cat(
                                    url_or_path=str(path),
                                    revision=revision )

        all_content_lines = wb_read_file.contentsAsUnicode( all_content_lines ).split( '\n' )

        return all_content_lines

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

class SvnCommitLogNode:
    def __init__( self, node ):
        self.__node = node

    def commitId( self ):
        return self.__node['revision'].number

    def commitIdString( self ):
        return '%d' % (self.commitId(),)

    def commitAuthor( self ):
        return self.__node['author']

    def commitAuthorEmail( self ):
        return ''

    def commitDate( self ):
        return wb_date.utcDatetime( self.__node['date'] )

    def commitMessage( self ):
        return self.__node['message']
