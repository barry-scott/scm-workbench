'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_ui_components.py.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_svn_ui_actions
import wb_log_history_options_dialog

import wb_svn_project
import wb_svn_commit_dialog
import wb_svn_info_dialog
import wb_svn_log_history

import pysvn
#
#   Add tool bars and menu for use in the Main Window
#
#   add the commit code at this level to avoid import loops
#
class SvnMainWindowComponents(wb_svn_ui_actions.SvnMainWindowActions):
    def __init__( self ):
        super().__init__()

    def about( self ):
        return ['PySVN %d.%d.%d-%d' % pysvn.version
               ,'SVN %d.%d.%d %s' % pysvn.svn_version]

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff Base vs. Working'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionSvnDiffHeadVsWorking, self.enablerTreeTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSeparator()
        addMenu( m, T_('Info'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )
        m.addSeparator()
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addMenu( m, T_('Status'), self.treeActionSvnStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Add'), self.tableActionSvnAdd, self.enablerSvnAdd, 'toolbar_images/add.png' )
        addMenu( m, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnRevert, 'toolbar_images/revert.png' )

        m.addSeparator()
        addMenu( m, T_('Delete…'), self.tableActionSvnDelete, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Checkin…'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png', thread_switcher=True )

        m.addSeparator()
        addMenu( m, T_('Update…'), self.treeActionSvnUpdate, icon_name='toolbar_images/update.png', thread_switcher=True )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('svn logo'), style='font-size: 20pt; width: 40px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Svn', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addTool( t, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addTool( t, T_('Info'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addTool( t, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        # ----------------------------------------
        t = addToolBar( T_('svn state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), self.tableActionSvnAdd, self.enablerSvnAdd, 'toolbar_images/add.png' )
        addTool( t, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Checkin'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png', thread_switcher=True )
        t.addSeparator()
        addTool( t, T_('Update'), self.treeActionSvnUpdate, icon_name='toolbar_images/update.png', thread_switcher=True )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), self.tableActionSvnDiffBaseVsWorking, self.enablerTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.tableActionSvnDiffHeadVsWorking, self.enablerTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSection( T_('Status') )
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), self.treeActionSvnDiffBaseVsWorking, self.enablerTreeSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeActionSvnDiffHeadVsWorking, self.enablerTreeSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSection( T_('Status') )
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )

    def treeActionSvnLogHistory( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            svn_project = self.selectedSvnProject()

            log_history_view = wb_svn_log_history.WbSvnLogHistoryView(
                    self.app,
                    T_('Commit Log for %s:%s') % (svn_project.projectName(), tree_node.relativePath()),
                    self.main_window.getQIcon( 'wb.png' ) )

            log_history_view.showCommitLogForFile( svn_project, tree_node.relativePath(), options )
            log_history_view.show()

    def enablerTreeTableSvnLogHistory( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnLogHistory, self.enablerTableSvnLogHistory, default=False )

    def enablerTreeSvnLogHistory( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTableSvnLogHistory( self ):
        if not self.isScmTypeActive():
            return False

        return True

    def tableActionSvnLogHistory( self ):
        self.table_view.tableActionViewRepo( None, self.__actionSvnLogHistory )

    def treeTableActionSvnLogHistory( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnLogHistory, self.tableActionSvnLogHistory )

    def __actionSvnLogHistory( self, svn_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            commit_log_view = wb_svn_log_history.WbSvnLogHistoryView(
                    self.app,
                    T_('Commit Log for %s:%s') % (svn_project.projectName(), filename),
                    self.main_window.getQIcon( 'wb.png' ) )

            commit_log_view.showCommitLogForFile( svn_project, filename, options )
            commit_log_view.show()


    def treeActionSvnCheckin( self, checked ):
        if self.commit_dialog is not None:
            self.log.error( T_('Commit dialog is already open') )
            return

        svn_project = self.selectedSvnProject()

        self.commit_dialog = wb_svn_commit_dialog.WbSvnCommitDialog( self.app, svn_project )
        self.commit_dialog.commitAccepted.connect( self.app.threadSwitcher( self.__commitAccepted ) )
        self.commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        self.commit_dialog.show()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        svn_project = self.selectedSvnProject()
        message = self.commit_dialog.getMessage()

        # hide the dialog
        self.commit_dialog.hide()

        self.setStatusAction( T_('Check in %s') % (svn_project.projectName(),) )
        self.progress.start( T_('Sent %(count)d'), 0 )

        yield self.switchToBackground

        commit_id = svn_project.cmdCommit( message )

        yield self.switchToForeground

        headline = message.split('\n')[0]
        self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') %
                {'headline': headline, 'commit_id': commit_id} )

        self.setStatusAction( T_('Ready') )
        self.progress.end()

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
