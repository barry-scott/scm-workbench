'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_components.py.py

'''
import os
import sys
import time
import shutil
import urllib.parse

import wb_log_history_options_dialog
import wb_platform_specific

import wb_ui_components

import wb_git_ui_actions
import wb_git_project
import wb_git_askpass_server
import wb_git_credentials_dialog

import git
import git.exc

from wb_background_thread import thread_switcher


#
#   Add tool bars and menu for use in the Main Window
#
#   add the commit code at this level to avoid import loops
#
class GitMainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        self.all_visible_table_columns = None

        super().__init__( 'git', factory )

        self.askpass_server = None
        self.saved_password = SavedPassword()

    def createProject( self, project ):
        if shutil.which( 'git' ) is None:
            self.app.log.error( '"git" command line tool not found' )
            return None

        try:
            return wb_git_project.GitProject( self.app, project, self )

        except git.exc.InvalidGitRepositoryError as e:
            self.log.error( 'Failed to add Git repo %r' % (project.path,) )
            self.log.error( 'Git error: %s' % (e,) )
            return None

    #------------------------------------------------------------
    def addProjectPreInitWizardHandler( self, name, url, wc_path ):
        self.log.infoheader( 'Initialise Git repository in %s' % (wc_path,) )
        self.setStatusAction( T_('Clone %(project)s') %
                                    {'project': name} )

    # runs on the background thread
    def addProjectInitWizardHandler_Bg( self, wc_path ):
        return wb_git_project.gitInit( self.app, wc_path )

    def addProjectPostInitWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    #------------------------------------------------------------
    def addProjectPreCloneWizardHandler( self, name, url, wc_path ):
        self.log.infoheader( T_('Cloning Git repository %(url)s into %(path)s') %
                                    {'url': url, 'path': wc_path} )
        self.setStatusAction( T_('Clone %(project)s') %
                                    {'project': name} )

    # runs on the background thread
    def addProjectCloneWizardHandler_Bg( self, name, url, wc_path ):
        return wb_git_project.gitCloneFrom( self.app, self.ui_actions.pullProgressHandler, url, wc_path )

    def addProjectPostCloneWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    #------------------------------------------------------------
    def setTopWindow( self, top_window ):
        super().setTopWindow( top_window )

        tm = self.table_view.table_model
        self.all_visible_table_columns = (tm.col_staged, tm.col_status, tm.col_name, tm.col_date)

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
        if sys.platform == 'win32':
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
        act = self.ui_actions

        # ----------------------------------------
        m = mb.addMenu( T_('&Git Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff HEAD vs. Working'), act.treeTableActionGitDiffHeadVsWorking, act.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), act.treeTableActionGitDiffStagedVsWorking, act.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), act.treeTableActionGitDiffHeadVsStaged, act.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Annotate'), act.tableActionGitAnnotate_Bg, act.enablerTableGitAnnotate )

        m.addSeparator()
        addMenu( m, T_('Status'), act.treeActionGitStatus )

        m.addSeparator()
        addMenu( m, T_('Commit History'), act.treeTableActionGitLogHistory_Bg, act.enablerGitLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        m = mb.addMenu( T_('&Git Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Stage'), act.tableActionGitStage_Bg, act.enablerGitFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), act.tableActionGitUnstage_Bg, act.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), act.tableActionGitRevert_Bg, act.enablerGitFilesRevert, 'toolbar_images/revert.png' )

        m.addSeparator()
        addMenu( m, T_('Rename…'), act.tableActionGitRename_Bg, self.main_window.table_view.enablerTableFilesExists )
        addMenu( m, T_('Delete…'), act.tableActionGitDelete_Bg, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Commit…'), act.treeActionGitCommit, act.enablerGitCommit, 'toolbar_images/commit.png' )

        m.addSeparator()
        addMenu( m, T_('Push…'), act.treeActionGitPush_Bg, act.enablerGitPush, 'toolbar_images/push.png' )
        addMenu( m, T_('Pull…'), act.treeActionGitPull_Bg, icon_name='toolbar_images/pull.png' )

        if hasattr( self, 'treeActionGitDebug1' ):
            m = mb.addMenu( T_('&Git Debug') )
            self.all_menus.append( m )
            addMenu( m, T_('Debug 1'), act.treeActionGitDebug1 )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('git logo'), style='font-size: 20pt; width: 40px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'Git', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('git info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), act.treeTableActionGitDiffSmart, act.enablerGitDiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Commit History'), act.treeTableActionGitLogHistory_Bg, act.enablerGitLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('git state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Stage'), act.tableActionGitStage_Bg, act.enablerGitFilesStage, 'toolbar_images/include.png' )
        addTool( t, T_('Unstage'), act.tableActionGitUnstage_Bg, act.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addTool( t, T_('Revert'), act.tableActionGitRevert_Bg, act.enablerGitFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Commit'), act.treeActionGitCommit, act.enablerGitCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), act.treeActionGitPush_Bg, act.enablerGitPush, 'toolbar_images/push.png' )
        addTool( t, T_('Pull'), act.treeActionGitPull_Bg, icon_name='toolbar_images/pull.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), act.tableActionGitDiffHeadVsWorking, act.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), act.tableActionGitDiffHeadVsStaged, act.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), act.tableActionGitDiffStagedVsWorking, act.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Git Actions') )
        addMenu( m, T_('Stage'), act.tableActionGitStage_Bg, act.enablerGitFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), act.tableActionGitUnstage_Bg, act.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), act.tableActionGitRevert_Bg, act.enablerGitFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        addMenu( m, T_('Rename…'), act.tableActionGitRename_Bg, self.main_window.table_view.enablerTableFilesExists )
        addMenu( m, T_('Delete…'), act.tableActionGitDelete_Bg, self.main_window.table_view.enablerTableFilesExists )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), act.treeActionGitDiffHeadVsWorking, act.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), act.treeActionGitDiffHeadVsStaged, act.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), act.treeActionGitDiffStagedVsWorking, act.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )

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
