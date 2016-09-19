'''
 ====================================================================
  (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_ui_components.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_ui_components
import wb_common_dialogs

import wb_svn_project
import wb_svn_info_dialog
import wb_svn_properties_dialog
import wb_svn_dialogs

import pysvn
import pathlib

from wb_background_thread import thread_switcher

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the commit window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class SvnMainWindowActions(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__( 'svn' )

    def setupDebug( self ):
        self._debug = self.main_window.app._debugSvnUi

    #--- Enablers ---------------------------------------------------------

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def enablerTreeTableSvnInfo( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnInfo, self.enablerTableSvnInfo, default=False )

    def enablerTreeTableSvnProperties( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnProperties, self.enablerTableSvnProperties, default=False )

    def enablerTreeTableSvnDiffBaseVsWorking( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnDiffBaseVsWorking, self.enablerTableSvnDiffBaseVsWorking, default=False )

    def enablerTreeTableSvnDiffHeadVsWorking( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnDiffHeadVsWorking, self.enablerTableSvnDiffHeadVsWorking, default=False )

    # ------------------------------------------------------------
    def treeTableActionSvnDiffBaseVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffBaseVsWorking, self.tableActionSvnDiffBaseVsWorking )

    def treeTableActionSvnDiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffHeadVsWorking, self.tableActionSvnDiffHeadVsWorking )

    def treeTableActionSvnInfo( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnInfo, self.tableActionSvnInfo )

    def treeTableActionSvnProperties( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnProperties, self.tableActionSvnProperties )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def selectedSvnProject( self ):
        scm_project = self.table_view.selectedScmProject()
        if scm_project is None:
            return None

        if not isinstance( scm_project, wb_svn_project.SvnProject ):
            return None

        return scm_project

    def enablerTreeSvnDiffBaseVsWorking( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTreeSvnDiffHeadVsWorking( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTreeSvnInfo( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTreeSvnMkdir( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTreeSvnRevert( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTreeSvnAdd( self ):
        return not self._enablerTreeSvnIsControlled()

    def enablerTreeSvnProperties( self ):
        return self._enablerTreeSvnIsControlled()

    def _enablerTreeSvnIsControlled( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return False

        tree_node.relativePath()

        if not tree_node.project.hasFileState( tree_node.relativePath() ):
            return False

        file_state = tree_node.project.getFileState( tree_node.relativePath() )
        return file_state.isControlled()

    # ------------------------------------------------------------
    def treeActionSvnDiffBaseVsWorking( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        try:
            diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=False )
            self.showDiffText( 'Diff Base vs. Working from %s' % (tree_node.relativePath(),), diff_text.split('\n') )

        except wb_svn_project.ClientError as e:
            tree_node.project.logClientError( e )


    def treeActionSvnDiffHeadVsWorking( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        try:
            diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=True )
            self.showDiffText( 'Diff Head vs. Working from %s' % (tree_node.relativePath(),), diff_text )

        except wb_svn_project.ClientError as e:
            tree_node.project.logClientError( e )

    def treeActionSvnAdd( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_svn_dialogs.WbAddFolderDialog( self.app, self.main_window, tree_node.relativePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdAdd( tree_node.relativePath(), depth=dialog.getDepth(), force=dialog.getForce() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            self.main_window.updateTableView()

    def treeActionSvnRevert( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_svn_dialogs.WbRevertFolderDialog( self.app, self.main_window, tree_node.absolutePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdRevert( tree_node.relativePath(), depth=dialog.getDepth() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            self.main_window.updateTableView()

    def treeActionSvnMkdir( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_common_dialogs.WbNewFolderDialog( self.app, self.main_window, tree_node.absolutePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdMkdir( tree_node.relativePath() / dialog.getFolderName() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            self.main_window.updateTableView()

    def treeActionSvnInfo( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        try:
            info = tree_node.project.cmdInfo( tree_node.relativePath() )

        except wb_svn_project.ClientError as e:
            tree_node.project.logClientError( e )
            return

        dialog = wb_svn_info_dialog.InfoDialog( self.app, self.main_window, tree_node.relativePath(), tree_node.absolutePath(), info )
        dialog.exec_()

    def treeActionSvnProperties( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        svn_project = tree_node.project
        filename = tree_node.relativePath()
        prop_dict = svn_project.cmdPropList( filename )

        dialog = wb_svn_properties_dialog.FolderPropertiesDialog( self.app, self.main_window, filename, prop_dict )
        if dialog.exec_():
            for is_present, name, value in dialog.getModifiedProperties():
                try:
                    if not is_present:
                        # delete name
                        svn_project.cmdPropDel( name, filename )

                    else:
                        # add/update name value
                        svn_project.cmdPropSet( name, value, filename )

                except wb_svn_project.ClientError as e:
                    svn_project.logClientError( e )

        self.main_window.updateTableView()

    def treeActionSvnCleanup( self, checked ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        self.top_window.setStatusAction( T_('Cleanup %s') % (tree_node.project.projectName(),) )

        try:
            tree_node.project.cmdCleanup()
            self.log.info( 'Cleanup finished for %s' % (tree_node.project.projectName(),) )

        except wb_svn_project.ClientError as e:
            tree_node.project.logClientError( e )

        self.top_window.setStatusAction()

    @thread_switcher
    def treeActionSvnUpdate_Bg( self, checked ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        path = tree_node.relativePath()
        if path == pathlib.Path( '.' ):
            self.setStatusAction( T_('Update %(project)s') %
                                        {'project': tree_node.project.projectName()} )

        else:
            self.setStatusAction( T_('Update %(project)s:%(filename)s') %
                                        {'project': tree_node.project.projectName()
                                        ,'filename': path} )

        self.progress.start( T_('Updated %(count)d') )

        yield self.switchToBackground
        try:
            svn_project = tree_node.project
            filename = tree_node.relativePath()

            svn_project.initNotificationOfFilesInConflictCount()

            rev_list = svn_project.cmdUpdate(
                                filename,
                                tree_node.svn_project.svn_rev_head,
                                tree_node.svn_project.svn_depth_infinity )
            yield self.switchToForeground
            self.__updateToRevisionProcessResults( tree_node, rev_list )

        except pysvn.ClientError as e:
            svn_project.logClientError( e )

            yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()

        self.main_window.updateTableView()

    def __updateToRevisionProcessResults( self, tree_node, rev_list ):
        svn_project = tree_node.project
        filename = tree_node.relativePath()

        if rev_list is not None:
            for rev in rev_list:
                if rev.number > 0:
                    count = self.progress.getEventCount()
                    if count == 0:
                        self.log.info( T_('Updated %(project)s:%(filename)s to revision %(rev)d, no new updates') %
                                                {'project': svn_project.projectName()
                                                ,'filename': filename
                                                ,'rev': rev.number} )
                    else:
                        self.log.info( S_('Updated %(project)s:%(filename)s to revision %(rev)d, %(count)d new update', 
                                          'Updated %(project)s:%(filename)s to revision %(rev)d, %(count)d new updates', count) %
                                                {'project': svn_project.projectName()
                                                ,'filename': filename
                                                ,'rev': rev.number
                                                ,'count': count} )
                else:
                    self.log.warning( T_('Already up to date') )

            files_in_conflict = self.progress.getInConflictCount()
            if files_in_conflict > 0:
                box = QtWidgets.QMessageBox( 
                        QtWidgets.QMessageBox.Information,
                        T_('Warning'),
                        S_("%d file is in conflict", 
                           "%d files are in conflict",
                            files_in_conflict) %
                                (files_in_conflict,),
                        QtWidgets.QMessageBox.Close,
                        parent=self.top_window )
                box.exec_()

    def treeActionSvnStatus( self ):
        pass

    #------------------------------------------------------------
    #
    # table actions
    #
    #------------------------------------------------------------
    def enablerTableSvnDiffBaseVsWorking( self ):
        if not self.isScmTypeActive():
            return False

        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not file_state.isModified():
                return False

        return True

    def enablerTableSvnDiffHeadVsWorking( self ):
        if not self.isScmTypeActive():
            return False

        return True

    def enablerTableSvnInfo( self ):
        return self._enablerTableSvnIsControlled()

    def enablerTableSvnProperties( self ):
        return self._enablerTableSvnIsControlled()

    def enablerSvnAdd( self ):
        # can only add uncontrolled files
        return self.__enablerTableSvnIsUncontrolled()

    def enablerSvnRevert( self ):
        # can only revert uncontrolled files
        return self._enablerTableSvnIsControlled()

    def __enablerTableSvnIsUncontrolled( self ):
        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not file_state.isUncontrolled():
                return False

        return True

    def _enablerTableSvnIsControlled( self ):
        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not file_state.isControlled():
                return False

        return True

    def enablerSvnCheckin( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return False

        return tree_node.project.numUncommittedFiles() > 0

    def __enablerSvnFilesModified( self ):
        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not (file_state.isAdded() or file_state.isModified() or file_state.isDeleted()):
                return False

        return True

    # ------------------------------------------------------------
    def tableActionSvnDiffBaseVsWorking( self ):
        for file_state in self.tableSelectedAllFileStates():
            self.diffTwoFiles(
                    T_('Diff Base vs. Working %s') % (file_state.relativePath(),),
                    file_state.getTextLinesBase(),
                    file_state.getTextLinesWorking(),
                    T_('Base %s') % (file_state.relativePath(),),
                    T_('Working %s') % (file_state.relativePath(),)
                    )

    def tableActionSvnDiffHeadVsWorking( self ):
        for file_state in self.tableSelectedAllFileStates():
            self.diffTwoFiles(
                    T_('Diff HEAD vs. Working %s') % (file_state.relativePath(),),
                    file_state.getTextLinesBase(),
                    file_state.getTextLinesWorking(),
                    T_('HEAD %s') % (file_state.relativePath(),),
                    T_('Working %s') % (file_state.relativePath(),)
                    )

    def tableActionSvnInfo( self ):
        def execute_function( svn_project, filename ):
            try:
                info = svn_project.cmdInfo( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

            dialog = wb_svn_info_dialog.InfoDialog( self.app, self.main_window, filename, svn_project.pathForSvn( filename ), info )
            dialog.exec_()

        self.__tableActionSvnCmd( execute_function )

    def tableActionSvnProperties( self ):
        def execute_function( svn_project, filename ):
            try:
                prop_dict = svn_project.cmdPropList( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

            dialog = wb_svn_properties_dialog.FilePropertiesDialog( self.app, self.main_window, filename, prop_dict )
            if dialog.exec_():
                for is_present, name, value in dialog.getModifiedProperties():
                    try:
                        if not is_present:
                            # delete name
                            svn_project.cmdPropDel( name, filename )
                        else:
                            # add/update name value
                            svn_project.cmdPropSet( name, value, filename )

                    except wb_svn_project.ClientError as e:
                        svn_project.logClientError( e )
                        return

            self.main_window.updateTableView()

        self.__tableActionSvnCmd( execute_function )

    def tableActionSvnAdd( self ):
        def execute_function( svn_project, filename ):
            svn_project.cmdAdd( filename )

        self.__tableActionSvnCmd( execute_function )

    def tableActionSvnRevert( self ):
        def execute_function( svn_project, filename ):
            try:
                svn_project.cmdRevert( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

        self.__tableActionSvnCmd( execute_function, are_you_sure )

    def tableActionSvnDelete( self ):
        def execute_function( svn_project, filename ):
            try:
                svn_project.cmdDelete( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureDelete( self.main_window, all_filenames )

        self.__tableActionSvnCmd( execute_function, are_you_sure )

    def tableActionSvnRename( self ):
        def execute_function( svn_project, filename ):
            rename = wb_common_dialogs.WbRenameFilenameDialog( self.app, self.main_window )
            rename.setName( filename.name )

            if rename.exec_():
                try:
                    # handles rename for controlled and uncontrolled files
                    svn_project.cmdRename( filename, filename.with_name( rename.getName() ) )

                except wb_svn_project.ClientError as e:
                    svn_project.logClientError( e )

        self.__tableActionSvnCmd( execute_function )

    def __tableActionSvnCmd( self, execute_function, are_you_sure_function=None ):
        svn_project = self.selectedSvnProject()
        if svn_project is None:
            return

        try:
            def finalise( svn_project ):
                # take account of the change
                self.top_window.updateTableView()

            self.table_view.tableActionViewRepo( execute_function, are_you_sure_function, finalise )

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e )

        self.main_window.updateTableView()

    # ------------------------------------------------------------
    def selectedSvnProjectTreeNode( self ):
        if not self.isScmTypeActive():
            return None

        tree_node = self.table_view.table_model.selectedScmProjectTreeNode()

        # if the place holder is being used return none
        if not isinstance( tree_node, wb_svn_project.SvnProjectTreeNode ):
            return None

        return tree_node
