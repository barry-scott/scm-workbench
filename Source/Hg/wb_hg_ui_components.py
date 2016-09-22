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

import hglib
import shutil

from wb_background_thread import thread_switcher


class HgMainWindowComponents(wb_hg_ui_actions.HgMainWindowActions):
    def __init__( self ):
        super().__init__()

    def setTopWindow( self, top_window ):
        super().setTopWindow( top_window )

        prefs = self.app.prefs.hg
        if prefs.program is not None:
            hglib.HGPATH = str( prefs.program )

        self.log.info( T_('Hg using program %s') % (hglib.HGPATH,) )

    def createProject( self, project ):
        tm = self.table_view.table_model
        self.all_visible_table_columns = (tm.col_status, tm.col_name, tm.col_date)

        if shutil.which( hglib.HGPATH ) is None:
            self.log.error( T_('Murcurial "hg" command line tool not found') )
            return None

        try:
            return wb_hg_project.HgProject( self.app, project, self )

        except hglib.error.ServerError as e:
            self.app.log.error( T_('Failed to add Hg repo %s') % (project.path,) )
            self.app.log.error( T_('hg error: %s') % (e,) )
            return None

    def addProjectInitWizardHandler( self, wc_path ):
        try:
            wb_hg_project.hgInit( wc_path )
            return True

        except hglib.error.ServerError as e:
            self.app.log.error( T_('Failed to init Hg repo %r') % (project.path,) )
            self.app.log.error( T_('hg error: %s') % (e,) )
            return False

    def addProjectPreCloneWizardHandler( self, name, url, wc_path ):
        self.setStatusAction( T_('Clone %(project)s') %
                                    {'project': name} )
        self.progress.start( T_('No progress available for hg') )

    def addProjectCloneWizardHandler( self, name, url, wc_path ):
        try:
            wb_hg_project.hgClone( url, wc_path )
            return True

        except hglib.error.ServerError as e:
            self.app.log.error( T_('Failed to clone Hg repo from %(url)s into %(path)s') % 
                                {'url': url
                                ,'path': wc_path} )
            self.app.log.error( 'hg error: %s' % (e,) )
            return False

    def addProjectPostCloneWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    def about( self ):
        if shutil.which( hglib.HGPATH ) is None:
            return ['Murcurial "hg" command line tool not found']

        else:
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
        addMenu( m, T_('Push…'), self.treeActionHgPush_Bg, self.enablerHgPush, 'toolbar_images/push.png' )
        addMenu( m, T_('Pull…'), self.treeActionHgPull_Bg, icon_name='toolbar_images/pull.png' )

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
        addTool( t, T_('Commit History'), self.treeTableActionHgLogHistory_Bg, self.enablerHgLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('hg state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), self.tableActionHgAdd, self.enablerHgFilesAdd, 'toolbar_images/add.png' )
        t.addSeparator()
        addTool( t, T_('Revert'), self.tableActionHgRevert, self.enablerHgFilesRevert, 'toolbar_images/revert.png' )
        addTool( t, T_('Commit'), self.treeActionHgCommit, self.enablerHgCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), self.treeActionHgPush_Bg, self.enablerHgPush, 'toolbar_images/push.png' )
        addTool( t, T_('Pull'), self.treeActionHgPull_Bg, icon_name='toolbar_images/pull.png' )

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
    @thread_switcher
    def treeActionHgLogHistory_Bg( self ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        hg_project = self.selectedHgProject()

        commit_log_view = wb_hg_log_history.WbHgLogHistoryView(
                self.app,
                T_('Commit Log for %s') % (hg_project.projectName(),) )

        yield from commit_log_view.showCommitLogForRepository_Bg( hg_project, options )

    @thread_switcher
    def tableActionHgLogHistory_Bg( self ):
        yield from self.table_view.tableActionViewRepo_Bg( self._actionHgLogHistory_Bg )

    def _actionHgLogHistory_Bg( self, hg_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        commit_log_view = wb_hg_log_history.WbHgLogHistoryView(
                self.app,
                T_('Commit Log for %s') % (filename,) )

        yield from commit_log_view.showCommitLogForFile_Bg( hg_project, filename, options )

    commit_key = 'hg-commit-dialog'
    def treeActionHgCommit( self ):
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.getSingleton( self.commit_key )
            commit_dialog.raise_()
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
