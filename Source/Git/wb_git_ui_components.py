'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_components.py.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_log_history_options_dialog

import wb_git_ui_actions
import wb_git_project
import wb_git_commit_dialog
import wb_git_log_history
import wb_git_status_view

import git.cmd

#
#   Add tool bars and menu for use in the Main Window
#
#   add the commit code at this level to avoid import loops
#
class GitMainWindowComponents(wb_git_ui_actions.GitMainWindowActions):
    def __init__( self ):
        super().__init__()

    def about( self ):
        return ['GitPython %s' % (git.__version__,)
               ,'git %d.%d.%d' % git.cmd.Git().version_info]

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Git Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerGitDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerGitDiffStagedVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerGitDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m.addSeparator()
        addMenu( m, T_('Status'), self.treeActionGitStatus )

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
        addMenu( m, T_('Push…'), self.treeActionGitPush, self.enablerGitPush, 'toolbar_images/push.png', thread_switcher=True )
        addMenu( m, T_('Pull…'), self.treeActionGitPull, icon_name='toolbar_images/pull.png', thread_switcher=True )

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
        addTool( t, T_('Commit History'), self.treeTableActionGitLogHistory, self.enablerGitLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('git state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Stage'), self.tableActionGitStage, self.enablerGitFilesStage, 'toolbar_images/include.png' )
        addTool( t, T_('Unstage'), self.tableActionGitUnstage, self.enablerGitFilesUnstage, 'toolbar_images/exclude.png' )
        addTool( t, T_('Revert'), self.tableActionGitRevert, self.enablerGitFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Commit'), self.treeActionGitCommit, self.enablerGitCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), self.treeActionGitPush, self.enablerGitPush, 'toolbar_images/push.png', thread_switcher=True )
        addTool( t, T_('Pull'), self.treeActionGitPull, icon_name='toolbar_images/pull.png', thread_switcher=True )

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
    def treeActionGitLogHistory( self ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            git_project = self.selectedGitProject()

            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app,
                    T_('Commit Log for %s') % (git_project.projectName(),),
                    self.main_window.getQIcon( 'wb.png' ) )

            func = self.app.threadSwitcher( commit_log_view.showCommitLogForRepository )
            func( git_project, options )

    def _actionGitLogHistory( self, git_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app, T_('Commit Log for %s') % (filename,), self.main_window.getQIcon( 'wb.png' ) )

            func = self.app.threadSwitcher( commit_log_view.showCommitLogForFile )
            func( git_project, filename, options )

    def treeActionGitCommit( self ):
        if self.commit_dialog is not None:
            self.log.error( 'Commit dialog is already open' )
            return

        git_project = self.selectedGitProject()

        self.commit_dialog = wb_git_commit_dialog.WbGitCommitDialog( self.app, git_project )
        self.commit_dialog.commitAccepted.connect( self.__commitAccepted )
        self.commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        self.commit_dialog.show()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        git_project = self.selectedGitProject()
        message = self.commit_dialog.getMessage()
        commit_id = git_project.cmdCommit( message )

        headline = message.split('\n')[0]
        self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        self.__commitClosed()

    def __commitClosed( self ):
        # get rid of the window
        if self.commit_dialog is not None:
            self.commit_dialog.close()
            self.commit_dialog = None

        # take account of any changes
        self.main_window.updateTableView()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()
