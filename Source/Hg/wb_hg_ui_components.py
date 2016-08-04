'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_ui_components.py.py

'''
import wb_log_history_options_dialog

import wb_hg_ui_actions
import wb_hg_project
import wb_hg_log_history

import wb_hg_commit_dialog

class HgMainWindowComponents(wb_hg_ui_actions.HgMainWindowActions):
    def __init__( self ):
        super().__init__()

    def about( self ):
        return [wb_hg_project.HgVersion()]

    def setupDebug( self ):
        self._debug = self.main_window.app._debugHgUi

    def setupMenuBar( self, mb, addMenu ):
        pass

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('hg logo'), style='font-size: 20pt; width: 40px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Hg', self.main_window.projectActionSettings )

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Hg Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionHgDiffHeadVsWorking, self.enablerHgDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSeparator()
        addMenu( m, T_('Status'), self.treeActionHgStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Hg Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Add'), self.tableActionHgAdd, self.enablerHgFilesAdd, 'toolbar_images/add.png' )

        m.addSeparator()
        addMenu( m, T_('Revert'), self.tableActionHgRevert, self.enablerHgFilesRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), self.tableActionHgDelete, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Commit…'), self.treeActionHgCommit, self.enablerHgCommit, 'toolbar_images/commit.png' )

        m.addSeparator()
        addMenu( m, T_('Push…'), self.treeActionHgPush, self.enablerHgPush, 'toolbar_images/push.png', thread_switcher=True )
        addMenu( m, T_('Pull…'), self.treeActionHgPull, icon_name='toolbar_images/pull.png', thread_switcher=True )

        if hasattr( self, 'treeActionHgDebug1' ):
            m = mb.addMenu( T_('&Hg Debug') )
            self.all_menus.append( m )
            addMenu( m, T_('Debug 1'), self.treeActionHgDebug1 )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('hg logo'), style='font-size: 20pt; width: 40px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'Hg', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('hg info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionHgDiffSmart, self.enablerHgDiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Commit History'), self.treeTableActionHgLogHistory, self.enablerHgLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('hg state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), self.tableActionHgAdd, self.enablerHgFilesAdd, 'toolbar_images/add.png' )
        t.addSeparator()
        addTool( t, T_('Revert'), self.tableActionHgRevert, self.enablerHgFilesRevert, 'toolbar_images/revert.png' )
        addTool( t, T_('Commit'), self.treeActionHgCommit, self.enablerHgCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), self.treeActionHgPush, self.enablerHgPush, 'toolbar_images/push.png', thread_switcher=True )
        addTool( t, T_('Pull'), self.treeActionHgPull, icon_name='toolbar_images/pull.png', thread_switcher=True )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), self.tableActionHgDiffHeadVsWorking, self.enablerHgDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Hg Actions') )
        addMenu( m, T_('Revert'), self.tableActionHgRevert, self.enablerHgFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        addMenu( m, T_('Delete…'), self.tableActionHgDelete, self.main_window.table_view.enablerTableFilesExists )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )
        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeActionHgDiffHeadVsWorking, self.enablerHgDiffHeadVsWorking, 'toolbar_images/diff.png' )

    # ------------------------------------------------------------
    def treeActionHgLogHistory( self ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            hg_project = self.selectedHgProject()

            commit_log_view = wb_hg_log_history.WbHgLogHistoryView(
                    self.app,
                    T_('Commit Log for %s') % (hg_project.projectName(),),
                    self.main_window.getQIcon( 'wb.png' ) )

            func = self.app.threadSwitcher( commit_log_view.showCommitLogForRepository )
            func( hg_project, options )

    def _actionHgLogHistory( self, hg_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            commit_log_view = wb_hg_log_history.WbHgLogHistoryView(
                    self.app, T_('Commit Log for %s') % (filename,), self.main_window.getQIcon( 'wb.png' ) )

            func = self.app.threadSwitcher( commit_log_view.showCommitLogForFile )
            func( hg_project, filename, options )

    commit_key = 'hg-commit-dialog'
    def treeActionHgCommit( self ):
        if self.app.hasSingleton( self.commit_key ):
            self.log.error( 'Commit dialog is already open' )
            return

        hg_project = self.selectedHgProject()

        commit_dialog = wb_hg_commit_dialog.WbHgCommitDialog( self.app, hg_project )
        commit_dialog.commitAccepted.connect( self.__commitAccepted )
        commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        commit_dialog = self.app.getSingleton( self.commit_key )

        hg_project = self.selectedHgProject()
        message = commit_dialog.getMessage()
        commit_id = hg_project.cmdCommit( message )

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
