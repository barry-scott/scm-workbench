'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_project.py

'''
import sys
import os
import pathlib

import wb_annotate_node
import wb_platform_specific
import wb_git_callback_server

import git
import git.exc
import git.index

GitCommandError = git.exc.GitCommandError

def gitInit( app, progress_handler, wc_path ):
    progress = Progress( progress_handler )

    try:
        git.repo.Repo.init( str(wc_path) )
        return True

    except GitCommandError:
        for line in progress.allErrorLines():
            app.log.error( line )
        return False

__callback_server = None
git_extra_environ = {}
def initCallbackServer( app ):
    #pylint disable=global-statement
    global __callback_server
    assert __callback_server is None, 'Cannot call initCallbackServer twice'

    __callback_server = wb_git_callback_server.WbGitCallbackServer( app )

    __callback_server.start()
    if sys.platform == 'win32':
        callback  = wb_platform_specific.getAppDir() / 'scm-workbench-git-callback.exe'
        if not callback.exists():
            app.log.info( 'Cannot find %s' % (callback,) )
            # assume in development environment
            callback = wb_platform_specific.getAppDir() / 'scm_workbench_git_callback.cmd'
    else:
        callback = wb_platform_specific.getAppDir() / 'scm-workbench-git-callback'

    if not callback.exists():
        app.log.error( 'Cannot find %s' % (callback,) )
        return

    if 'GIT_ASKPASS' in os.environ:
        app.log.info( "Using user's GIT_ASKPASS program %s" % (os.environ[ 'GIT_ASKPASS' ],) )

    else:
        git_extra_environ['GIT_ASKPASS'] = '"%s" askpass' % (str(callback),)
        app.log.info( "Using Workbench's GIT_ASKPASS program" )

    git_extra_environ['GIT_SEQUENCE_EDITOR'] = '"%s" sequence-editor' % (str(callback),)
    git_extra_environ['GIT_EDITOR'] = '"%s" editor' % (str(callback),)
    app.log.info( "Setup Workbench's GIT callback program" )

def setCallbackCredentialsHandler( handler ):
    __callback_server.setCallbackCredentialsHandler( handler )

def setCallbackRebaseSequenceHandler( handler ):
    __callback_server.setCallbackRebaseSequenceHandler( handler )

def setCallbackRebaseEditorHandler( handler ):
    __callback_server.setCallbackRebaseEditorHandler( handler )

def setCallbackReply( code, value ):
    __callback_server.setReply( code, value )

class GitProject:
    def __init__( self, app, prefs_project, ui_components ):
        self.app = app
        self.ui_components = ui_components

        self.debugLog = self.app.debug_options.debugLogGitProject
        self.debugLogTree = self.app.debug_options.debugLogGitUpdateTree

        self.prefs_project = prefs_project
        # repo will be setup on demand - this speeds up start up especically on macOS
        self.__repo = None
        self.index = None

        self.tree = GitProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = GitProjectTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

        self.all_file_state = {}

        self.__stale_index = False

        self.__num_staged_files = 0
        self.__num_modified_files = 0

    def getMasterBranchName( self ):
        if self.prefs_project.master_branch_name is None:
            return 'master'
        else:
            return self.prefs_project.master_branch_name

    def setMasterBranchName( self, master_branch_name ):
        if master_branch_name == 'master':
            self.prefs_project.master_branch_name = None
        else:
            self.prefs_project.master_branch_name = master_branch_name

    def cloneFrom( self, url, progress_handler ):
        assert self.__repo is None

        progress = Progress( progress_handler )

        try:
            self.__repo = git.repo.Repo.clone_from( url, str(self.prefs_project.path), progress )
            return True

        except GitCommandError:
            for line in progress.allErrorLines():
                self.app.log.error( line )

            return False

    def repo( self ):
        # setup repo on demand
        if self.__repo is None:
            self.__repo = git.Repo( str( self.prefs_project.path ) )
            self.__repo.git.update_environment( **git_extra_environ )

        return self.__repo

    def scmType( self ):
        return 'git'

    # return a new GitProject that can be used in another thread
    def newInstance( self ):
        return GitProject( self.app, self.prefs_project, self.ui_components )

    def isNotEqual( self, other ):
        return self.prefs_project.name != other.prefs_project.name

    def __repr__( self ):
        return '<GitProject: %s (id:%d>' % (self.prefs_project.name, id(self))

    def pathForGit( self, path ):
        assert isinstance( path, pathlib.Path )
        # return abs path
        return str( self.projectPath() / path )

    def pathForWb( self, str_path ):
        assert type( str_path ) == str
        wb_path = pathlib.Path( str_path )
        if wb_path.is_absolute():
            wb_path = wb_path.relative_to( self.projectPath() )

        return wb_path

    def hasCommits( self ):
        try:
            self.repo().head.ref.commit
            return True

        except ValueError:
            return False

    def projectName( self ):
        return self.prefs_project.name

    def projectPath( self ):
        return pathlib.Path( self.prefs_project.path )

    def configReader( self, level ):
        return self.repo().config_reader( level )

    def configWriter( self, level ):
        return self.repo().config_writer( level )

    def addRemote( self, name, url ):
        self.repo().create_remote( name, url )

    def getHeadCommit( self ):
        return self.repo().head.ref.commit

    def getShortCommitId( self, commit_id, size=7 ):
        return self.repo().git.rev_parse( commit_id, short=size )

    def switchToBranch( self, branch ):
        self.cmdCheckout( branch )

    def getBranchName( self ):
        return self.repo().head.ref.name

    def getAllBranchNames( self ):
        all_branch_names = sorted( [b.name for b in self.repo().branches] )
        # detect the case of a new, empty git repo
        if len(all_branch_names) == 0:
            all_branch_names = [self.getBranchName()]
        return all_branch_names

    def getTrackingBranchName( self ):
        tracking_branch = self.repo().head.ref.tracking_branch()
        return tracking_branch.name if tracking_branch is not None else None

    def getTrackingBranchCommit( self ):
        tracking_branch = self.repo().head.ref.tracking_branch()
        if tracking_branch is None:
            return None

        return tracking_branch.commit

    def getRemote( self, name ):
        try:
            return self.repo().remote( name )

        except ValueError:
            return None

    def cmdAddRemote( self, name, url ):
        git.Remote.create( self.repo(), name, url )

    def cmdDeleteRemote( self, name ):
        git.Remote.remove( self.repo(), name )

    def cmdUpdateRemote( self, name, url ):
        remote = self.getRemote( name )
        remote.set_url( url, remote.url )

    def numStagedFiles( self ):
        return self.__num_staged_files

    def numModifiedFiles( self ):
        return self.__num_modified_files

    def saveChanges( self ):
        self.debugLog( 'saveChanges() __stale_index %r' % (self.__stale_index,) )

        if self.__stale_index:
            self.updateState( 'QQQ' )
            self.__stale_index = False

    def updateState( self, tree_leaf ):
        self.debugLog( 'updateState( %r ) repo=%s' % (tree_leaf, self.projectPath()) )

        # rebuild the tree
        self.tree = GitProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )
        self.flat_tree = GitProjectTreeNode( self, self.prefs_project.name, pathlib.Path( '.' ) )

        if not self.projectPath().exists():
            self.app.log.error( T_('Project %(name)s folder %(folder)s has been deleted') %
                            {'name': self.projectName()
                            ,'folder': self.projectPath()} )

            self.all_file_state = {}

        else:
            self.__calculateStatus()

        for path in self.all_file_state:
            self.__updateTree( path )

        self.dumpTree()

    def __calculateStatus( self ):
        self.all_file_state = {}

        repo_root = self.projectPath()

        git_dir = repo_root / '.git'

        all_folders = set( [repo_root] )
        while len(all_folders) > 0:
            folder = all_folders.pop()

            for filename in folder.iterdir():
                abs_path = folder / filename

                repo_relative = abs_path.relative_to( repo_root )

                if abs_path.is_dir():
                    if abs_path != git_dir:
                        all_folders.add( abs_path )

                        self.all_file_state[ repo_relative ] = WbGitFileState( self, repo_relative )
                        self.all_file_state[ repo_relative ].setIsDir()

                else:
                    self.all_file_state[ repo_relative ] = WbGitFileState( self, repo_relative )

        # ----------------------------------------
        # can only get info from the index if there is at least 1 commit
        self.index = git.index.IndexFile( self.repo() )

        if self.hasCommits():
            head_vs_index = self.index.diff( self.repo().head.commit )
            index_vs_working = self.index.diff( None )

        else:
            head_vs_index = []
            index_vs_working = []

        # each ref to self.repo().untracked_files creates a new object
        # cache the value once/update
        untracked_files = self.repo().untracked_files

        for entry in self.index.entries.values():
            filepath = pathlib.Path( entry.path )
            if filepath not in self.all_file_state:
                # filepath has been deleted
                self.all_file_state[ filepath ] = WbGitFileState( self, filepath )

            self.all_file_state[ filepath ].setIndexEntry( entry )

        self.__num_staged_files = 0
        for diff in head_vs_index:
            self.__num_staged_files += 1
            filepath = pathlib.Path( diff.b_path )

            if filepath not in self.all_file_state:
                self.all_file_state[ filepath ] = WbGitFileState( self, filepath )

            if diff.renamed:
                self.all_file_state[ pathlib.Path( diff.rename_from ) ]._addStaged( diff )

            else:
                self.all_file_state[ filepath ]._addStaged( diff )

        self.__num_modified_files = 0
        for diff in index_vs_working:
            self.__num_modified_files += 1
            filepath = pathlib.Path( diff.a_path )
            if filepath not in self.all_file_state:
                self.all_file_state[ filepath ] = WbGitFileState( self, filepath )
            self.all_file_state[ filepath ]._addUnstaged( diff )

        for path in untracked_files:
            filepath = pathlib.Path( path )
            if filepath not in self.all_file_state:
                self.all_file_state[ filepath ] = WbGitFileState( self, filepath )

            self.all_file_state[ filepath ]._setUntracked()

    def __updateTree( self, path ):
        assert isinstance( path, pathlib.Path ), 'path %r' % (path,)
        self.debugLogTree( '__updateTree path %r' % (path,) )
        node = self.tree

        self.debugLogTree( '__updateTree path.parts %r' % (path.parts,) )

        for index, name in enumerate( path.parts[0:-1] ):
            self.debugLogTree( '__updateTree name %r at node %r' % (name,node) )

            if not node.hasFolder( name ):
                node.addFolder( name, GitProjectTreeNode( self, name, pathlib.Path( *path.parts[0:index+1] ) ) )

            node = node.getFolder( name )

        self.debugLogTree( '__updateTree addFile %r to node %r' % (path, node) )
        node.addFileByName( path )
        self.flat_tree.addFileByPath( path )

    def dumpTree( self ):
        if self.debugLogTree.isEnabled():
            self.tree._dumpTree( 0 )

    #------------------------------------------------------------
    #
    # functions to retrive interesting info from the repo
    #
    #------------------------------------------------------------
    def hasFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        return filename in self.all_file_state

    def getFileState( self, filename ):
        assert isinstance( filename, pathlib.Path )
        # status only has entries for none CURRENT status files
        return self.all_file_state[ filename ]

    def getReportStagedFiles( self ):
        all_staged_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isStagedNew():
                all_staged_files.append( (T_('New file'), filename, None) )

            elif file_state.isStagedModified():
                all_staged_files.append( (T_('Modified'), filename, None) )

            elif file_state.isStagedDeleted():
                all_staged_files.append( (T_('Deleted'), filename, None) )

            elif file_state.isStagedRenamed():
                all_staged_files.append( (T_('Renamed'), file_state.renamedFromFilename(), file_state.renamedToFilename()) )

        return all_staged_files

    def getReportUntrackedFiles( self ):
        all_untracked_files = []
        for filename, file_state in self.all_file_state.items():
            if file_state.isUncontrolled():
                all_untracked_files.append( (T_('New file'), filename) )

            elif file_state.isUnstagedModified():
                all_untracked_files.append( (T_('Modified'), filename) )

            elif file_state.isUnstagedDeleted():
                all_untracked_files.append( (T_('Deleted'), filename) )

        return all_untracked_files

    def canPush( self ):
        if not self.hasCommits():
            return False

        remote_commit = self.getTrackingBranchCommit()
        if remote_commit is None:
            return False

        head_commit = self.repo().head.ref.commit

        return head_commit != remote_commit

    def canPull( self ):
        return self.repo().head.ref.tracking_branch() is not None

    def getUnpushedCommits( self ):
        tracking_commit = self.getTrackingBranchCommit()
        if tracking_commit is None:
            return []

        last_pushed_commit_id = tracking_commit.hexsha

        all_unpushed_commits = []
        for commit in self.repo().iter_commits( None ):
            commit_id = commit.hexsha

            if last_pushed_commit_id == commit_id:
                break

            all_unpushed_commits.append( commit )

        return all_unpushed_commits

    #------------------------------------------------------------
    #
    # all functions starting with "cmd" are like the git <cmd> in behavior
    #
    #------------------------------------------------------------
    def cmdCheckout( self, branch_name ):
        try:
            branch = self.repo().branches[ branch_name ]
            branch.checkout()

        except GitCommandError as e:
            self.app.log.error( str(e) )

    def cmdStage( self, filename ):
        self.debugLog( 'cmdStage( %r )' % (filename,) )

        self.repo().git.add( filename )
        self.__stale_index = True

    def cmdUnstage( self, rev, filename ):
        self.debugLog( 'cmdUnstage( %r )' % (filename,) )

        self.repo().git.reset( 'HEAD', filename, mixed=True )
        self.__stale_index = True

    def cmdRevert( self, rev, file_state ):
        self.debugLog( 'cmdRevert( %r, %s:%r )' % (rev, file_state.relativePath(), file_state) )

        try:
            if file_state.isStagedRenamed():
                self.debugLog( 'cmdRevert renamedFromFilename %r renamedToFilename %r' %
                    (file_state.renamedFromFilename(), file_state.renamedToFilename()) )

                self.repo().git.reset( rev, file_state.renamedFromFilename(), mixed=True )
                self.repo().git.reset( rev, file_state.renamedToFilename(), mixed=True )
                self.repo().git.checkout( rev, file_state.renamedFromFilename() )
                self.cmdDelete( file_state.renamedToFilename() )

            elif( file_state.isStagedNew()
            or file_state.isStagedModified() ):
                self.repo().git.reset( rev, file_state.relativePath(), mixed=True )

            else:
                self.repo().git.checkout( rev, file_state.relativePath() )

        except GitCommandError as e:
            if e.stderr is not None:
                # stderr unfortuently is prefixed with "\n  stderr: '"
                self.app.log.error( e.stderr.split( "'", 1 )[1][:-1] )
            else:
                self.app.log.error( str(e) )

        self.__stale_index = True

    def cmdDelete( self, filename ):
        (self.prefs_project.path / filename).unlink()
        self.__stale_index = True

    def cmdRename( self, filename, new_filename ):
        filestate = self.getFileState( filename )
        if filestate.isControlled():
            self.repo().git.mv( filename, new_filename )

        else:
            abs_path = filestate.absolutePath()
            new_abs_path = self.prefs_project.path / new_filename
            try:
                abs_path.rename( new_abs_path )

            except IOError as e:
                self.app.log.error( 'Renamed failed - %s' % (e,) )

        self.__stale_index = True

    def cmdRebase( self, commit_id, all_rebase_commands, new_commit_message=None ):
        all_text = []
        for command in all_rebase_commands:
            all_text.append( ' '.join( command ) )
        all_text.append( '' )
        rebase_commands = '\n'.join( all_text )

        def rebaseHandler( filename ):
            if self.debugLog.isEnabled():
                with open( filename, 'r', encoding='utf-8' ) as f:
                    for line in f:
                        self.debugLog( 'Old Rebase: %r' % (line,) )

            with open( filename, 'w', encoding='utf-8' ) as f:
                if self.debugLog.isEnabled():
                    for line in all_text:
                        self.debugLog( 'New Rebase: %r' %(line,) )

                f.write( rebase_commands )

            return 0, ''

        def newCommitMessage( filename ):
            if self.debugLog.isEnabled():
                with open( filename, 'r', encoding='utf-8' ) as f:
                    for line in f:
                        self.debugLog( 'Old Commit Message: %r' % (line,) )

            with open( filename, 'w', encoding='utf-8' ) as f:
                if self.debugLog.isEnabled():
                    for line in new_commit_message.split('\n'):
                        self.debugLog( 'New Commit Message: %r' % (line,) )

                f.write( new_commit_message )

            return 0, ''

        def unexpectedCallback( filename ):
            return 1, 'Unexpected callback with %r' % (filename,)

        setCallbackRebaseSequenceHandler( rebaseHandler )
        if new_commit_message is None:
            setCallbackRebaseEditorHandler( unexpectedCallback )
        else:
            setCallbackRebaseEditorHandler( newCommitMessage )

        rc, stdout, stderr = self.repo().git.execute(
                    [git.Git.GIT_PYTHON_GIT_EXECUTABLE, 'rebase', '--interactive', '%s^1' % (commit_id,)],
                    with_extended_output=True,
                    with_exceptions=False,
                    universal_newlines=False,   # GitPython bug will TB if true
                    stdout_as_string=True )
        self.debugLog( '%s rebase --interactive %s -> rc %d' %
                (git.Git.GIT_PYTHON_GIT_EXECUTABLE, commit_id, rc) )

        if rc != 0:
            # assume need to abort rebase on failure
            self.repo().git.execute(
                    [git.Git.GIT_PYTHON_GIT_EXECUTABLE, 'rebase', '--abort'],
                    with_extended_output=True,
                    with_exceptions=False,
                    universal_newlines=False,   # GitPython bug will TB if true
                    stdout_as_string=True )

        setCallbackRebaseSequenceHandler( None )
        setCallbackRebaseEditorHandler( None )

        return rc, stdout.replace( '\r', '' ).split('\n'), stderr.replace( '\r', '' ).split('\n')

    def cmdCreateTag( self, tag_name, ref ):
        self.repo().create_tag( tag_name, ref=ref )

    def cmdDiffFolder( self, folder, head, staged ):
        if head and staged:
            return self.repo().git.diff( 'HEAD', self.pathForGit( folder ), staged=staged )

        elif staged:
            return self.repo().git.diff( self.pathForGit( folder ), staged=True )

        elif head:
            return self.repo().git.diff( 'HEAD', self.pathForGit( folder ), staged=False )

        else:
            return self.repo().git.diff( self.pathForGit( folder ), staged=False )

    def cmdDiffWorkingVsCommit( self, filename, commit ):
        return self.repo().git.diff( commit, self.pathForGit( filename ), staged=False )

    def cmdDiffStagedVSCommit( self, filename, commit ):
        return self.repo().git.diff( commit, self.pathForGit( filename ), staged=True )

    def cmdDiffCommitVsCommit( self, filename, old_commit, new_commit ):
        return self.repo().git.diff( old_commit, new_commit, '--', self.pathForGit( filename ) )

    def cmdShow( self, what ):
        return self.repo().git.show( what )

    def getTextLinesForCommit( self, filepath, commit_id ):
        assert isinstance( filepath, pathlib.Path ), 'expecting pathlib.Path got %r' % (filepath,)

        # git show wants a posix path, it does not work with '\' path seperators
        git_filepath = pathlib.PurePosixPath( filepath )
        text = self.cmdShow( '%s:%s' % (commit_id, git_filepath) )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def cmdCommit( self, message ):
        self.__stale_index = True
        return self.index.commit( message )

    def cmdCommitLogAfterCommitId( self, commit_id ):
        if not self.hasCommits():
            return []

        all_commit_logs = []

        for commit in self.repo().iter_commits( None ):
            if commit.hexsha == commit_id:
                break

            all_commit_logs.append( GitCommitLogNode( commit ) )

        return all_commit_logs

    def cmdCommitLogForRepository( self, progress_callback, limit=None, since=None, until=None, rev=None, paths='' ):
        if not self.hasCommits():
            return []

        all_commit_logs = []

        kwds = {}
        if limit is not None:
            kwds['max_count'] = limit
        if since is not None:
            kwds['since'] = since
        if since is not None:
            kwds['until'] = until

        for commit in self.repo().iter_commits( rev, paths, **kwds ):
            all_commit_logs.append( GitCommitLogNode( commit ) )

        total = len(all_commit_logs)
        progress_callback( 0, total )

        self.__addCommitChangeInformation( progress_callback, all_commit_logs )
        progress_callback( total, total )

        return all_commit_logs

    def cmdCommitLogForFile( self, progress_callback, filename, limit=None, since=None, until=None, rev=None ):
        return self.cmdCommitLogForRepository( progress_callback, paths=filename, limit=limit, since=since, until=until, rev=rev )

    def cmdTagsForRepository( self ):
        tag_name_by_id = {}
        for tag in self.repo().tags:
            try:
                tag_name_by_id[ tag.commit.hexsha ] = tag.name

            except ValueError:
                # cannot get the tag - may be a deteched ref
                pass

        return tag_name_by_id

    def doesTagExist( self, tag_name ):
        return tag_name in self.repo().tags

    def __addCommitChangeInformation( self, progress_callback, all_commit_logs ):
        # now calculate what was added, deleted and modified in each commit
        total = len(all_commit_logs)
        for offset in range( total ):
            progress_callback( offset, total )
            all_files = all_commit_logs[ offset ].commitStats().files
            new_tree = all_commit_logs[ offset ].commitTree()
            old_tree = all_commit_logs[ offset ].commitPreviousTree()

            all_new = {}
            self.__treeToDict( all_files, new_tree, all_new )
            new_set = set(all_new)

            if old_tree is None:
                all_commit_logs[ offset ]._addChanges( new_set, set(), [], set() )

            else:
                all_old = {}
                self.__treeToDict( all_files, old_tree, all_old )

                old_set = set(all_old)

                all_added = new_set - old_set
                all_deleted = old_set - new_set

                all_renamed = []

                # look for renames
                if len(all_added) > 0 and len(all_deleted) > 0:
                    all_old_id_to_name = {}
                    for name in all_deleted:
                        all_old_id_to_name[ all_old[ name ] ] = name

                    for name in list(all_added):
                        id_ = all_new[ name ]

                        if id_ in all_old_id_to_name:
                            old_name = all_old_id_to_name[ id_ ]

                            # converted svn repos can have trees that cannot
                            # be used to figure out the rename
                            # for example when the checkin deletes a folder
                            # which cannot be expressed in git trees
                            if( old_name in all_added
                            and old_name in all_deleted ):
                                all_added.remove( name )
                                all_deleted.remove( old_name )
                                all_renamed.append( (name, old_name) )

                all_modified = set()

                for key in all_new:
                    if( key in all_old
                    and all_new[ key ] != all_old[ key ] ):
                        all_modified.add( key )

                all_commit_logs[ offset ]._addChanges( all_added, all_deleted, all_renamed, all_modified )

    def __treeToDict( self, all_files, tree, all_entries ):
        for file in all_files:
            all_parts = file.split('/')
            node = tree

            # walk down the tree (aka folders) until we have
            # the tree that has the blob (aka file) in it

            # tree.path is the full name of the folder
            for index in range(1, len(all_parts)):
                prefix = '/'.join( all_parts[:index] )
                for child in node.trees:
                    if child.path == prefix:
                        node = child
                        break

            # blob.path is the full path to the file
            for blob in node:
                if blob.path == file:
                    all_entries[ blob.path ] = blob.hexsha
                    break

    def cmdAnnotationForFile( self, filename, rev=None ):
        if rev is None:
            rev = 'HEAD'

        all_annotate_nodes = []

        line_num = 0
        for commit, all_lines in self.repo().blame( rev, self.pathForGit( filename ) ):
            commit_id = commit.hexsha
            for line_text in all_lines:
                line_num += 1
                all_annotate_nodes.append(
                    wb_annotate_node.AnnotateNode( line_num, line_text, commit_id ) )

        return all_annotate_nodes

    def cmdCommitLogForAnnotateFile( self, filename, all_commit_ids ):
        all_commit_logs = {}

        for commit_id in all_commit_ids:
            commit = self.repo().commit( commit_id )
            all_commit_logs[ commit_id ] = GitCommitLogNode( commit )

        return all_commit_logs

    def cmdPull( self, progress_callback, info_callback ):
        tracking_branch = self.repo().head.ref.tracking_branch()
        remote = self.repo().remote( tracking_branch.remote_name )

        progress = Progress( progress_callback )

        try:
            for info in remote.pull( progress=progress ):
                info_callback( info )

            for line in progress.allDroppedLines():
                self.app.log.info( line )

        except GitCommandError:
            for line in progress.allErrorLines():
                self.app.log.error( line )

            raise

    def cmdPush( self, progress_callback, info_callback ):
        progress = Progress( progress_callback )

        tracking_branch = self.repo().head.ref.tracking_branch()
        remote = self.repo().remote( tracking_branch.remote_name )

        try:
            for info in remote.push( progress=progress ):
                info_callback( info )

            for line in progress.allDroppedLines():
                self.app.log.info( line )

        except GitCommandError:
            for line in progress.allErrorLines():
                self.app.log.error( line )

            raise

    def cmdStashSave( self, message=None ):
        cmd = [git.Git.GIT_PYTHON_GIT_EXECUTABLE, 'stash', 'push']
        if message is not None:
            cmd.append( '--message' )
            cmd.append( message )

        rc, stdout, stderr = self.repo().git.execute(
                    cmd,
                    with_extended_output=True,
                    with_exceptions=False,
                    universal_newlines=False,   # GitPython bug will TB if true
                    stdout_as_string=True )
        self.debugLog( '%s stash save -> rc %d' % (git.Git.GIT_PYTHON_GIT_EXECUTABLE, rc) )
        if rc != 0:
            for line in stderr.split( '\n' ):
                line = line.strip()
                self.app.log.error( line )

        return rc == 0

    def cmdStashPop( self, stash_id ):
        cmd = [git.Git.GIT_PYTHON_GIT_EXECUTABLE, 'stash', 'pop', '--quiet', stash_id]
        self.debugLog( 'cmdStashPop: %r' % (cmd,) )
        rc, stdout, stderr = self.repo().git.execute(
                    cmd,
                    with_extended_output=True,
                    with_exceptions=False,
                    universal_newlines=False,   # GitPython bug will TB if true
                    stdout_as_string=True )
        self.debugLog( '%s stash apply %s -> rc %d' % (git.Git.GIT_PYTHON_GIT_EXECUTABLE, stash_id, rc) )

        for line in stdout.split( '\n' ):
            line = line.strip()
            self.app.log.info( line )

        if rc != 0:
            for line in stderr.split( '\n' ):
                line = line.strip()
                self.app.log.error( line )

        return rc == 0

    def cmdStashList( self ):
        rc, stdout, stderr = self.repo().git.execute(
                    [git.Git.GIT_PYTHON_GIT_EXECUTABLE, 'stash', 'list'],
                    with_extended_output=True,
                    with_exceptions=False,
                    universal_newlines=False,   # GitPython bug will TB if true
                    stdout_as_string=True )
        self.debugLog( '%s stash list -> rc %d' % (git.Git.GIT_PYTHON_GIT_EXECUTABLE, rc) )
        if rc != 0:
            for line in stderr.split( '\n' ):
                line = line.strip()
                self.app.log.error( line )
            return []

        all_stashes = []

        for line in stdout.split( '\n' ):
            line = line.strip()
            if line == '':
                continue

            stash_id, stash_branch, stash_message = line.split( ': ', 2 )
            for branch_prefix in ('WIP on ', 'On '):
                if stash_branch.startswith( branch_prefix ):
                    stash_branch = stash_branch[len(branch_prefix):]
                    break

            all_stashes.append( WbGitStashInfo( stash_id, stash_branch, stash_message ) )

        return all_stashes


class WbGitStashInfo:
    def __init__( self, stash_id, stash_branch, stash_message ):
        self.stash_id = stash_id
        self.stash_branch = stash_branch
        self.stash_message = stash_message

    def __repr__( self ):
        return ('<WbGitStashInfo: id=%s branch=%s msg=%s>' %
                (self.stash_id, self.stash_branch, self.stash_message))


class WbGitFileState:
    def __init__( self, project, filepath ):
        assert isinstance( project, GitProject ),'expecting GitProject got %r' % (project,)
        assert isinstance( filepath, pathlib.Path ), 'expecting pathlib.Path got %r' % (filepath,)

        self.__project = project
        self.__filepath = filepath

        self.__is_dir = False

        self.__index_entry = None
        self.__unstaged_diff = None
        self.__staged_diff = None
        self.__untracked = False

        # from the above calculate the following
        self.__state_calculated = False

        self.__staged_is_modified = False
        self.__unstaged_is_modified = False

        self.__staged_abbrev = None
        self.__unstaged_abbrev = None

        self.__head_blob = None
        self.__staged_blob = None

    def __repr__( self ):
        return ('<WbGitFileState: calc %r, S=%r, U=%r' %
                (self.__state_calculated, self.__staged_abbrev, self.__unstaged_abbrev))

    def relativePath( self ):
        return self.__filepath

    def absolutePath( self ):
        return self.__project.projectPath() / self.__filepath

    def renamedToFilename( self ):
        assert self.isStagedRenamed()
        return pathlib.Path( self.__staged_diff.rename_from )

    def renamedFromFilename( self ):
        assert self.isStagedRenamed()
        return pathlib.Path( self.__staged_diff.rename_to )

    def setIsDir( self ):
        self.__is_dir = True

    def isDir( self ):
        return self.__is_dir

    def setIndexEntry( self, index_entry ):
        self.__index_entry = index_entry

    def _addStaged( self, diff ):
        self.__state_calculated = False
        self.__staged_diff = diff

    def _addUnstaged( self, diff ):
        self.__state_calculated = False
        self.__unstaged_diff = diff

    def _setUntracked( self ):
        self.__untracked = True

    # from the provided info work out
    # interesting properies
    def __calculateState( self ):
        if self.__state_calculated:
            return

        if self.__staged_diff is None:
            self.__staged_abbrev = ''

        else:
            if self.__staged_diff.renamed:
                self.__staged_abbrev = 'R'

            elif self.__staged_diff.deleted_file:
                self.__staged_abbrev = 'A'

            elif self.__staged_diff.new_file:
                self.__staged_abbrev = 'D'

            else:
                self.__staged_abbrev = 'M'
                self.__staged_is_modified = True
                self.__head_blob = self.__staged_diff.b_blob
                self.__staged_blob = self.__staged_diff.a_blob

        if  self.__unstaged_diff is None:
            self.__unstaged_abbrev = ''

        else:
            if self.__unstaged_diff.deleted_file:
                self.__unstaged_abbrev = 'D'

            elif self.__unstaged_diff.new_file:
                self.__unstaged_abbrev = 'A'

            else:
                self.__unstaged_abbrev = 'M'
                self.__unstaged_is_modified = True
                if self.__head_blob is None:
                    self.__head_blob = self.__unstaged_diff.a_blob

        self.__state_calculated = True

    def getStagedAbbreviatedStatus( self ):
        self.__calculateState()
        return self.__staged_abbrev

    def getUnstagedAbbreviatedStatus( self ):
        self.__calculateState()
        return self.__unstaged_abbrev

    #------------------------------------------------------------
    def isControlled( self ):
        if self.__staged_diff is not None:
            return True

        return self.__index_entry is not None

    def isUncontrolled( self ):
        return self.__untracked

    def isIgnored( self ):
        if self.__staged_diff is not None:
            return False

        if self.__index_entry is not None:
            return False

        # untracked files have had ignored files striped out
        if self.__untracked:
            return False

        return True

    # ------------------------------
    def isStagedNew( self ):
        self.__calculateState()
        return self.__staged_abbrev == 'A'

    def isStagedModified( self ):
        self.__calculateState()
        return self.__staged_abbrev == 'M'

    def isStagedDeleted( self ):
        self.__calculateState()
        return self.__staged_abbrev == 'D'

    def isStagedRenamed( self ):
        self.__calculateState()
        return self.__staged_abbrev == 'R'

    def isUnstagedModified( self ):
        self.__calculateState()
        return self.__unstaged_abbrev == 'M'

    def isUnstagedDeleted( self ):
        self.__calculateState()
        return self.__unstaged_abbrev == 'D'

    # ------------------------------------------------------------
    def canCommit( self ):
        return self.__staged_abbrev != ''

    def canStage( self ):
        return self.__unstaged_abbrev != '' or self.__untracked

    def canUnstage( self ):
        return self.__staged_abbrev != ''

    def canRevert( self ):
        return (self.isUnstagedDeleted()
               or self.isUnstagedModified()
               or self.isStagedNew()
               or self.isStagedRenamed()
               or self.isStagedDeleted()
               or self.isStagedModified())

    # ------------------------------------------------------------
    def canDiffHeadVsStaged( self ):
        self.__calculateState()
        return self.__staged_is_modified

    def canDiffStagedVsWorking( self ):
        self.__calculateState()
        return self.__unstaged_is_modified and self.__staged_is_modified

    def canDiffHeadVsWorking( self ):
        self.__calculateState()
        return self.__unstaged_is_modified

    def getTextLinesWorking( self ):
        path = self.absolutePath()
        with path.open( encoding='utf-8' ) as f:
            all_lines = f.read().split( '\n' )
            if all_lines[-1] == '':
                return all_lines[:-1]
            else:
                return all_lines

    def getTextLinesHead( self ):
        return self.__getTextLinesFromBlob( self.getHeadBlob() )

    def getTextLinesStaged( self ):
        return self.__getTextLinesFromBlob( self.getStagedBlob() )

    def __getTextLinesFromBlob( self, blob ):
        data = blob.data_stream.read()
        text = data.decode( 'utf-8' )
        all_lines = text.split('\n')
        if all_lines[-1] == '':
            return all_lines[:-1]
        else:
            return all_lines

    def getTextLinesForCommit( self, commit_id ):
        git_filepath = pathlib.PurePosixPath( self.__filepath )
        text = self.__project.cmdShow( '%s:%s' % (commit_id, git_filepath) )
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

    def commitStats( self ):
        return self.__commit.stats

    def commitTree( self ):
        return self.__commit.tree

    def commitPreviousTree( self ):
        if len(self.__commit.parents) == 0:
            return None

        previous_commit = self.__commit.parents[0]
        return previous_commit.tree

    def commitId( self ):
        return self.__commit.hexsha

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

    def commitMessageHeadline( self ):
        return self.__commit.message.split('\n')[0]

    def commitFileChanges( self ):
        return self.__all_changes

class GitProjectTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.is_by_path = False
        self.__path = path
        self.__all_folders = {}
        self.__all_files = {}

    def __repr__( self ):
        return '<GitProjectTreeNode: project %r, path %s>' % (self.project, self.__path)

    def updateTreeNode( self ):
        pass

    def isByPath( self ):
        return self.is_by_path

    def addFileByName( self, path ):
        assert path.name != ''
        self.__all_files[ path.name ] = path

    def addFileByPath( self, path ):
        assert path.name != ''
        self.is_by_path = True
        path = path
        self.__all_files[ path ] = path

    def getAllFileNames( self ):
        return self.__all_files.keys()

    def addFolder( self, name, node ):
        assert type(name) == str and name != '', 'name %r, node %r' % (name, node)
        assert isinstance( node, GitProjectTreeNode )
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
        self.project.debugLog( 'dump: %*s%r' % (indent, '', self) )

        for file in sorted( self.__all_files ):
            self.project.debugLog( 'dump %*s   file: %r' % (indent, '', file) )

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
            entry = WbGitFileState( self.project, path )

        return entry

class Progress(git.RemoteProgress):
    def __init__( self, progress_call_back ):
        self.progress_call_back = progress_call_back
        super().__init__()

        self.__all_dropped_lines = []

    all_update_stages = {
        git.RemoteProgress.COUNTING:        'Counting',
        git.RemoteProgress.COMPRESSING:     'Compressing',
        git.RemoteProgress.WRITING:         'Writing',
        git.RemoteProgress.RECEIVING:       'Receiving',
        git.RemoteProgress.RESOLVING:       'Resolving',
        git.RemoteProgress.FINDING_SOURCES: 'Finding Sources',
        git.RemoteProgress.CHECKING_OUT:    'Checking Out',
        }

    def update( self, op_code, cur_count, max_count=None, message='' ):
        stage_name = self.all_update_stages.get( op_code&git.RemoteProgress.OP_MASK, 'Unknown' )
        is_begin = op_code&git.RemoteProgress.BEGIN != 0
        is_end = op_code&git.RemoteProgress.END != 0
        self.progress_call_back( is_begin, is_end, stage_name, cur_count, max_count, message )

    def line_dropped( self, line ):
        if line.startswith( 'POST git-upload-pack' ):
            return

        self.__all_dropped_lines.append( line )

    def allErrorLines( self ):
        return self.error_lines + self.__all_dropped_lines

    def allDroppedLines( self ):
        return self.__all_dropped_lines
