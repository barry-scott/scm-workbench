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
import wb_svn_info_dialog
import wb_svn_properties_dialog

import pysvn
import pathlib

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

    def enablerTreeTableSvnLogHistory( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnLogHistory, self.enablerTableSvnLogHistory, default=False )

    # ------------------------------------------------------------
    def treeTableActionSvnDiffBaseVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffBaseVsWorking, self.tableActionSvnDiffBaseVsWorking )

    def treeTableActionSvnDiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffHeadVsWorking, self.tableActionSvnDiffHeadVsWorking )

    def treeTableActionSvnLogHistory( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnLogHistory, self.tableActionSvnLogHistory )

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
        return self.__enablerTreeSvnIsControlled()

    def enablerTreeSvnDiffHeadVsWorking( self ):
        return self.__enablerTreeSvnIsControlled()

    def enablerTreeSvnLogHistory( self ):
        return self.__enablerTreeSvnIsControlled()

    def enablerTreeSvnInfo( self ):
        return self.__enablerTreeSvnIsControlled()

    def enablerTreeSvnProperties( self ):
        return self.__enablerTreeSvnIsControlled()

    def __enablerTreeSvnIsControlled( self ):
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

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=False )
        self.main_window.showDiffText( 'Diff Base vs. Working from %s' % (tree_node.relativePath(),), diff_text.split('\n') )

    def treeActionSvnDiffHeadVsWorking( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=True )
        self.main_window.showDiffText( 'Diff Head vs. Working from %s' % (tree_node.relativePath(),), diff_text )

    def treeActionSvnInfo( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        project = tree_node.project
        info = project.cmdInfo( tree_node.relativePath() )

        dialog = wb_svn_info_dialog.InfoDialog( self.app, self.main_window, tree_node.relativePath(), tree_node.absolutePath(), info )
        dialog.exec_()

    def treeActionSvnProperties( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        project = tree_node.project
        filename = tree_node.relativePath()
        prop_dict = project.cmdPropList( filename )

        dialog = wb_svn_properties_dialog.FolderPropertiesDialog( self.app, self.main_window, filename, prop_dict )
        if dialog.exec_():
            for is_present, name, value in dialog.getModifiedProperties():
                if not is_present:
                    # delete name
                    project.cmdPropDel( name, filename )

                else:
                    # add/update name value
                    project.cmdPropSet( name, value, filename )

        self.main_window.updateTableView()

    def treeActionSvnLogHistory( self ):
        print( 'treeActionSvnLogHistory' )

    def treeActionSvnUpdate( self, checked ):
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
        rev_list = self.__updateToRevision(
                            tree_node,
                            tree_node.project.svn_rev_head,
                            tree_node.project.svn_depth_infinity )

        yield self.switchToForeground
        self.__updateToRevisionProcessResults( tree_node, rev_list )

    def __updateToRevision( self, tree_node, rev, svndepth ):
        project = tree_node.project
        filename = tree_node.relativePath()

        try:
            project.initNotificationOfFilesInConflictCount()

            rev_list = project.cmdUpdateBg( filename, depth=svndepth, revision=rev )

            return rev_list

        except pysvn.ClientError as e:
            all_client_error_lines = project.clientErrorToStrList( e )
            for line in all_client_error_lines:
                self.app.log.error( line )

            self.top_window.errorMessage( 'Svn Error', '\n'.join( all_client_error_lines ) )
            return None
        
    def __updateToRevisionProcessResults( self, tree_node, rev_list ):
        project = tree_node.project
        filename = tree_node.relativePath()

        if rev_list is not None:
            for rev in rev_list:
                if rev.number > 0:
                    count = self.progress.getEventCount()
                    if count == 0:
                        self.log.info( T_('Updated %(project)s:%(filename)s to revision %(rev)d, no new updates') %
                                                {'project': project.projectName()
                                                ,'filename': filename
                                                ,'rev': rev.number} )
                    else:
                        self.log.info( S_('Updated %(project)s:%(filename)s to revision %(rev)d, %(count)d new update', 
                                          'Updated %(project)s:%(filename)s to revision %(rev)d, %(count)d new updates', count) %
                                                {'project': project.projectName()
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

        self.progress.end()
        self.setStatusAction()

        self.main_window.updateTableView()

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

    def enablerTableSvnLogHistory( self ):
        if not self.isScmTypeActive():
            return False

        return True

    def enablerTableSvnInfo( self ):
        return self.__enablerSvnFilesControlled()

    def enablerTableSvnProperties( self ):
        return self.__enablerSvnFilesControlled()

    def enablerSvnAdd( self ):
        # can only add uncontrolled files
        return self.__enablerSvnFilesUncontrolled()

    def enablerSvnRevert( self ):
        # can only revert uncontrolled files
        return self.__enablerSvnFilesControlled()

    def __enablerSvnFilesUncontrolled( self ):
        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not file_state.isUncontrolled():
                return False

        return True

    def __enablerSvnFilesControlled( self ):
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
                    file_state.getTextLinesBase(),
                    file_state.getTextLinesWorking(),
                    T_('Diff Base vs. Working %s') % (file_state.filePath(),),
                    T_('Base %s') % (file_state.filePath(),),
                    T_('Working %s') % (file_state.filePath(),)
                    )

    def tableActionSvnDiffHeadVsWorking( self ):
        for file_state in self.tableSelectedAllFileStates():
            self.diffTwoFiles(
                    file_state.getTextLinesBase(),
                    file_state.getTextLinesWorking(),
                    T_('Diff HEAD vs. Working %s') % (file_state.filePath(),),
                    T_('HEAD %s') % (file_state.filePath(),),
                    T_('Working %s') % (file_state.filePath(),)
                    )

    def tableActionSvnInfo( self ):
        def action( project, filename ):
            info = project.cmdInfo( filename )

            dialog = wb_svn_info_dialog.InfoDialog( self.app, self.main_window, filename, project.pathForSvn( filename ), info )
            dialog.exec_()

        self.__tableActionSvnCmd( action )

    def tableActionSvnProperties( self ):
        def action( project, filename ):
            prop_dict = project.cmdPropList( filename )

            dialog = wb_svn_properties_dialog.FilePropertiesDialog( self.app, self.main_window, filename, prop_dict )
            if dialog.exec_():
                for is_present, name, value in dialog.getModifiedProperties():
                    if not is_present:
                        # delete name
                        project.cmdPropDel( name, filename )
                    else:
                        # add/update name value
                        project.cmdPropSet( name, value, filename )

            self.main_window.updateTableView()

        self.__tableActionSvnCmd( action )

    def tableActionSvnLogHistory( self ):
        print( 'tableActionSvnLogHistory' )

    def tableActionSvnAdd( self ):
        def action( project, filename ):
            project.cmdAdd( filename )

        self.__tableActionSvnCmd( action )

    def tableActionSvnRevert( self ):
        def action( project, filename ):
            project.cmdRevert( filename )

        self.__tableActionSvnCmd( action )

    def tableActionSvnDelete( self ):
        def action( project, filename ):
            project.cmdDelete( filename )

        self.__tableActionSvnCmd( action )

    def __tableActionSvnCmd( self, cmd ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        project = tree_node.project

        try:
            for file_state in self.tableSelectedAllFileStates():
                cmd( project, file_state.filePath() )

        except wb_svn_project.ClientError as e:
            all_client_error_lines = project.clientErrorToStrList( e )
            for line in all_client_error_lines:
                self.app.log.error( line )

            self.top_window.errorMessage( 'Svn Error', '\n'.join( all_client_error_lines ) )

        self.main_window.updateTableView()


    # ------------------------------------------------------------
    def selectedSvnProjectTreeNode( self ):
        if not self.isScmTypeActive():
            return None

        tree_node = self.table_view.table_model.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_svn_project.SvnProjectTreeNode )
        return tree_node
