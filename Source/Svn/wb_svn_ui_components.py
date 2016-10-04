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

import wb_log_history_options_dialog

import wb_svn_ui_actions
import wb_svn_project
import wb_svn_commit_dialog
import wb_svn_info_dialog
import wb_svn_credential_dialogs
import wb_svn_annotate

import pysvn

from wb_background_thread import thread_switcher

#
#   Add tool bars and menu for use in the Main Window
#
#   add the commit code at this level to avoid import loops
#
class SvnMainWindowComponents(wb_svn_ui_actions.SvnMainWindowActions):
    def __init__( self, factory ):
        self.all_visible_table_columns = None

        super().__init__( factory )

    def createProject( self, project ):
        tm = self.table_view.table_model
        self.all_visible_table_columns = (tm.col_status, tm.col_name, tm.col_date)

        try:
            return wb_svn_project.SvnProject( self.app, project, self )

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Failed to add SVN repo %r' % (project.path,) )
            return None

    def addProjectInitWizardHandler( self, wc_path ):
        raise RuntimeError( 'SVN does not support project init' )

    def addProjectPreCloneWizardHandler( self, name, url, wc_path ):
        self.setStatusAction( T_('Checkout %(project)s') %
                                    {'project': name} )
        self.progress.start( T_('Checkout %(count)d') )

    def addProjectCloneWizardHandler( self, name, url, wc_path ):
        svn_project = wb_svn_project.SvnProject( self.app, None, self )

        try:
            rev = svn_project.cmdCheckout( url, wc_path )
            self.log.info( 'Checked out at revision r%d' % (rev.number,) )
            return True

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e )
            return False

    def addProjectPostCloneWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    def about( self ):
        return ['PySVN %d.%d.%d-%d' % pysvn.version
               ,'SVN %d.%d.%d %s' % pysvn.svn_version]

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff Base vs. Working'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionSvnDiffHeadVsWorking, self.enablerTreeTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Annotate'), self.tableActionSvnAnnotate_Bg, self.enablerTableSvnAnnotate )

        m.addSeparator()
        addMenu( m, T_('Add Folder…'), self.treeActionSvnAdd, self.enablerTreeSvnAdd )
        addMenu( m, T_('New Folder…'), self.treeActionSvnMkdir, self.enablerTreeSvnMkdir )

        m.addSeparator()
        addMenu( m, T_('Information'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSeparator()
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory_Bg, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addMenu( m, T_('Status'), self.treeActionSvnStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Add'), self.tableActionSvnAdd, self.enablerSvnAdd, 'toolbar_images/add.png' )
        addMenu( m, T_('Rename…'), self.tableActionSvnRename, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Revert…'), self.tableActionSvnRevert, self.enablerSvnRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), self.tableActionSvnDelete, self.main_window.table_view.enablerTableFilesExists, 'toolbar_images/delete.png' )

        m.addSeparator()
        addMenu( m, T_('Checkin…'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png' )

        m.addSeparator()
        addMenu( m, T_('Update'), self.treeActionSvnUpdate_Bg, icon_name='toolbar_images/update.png' )

        m.addSeparator()
        addMenu( m, T_('Cleanup'), self.treeActionSvnCleanup )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('svn logo'), style='font-size: 20pt; width: 40px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Svn', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addTool( t, T_('Log History'), self.treeTableActionSvnLogHistory_Bg, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addTool( t, T_('Info'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addTool( t, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        # ----------------------------------------
        t = addToolBar( T_('svn state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), self.tableActionSvnAdd, self.enablerSvnAdd, 'toolbar_images/add.png' )
        addTool( t, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Checkin'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png' )
        t.addSeparator()
        addTool( t, T_('Update'), self.treeActionSvnUpdate_Bg, icon_name='toolbar_images/update.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), self.tableActionSvnDiffBaseVsWorking, self.enablerTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.tableActionSvnDiffHeadVsWorking, self.enablerTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSection( T_('Status') )
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory_Bg, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )

        m.addSection( T_('Actions') )
        addMenu( m, T_('Add'), self.tableActionSvnAdd, self.enablerSvnAdd, 'toolbar_images/add.png' )
        addMenu( m, T_('Rename…'), self.tableActionSvnRename, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), self.tableActionSvnDelete, self.main_window.table_view.enablerTableFilesExists, 'toolbar_images/delete.png' )


    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), self.treeActionSvnDiffBaseVsWorking, self.enablerTreeSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeActionSvnDiffHeadVsWorking, self.enablerTreeSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Actions') )
        addMenu( m, T_('Add Folder…'), self.treeActionSvnAdd, self.enablerTreeSvnAdd )
        addMenu( m, T_('New Folder…'), self.treeActionSvnMkdir, self.enablerTreeSvnMkdir )

        m.addSeparator()
        addMenu( m, T_('Revert…'), self.treeActionSvnRevert, self.enablerTreeSvnRevert, 'toolbar_images/revert.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), self.treeTableActionSvnInfo, self.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), self.treeTableActionSvnProperties, self.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSeparator()
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory_Bg, self.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )


    def enablerTableSvnAnnotate( self ):
        if not self.isScmTypeActive():
            return False

        return True

    @thread_switcher
    def tableActionSvnAnnotate_Bg( self, checked ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionSvnAnnotate_Bg )

    @thread_switcher
    def __actionSvnAnnotate_Bg( self, svn_project, filename ):
        self.setStatusAction( T_('Annotate %s') % (filename,) )
        self.progress.start( T_('Annotate %(count)d'), 0 )

        yield self.switchToBackground

        try:
            all_annotation_nodes = svn_project.cmdAnnotationForFile( filename )
            all_annotate_revs = set()
            for node in all_annotation_nodes:
                all_annotate_revs.add( node.log_id )

            yield self.switchToForeground

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Cannot get annotations for %s:%s' % (project.path, filename) )

            yield self.switchToForeground
            return

        self.progress.end()
        self.progress.start( T_('Annotate Commit Logs %(count)d'), 0 )

        yield self.switchToBackground

        rev_min = min( all_annotate_revs )
        rev_max = max( all_annotate_revs )

        try:
            all_commit_logs = svn_project.cmdCommitLogForAnnotateFile( filename, rev_max, rev_min )

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Cannot get commit logs for %s:%s' % (project.path, filename) )
            all_commit_logs = []

        yield self.switchToForeground

        self.setStatusAction()
        self.progress.end()

        annotate_view = wb_svn_annotate.WbSvnAnnotateView(
                            self.app,
                            T_('Annotation of %s') % (filename,) )
        annotate_view.showAnnotationForFile( all_annotation_nodes, all_commit_logs )
        annotate_view.show()

    commit_key = 'svn-commit-dialog'

    def treeActionSvnCheckin( self, checked ):
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.getSingleton( self.commit_key )
            commit_dialog.raise_()
            return

        svn_project = self.selectedSvnProject()

        commit_dialog = wb_svn_commit_dialog.WbSvnCommitDialog( self.app, svn_project )
        commit_dialog.commitAccepted.connect( self.app.threadSwitcher( self.__commitAccepted_Bg ) )
        commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    @thread_switcher
    def __commitAccepted_Bg( self ):
        svn_project = self.selectedSvnProject()

        commit_dialog = self.app.getSingleton( self.commit_key )

        message = commit_dialog.getMessage()
        all_commit_files = commit_dialog.getAllCommitIncludedFiles()

        # hide the dialog
        commit_dialog.hide()

        self.setStatusAction( T_('Check in %s') % (svn_project.projectName(),) )
        self.progress.start( T_('Sent %(count)d'), 0 )

        yield self.switchToBackground

        try:
            commit_id = svn_project.cmdCommit( message, all_commit_files )

            yield self.switchToForeground

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Cannot Check in %s' % (svn_project.projectName(),) )

            yield self.switchToForeground
            self.__commitClosed()
            return

        headline = message.split('\n')[0]
        self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') %
                {'headline': headline, 'commit_id': commit_id} )

        self.setStatusAction( T_('Ready') )
        self.progress.end()

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

    def svnGetLogin( self, realm, username, may_save ):
        # used as a pysvn callback for callback_get_login
        dialog = wb_svn_credential_dialogs.WbSvnGetLoginDialog( self.app.top_window, realm, username, may_save )
        if dialog.exec_():
            return  (True
                    ,dialog.getUsername()
                    ,dialog.getPassword()
                    ,dialog.getSaveCredentials())

        else:
            return  (False
                    ,''
                    ,''
                    ,False)

    def svnSslServerTrustPrompt( self, realm, info_list, may_save ):
        # used as a pysvn callback for callback_ssl_server_trust_prompt
        dialog = wb_svn_credential_dialogs.WbSvnSslServerTrustDialog( self.app.top_window, realm, info_list, may_save )
        result = dialog.ShowModal()
        if result == wx.ID_OK:
            # Trust, save
            return  (True
                    ,dialog.getSaveTrust())
        else:
            # don't trust, don't save
            return  (False
                    ,False)

