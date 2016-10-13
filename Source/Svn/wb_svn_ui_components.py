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

import wb_ui_components

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
class SvnMainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        self.all_visible_table_columns = None

        super().__init__( 'svn', factory )

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
        act = self.ui_actions

        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff Base vs. Working'), act.treeTableActionSvnDiffBaseVsWorking, act.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), act.treeTableActionSvnDiffHeadVsWorking, act.enablerTreeTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Annotate'), act.tableActionSvnAnnotate_Bg, act.enablerTableSvnAnnotate )

        m.addSeparator()
        addMenu( m, T_('Add Folder…'), act.treeActionSvnAdd_Bg, act.enablerTreeSvnAdd )
        addMenu( m, T_('New Folder…'), act.treeActionSvnMkdir_Bg, act.enablerTreeSvnMkdir )

        m.addSeparator()
        addMenu( m, T_('Information'), act.treeTableActionSvnInfo_Bg, act.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), act.treeTableActionSvnProperties_Bg, act.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSeparator()
        addMenu( m, T_('Log History'), act.treeTableActionSvnLogHistory_Bg, act.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addMenu( m, T_('Status'), act.treeActionSvnStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Add'), act.tableActionSvnAdd_Bg, act.enablerSvnAdd, 'toolbar_images/add.png' )
        addMenu( m, T_('Rename…'), act.tableActionSvnRename_Bg, act.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Revert…'), act.tableActionSvnRevert_Bg, act.enablerSvnRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), act.tableActionSvnDelete_Bg, act.main_window.table_view.enablerTableFilesExists, 'toolbar_images/delete.png' )

        m.addSeparator()
        addMenu( m, T_('Checkin…'), act.treeActionSvnCheckin, act.enablerSvnCheckin, 'toolbar_images/checkin.png' )

        m.addSeparator()
        addMenu( m, T_('Update'), act.treeActionSvnUpdate_Bg, icon_name='toolbar_images/update.png' )

        m.addSeparator()
        addMenu( m, T_('Cleanup'), act.treeActionSvnCleanup )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('svn logo'), style='font-size: 20pt; width: 40px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Svn', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), act.treeTableActionSvnDiffBaseVsWorking, act.enablerTreeTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addTool( t, T_('Log History'), act.treeTableActionSvnLogHistory_Bg, act.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )
        addTool( t, T_('Info'), act.treeTableActionSvnInfo_Bg, act.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addTool( t, T_('Properties'), act.treeTableActionSvnProperties_Bg, act.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        # ----------------------------------------
        t = addToolBar( T_('svn state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), act.tableActionSvnAdd_Bg, act.enablerSvnAdd, 'toolbar_images/add.png' )
        addTool( t, T_('Revert'), act.tableActionSvnRevert_Bg, act.enablerSvnRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Checkin'), act.treeActionSvnCheckin, act.enablerSvnCheckin, 'toolbar_images/checkin.png' )
        t.addSeparator()
        addTool( t, T_('Update'), act.treeActionSvnUpdate_Bg, icon_name='toolbar_images/update.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), act.tableActionSvnDiffBaseVsWorking, act.enablerTableSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), act.tableActionSvnDiffHeadVsWorking, act.enablerTableSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), act.treeTableActionSvnInfo_Bg, act.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), act.treeTableActionSvnProperties_Bg, act.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSection( T_('Status') )
        addMenu( m, T_('Log History'), act.treeTableActionSvnLogHistory_Bg, act.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )

        m.addSection( T_('Actions') )
        addMenu( m, T_('Add'), act.tableActionSvnAdd_Bg, act.enablerSvnAdd, 'toolbar_images/add.png' )
        addMenu( m, T_('Rename…'), act.tableActionSvnRename_Bg, self.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Revert'), act.tableActionSvnRevert_Bg, act.enablerSvnRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), act.tableActionSvnDelete_Bg, self.main_window.table_view.enablerTableFilesExists, 'toolbar_images/delete.png' )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff Base vs. Working'), act.treeActionSvnDiffBaseVsWorking, act.enablerTreeSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), act.treeActionSvnDiffHeadVsWorking, act.enablerTreeSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSection( T_('Actions') )
        addMenu( m, T_('Add Folder…'), act.treeActionSvnAdd_Bg, act.enablerTreeSvnAdd )
        addMenu( m, T_('New Folder…'), act.treeActionSvnMkdir_Bg, act.enablerTreeSvnMkdir )

        m.addSeparator()
        addMenu( m, T_('Revert…'), act.treeActionSvnRevert_Bg, act.enablerTreeSvnRevert, 'toolbar_images/revert.png' )

        m.addSection( T_('Info' ) )
        addMenu( m, T_('Information'), act.treeTableActionSvnInfo_Bg, act.enablerTreeTableSvnInfo, 'toolbar_images/info.png' )
        addMenu( m, T_('Properties'), act.treeTableActionSvnProperties_Bg, act.enablerTreeTableSvnProperties, 'toolbar_images/property.png' )

        m.addSeparator()
        addMenu( m, T_('Log History'), act.treeTableActionSvnLogHistory_Bg, act.enablerTreeTableSvnLogHistory, 'toolbar_images/history.png' )

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

