'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_components.py.py

'''
import os
import time
import shutil
import urllib.parse

import wb_log_history_options_dialog
import wb_platform_specific

import wb_git_ui_actions
import wb_git_project
import wb_git_commit_dialog
import wb_git_log_history
import wb_git_askpass_server
import wb_git_credentials_dialog
import wb_git_annotate

import git
import git.exc

from wb_background_thread import thread_switcher


#
#   Add tool bars and menu for use in the Main Window
#
#   add the commit code at this level to avoid import loops
#
class GitMainWindowComponents(wb_git_ui_actions.GitMainWindowActions):
    def __init__( self ):
        self.all_visible_table_columns = None

        super().__init__()

        self.askpass_server = None
        self.saved_password = SavedPassword()

    def createProject( self, project ):
        tm = self.table_view.table_model
        self.all_visible_table_columns = (tm.col_staged, tm.col_status, tm.col_name, tm.col_date)

        if shutil.which( 'git' ) is None:
            self.app.log.error( '"git" command line tool not found' )
            return None

        try:
            return wb_git_project.GitProject( self.app, project, self )

        except git.exc.InvalidGitRepositoryError as e:
            self.log.error( 'Failed to add Git repo %r' % (project.path,) )
            self.log.error( 'Git error: %s' % (e,) )
            return None

    def addProjectInitWizardHandler( self, wc_path ):
        self.log.info( 'Initialise Git repository in %s' % (wc_path,) )

        return wb_git_project.gitInit( self.app, wc_path )

    def addProjectPreCloneWizardHandler( self, name, url, wc_path ):
        self.log.info( 'Cloning Git repository %s into %s' % (url, wc_path) )
        self.setStatusAction( T_('Clone %(project)s') %
                                    {'project': name} )

    def addProjectCloneWizardHandler( self, name, url, wc_path ):
        return wb_git_project.gitCloneFrom( self.app, self.pullProgressHandler, url, wc_path )

    def addProjectPostCloneWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    def setTopWindow( self, top_window ):
        super().setTopWindow( top_window )

        prefs = self.app.prefs.git
        if prefs.program is not None:
            git.Git.GIT_PYTHON_GIT_EXECUTABLE = str(prefs.program)

        self.log.info( 'Git using program %s' % (git.Git.GIT_PYTHON_GIT_EXECUTABLE,) )

        if 'GIT_ASKPASS' in os.environ:
            self.log.info( "Using user's GIT_ASKPASS program %s" % (os.environ[ 'GIT_ASKPASS' ],) )
            return

        self.askpass_server = wb_git_askpass_server.WbGitAskPassServer( self.app, self )

        devel_fallback = False
        self.askpass_server.start()
        if wb_platform_specific.isWindows():
            askpass  = wb_platform_specific.getAppDir() / 'scm-workbench-askpass.exe'
            if not askpass.exists():
                self.log.info( 'Cannot find %s' % (askpass,) )
                # assume in development environment
                askpass = wb_platform_specific.getAppDir() / 'scm-workbench-askpass.py'

        else:
            askpass = wb_platform_specific.getAppDir() / 'scm-workbench-askpass'

        if not askpass.exists():
            self.log.error( 'Cannot find %s' % (askpass,) )
            return

        os.environ['GIT_ASKPASS'] = str(askpass)
        self.log.info( "Using Workbench's GIT_ASKPASS program" )

    def about( self ):
        if shutil.which( 'git' ) is None:
            git_ver = '"git" command line tool not found'

        else:
            git_ver = 'git %d.%d.%d' % git.Git().version_info

        return  ['GitPython %s' % (git.__version__,)
                ,git_ver]

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Git Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Annotate'), self.tableActionGitAnnotate_Bg, self.enablerTableGitAnnotate )

        m.addSeparator()
        addMenu( m, T_('Status'), self.treeActionGitStatus )

        m.addSeparator()
        addMenu( m, T_('Commit History'), self.treeTableActionGitLogHistory_Bg, self.enablerGitLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        m = mb.addMenu( T_('&Git Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerGitFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerGitFilesRevert, 'toolbar_images/revert.png' )

        m.addSeparator()
        addMenu( m, T_('Rename…'), self.tableActionGitRename, self.main_window.table_view.enablerTableFilesExists )
        addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Commit…'), self.treeActionGitCommit, self.enablerGitCommit, 'toolbar_images/commit.png' )

        m.addSeparator()
        addMenu( m, T_('Push…'), self.treeActionGitPush_Bg, self.enablerGitPush, 'toolbar_images/push.png' )
        addMenu( m, T_('Pull…'), self.treeActionGitPull_Bg, icon_name='toolbar_images/pull.png' )

        if hasattr( self, 'treeActionGitDebug1' ):
            m = mb.addMenu( T_('&Git Debug') )
            self.all_menus.append( m )
            addMenu( m, T_('Debug 1'), self.treeActionGitDebug1 )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('git logo'), style='font-size: 20pt; width: 40px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'Git', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('git info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionGitDiffSmart, self.enablerGitDiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Commit History'), self.treeTableActionGitLogHistory_Bg, self.enablerGitLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('git state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Stage'), self.tableActionGitStage, self.enablerGitFilesStage, 'toolbar_images/include.png' )
        addTool( t, T_('Unstage'), self.tableActionGitUnstage, self.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addTool( t, T_('Revert'), self.tableActionGitRevert, self.enablerGitFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Commit'), self.treeActionGitCommit, self.enablerGitCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), self.treeActionGitPush_Bg, self.enablerGitPush, 'toolbar_images/push.png' )
        addTool( t, T_('Pull'), self.treeActionGitPull_Bg, icon_name='toolbar_images/pull.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), self.tableActionGitDiffHeadVsWorking, self.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.tableActionGitDiffHeadVsStaged, self.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.tableActionGitDiffStagedVsWorking, self.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Git Actions') )
        addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerGitFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerGitFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        addMenu( m, T_('Rename…'), self.tableActionGitRename, self.main_window.table_view.enablerTableFilesExists )
        addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.main_window.table_view.enablerTableFilesExists )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )
        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeActionGitDiffHeadVsWorking, self.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.treeActionGitDiffHeadVsStaged, self.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.treeActionGitDiffStagedVsWorking, self.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionGitLogHistory_Bg( self ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        git_project = self.selectedGitProject()

        commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                self.app,
                T_('Commit Log for %s') % (git_project.projectName(),) )

        yield from commit_log_view.showCommitLogForRepository_Bg( git_project, options )

    @thread_switcher
    def _actionGitLogHistory_Bg( self, git_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                self.app, T_('Commit Log for %s') % (filename,) )

        yield from commit_log_view.showCommitLogForFile_Bg( git_project, filename, options )

    def enablerTableGitAnnotate( self ):
        if not self.isScmTypeActive():
            return False

        return True

    @thread_switcher
    def tableActionGitAnnotate_Bg( self, checked ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionGitAnnotate_Bg )

    @thread_switcher
    def __actionGitAnnotate_Bg( self, git_project, filename ):
        self.setStatusAction( T_('Annotate %s') % (filename,) )
        self.progress.start( T_('Annotate %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_annotation_nodes = git_project.cmdAnnotationForFile( filename )

        all_annotate_commit_ids = set()
        for node in all_annotation_nodes:
            all_annotate_commit_ids.add( node.log_id )

        yield self.switchToForeground

        self.progress.end()
        self.progress.start( T_('Annotate Commit Logs %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_commit_logs = git_project.cmdCommitLogForAnnotateFile( filename, all_annotate_commit_ids )

        yield self.switchToForeground

        self.setStatusAction()
        self.progress.end()

        annotate_view = wb_git_annotate.WbGitAnnotateView(
                            self.app,
                            T_('Annotation of %s') % (filename,) )
        annotate_view.showAnnotationForFile( all_annotation_nodes, all_commit_logs )
        annotate_view.show()

    commit_key = 'git-commit-dialog'
    def treeActionGitCommit( self ):
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.getSingleton( self.commit_key )
            commit_dialog.raise_()
            return

        git_project = self.selectedGitProject()

        commit_dialog = wb_git_commit_dialog.WbGitCommitDialog( self.app, git_project )
        commit_dialog.commitAccepted.connect( self.__commitAccepted )
        commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        commit_dialog = self.app.getSingleton( self.commit_key )

        git_project = commit_dialog.getGitProject()
        message = commit_dialog.getMessage()
        commit_id = git_project.cmdCommit( message )

        headline = message.split('\n')[0]
        self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        self.__commitClosed()

    def __commitClosed( self ):
        # on top window close the commit_key may already have been pop'ed
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.popSingleton( self.commit_key )
            commit_dialog.close()

        # take account of any changes
        self.main_window.updateTableView()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def getGitCredentials( self, prompt ):
        # the prompt contains a url enclosed in "'".
        if "'" not in prompt:
            self.askpass_server.setReply( 1, 'unknown prompt' )
            return

        url = prompt.split( "'" )[1]

        # see if the password is required
        if self.saved_password.isValid():
            self.askpass_server.setReply( 0, self.saved_password.password )
            self.saved_password.clearPassword()
            return

        # forgot the saved credentials as the url did not match
        self.saved_password.clearPassword()

        url_parts = urllib.parse.urlsplit( url )

        cred = wb_git_credentials_dialog.WbGitCredentialsDialog( self.app, self.main_window )
        cred.setFields( url, url_parts.username )
        if cred.exec_():
            if url_parts.username is None:
                self.askpass_server.setReply( 0, cred.getUsername() )

                # assume that the password will be required next
                netloc = '%s@%s' % (cred.getUsername(), url_parts.netloc)
                url2 = urllib.parse.urlunsplit( (url_parts.scheme, netloc, url_parts.path, url_parts.query, url_parts.fragment) )
                self.saved_password.savePassword( url2, cred.getPassword() )

            else:
                self.askpass_server.setReply( 0, cred.getPassword() )

        else:
            self.askpass_server.setReply( 1, '' )

class SavedPassword:
    timeout = 5.0
    def __init__( self ):
        self.url = None
        self.password = None
        self.save_time = 0

    def savePassword( self, url, password ):
        self.url = url
        self.password = password
        self.save_time = time.time()

    def clearPassword( self ):
        self.url = None
        self.password = None
        self.save_time = 0

    def isValid( self ):
        if self.password is None:
            return False

        delta = time.time() - self.save_time
        return delta < self.timeout
