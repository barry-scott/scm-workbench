'''
 ====================================================================
  (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_ui_actions.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_log_history_options_dialog
import wb_ui_actions
import wb_common_dialogs

import wb_svn_project
import wb_svn_info_dialog
import wb_svn_properties_dialog
import wb_svn_dialogs
import wb_svn_commit_dialog

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
class SvnMainWindowActions(wb_ui_actions.WbMainWindowActions):
    def __init__( self, factory ):
        super().__init__( 'svn', factory )

    def setupDebug( self ):
        self._debug = self.main_window.app._debug_options._debugSvnUi

    #--- Enablers ---------------------------------------------------------

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def enablerTreeTableSvnInfo( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnInfo, self.enablerTableSvnInfo )

    def enablerTreeTableSvnProperties( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnProperties, self.enablerTableSvnProperties )

    def enablerTreeTableSvnDiffBaseVsWorking( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnDiffBaseVsWorking, self.enablerTableSvnDiffBaseVsWorking )

    def enablerTreeTableSvnDiffHeadVsWorking( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnDiffHeadVsWorking, self.enablerTableSvnDiffHeadVsWorking )

    # ------------------------------------------------------------
    def treeTableActionSvnDiffBaseVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffBaseVsWorking, self.tableActionSvnDiffBaseVsWorking )

    def treeTableActionSvnDiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionSvnDiffHeadVsWorking, self.tableActionSvnDiffHeadVsWorking )

    @thread_switcher
    def treeTableActionSvnInfo_Bg( self, checked=None ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionSvnInfo, self.tableActionSvnInfo_Bg )

    @thread_switcher
    def treeTableActionSvnProperties_Bg( self, checked=None ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionSvnProperties_Bg, self.tableActionSvnProperties_Bg )

    #------------------------------------------------------------
    def enablerTreeTableSvnLogHistory( self ):
        return self.main_window.callTreeOrTableFunction( self.enablerTreeSvnLogHistory, self.enablerTableSvnLogHistory )

    def enablerTreeSvnLogHistory( self ):
        return self._enablerTreeSvnIsControlled()

    def enablerTableSvnLogHistory( self ):
        return self._enablerTableSvnIsControlled()

    @thread_switcher
    def tableActionSvnLogHistory_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionSvnLogHistory_Bg )

    @thread_switcher
    def treeTableActionSvnLogHistory_Bg( self, checked=None ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionSvnLogHistory_Bg, self.tableActionSvnLogHistory_Bg )

    @thread_switcher
    def treeActionSvnLogHistory_Bg( self, checked=None ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        yield from self.__actionSvnLogHistory_Bg( self.selectedSvnProject(), tree_node.relativePath() )

    @thread_switcher
    def __actionSvnLogHistory_Bg( self, svn_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )
        # as soon as possible del options to attemtp to avoid XCB errors
        if not options.exec_():
            return

        self.setStatusAction( T_('Log for %(filename)s') %
                                    {'filename': filename} )
        self.progress.start( T_('Logs %(count)d') )

        yield self.switchToBackground
        try:
            all_commit_nodes = svn_project.cmdCommitLogForFile( filename, options.getLimit(), options.getSince(), options.getUntil())

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Cannot get commit logs for %s:%s' % (svn_project.projectName(), filename) )

            yield self.switchToForeground
            return

        if len(all_commit_nodes) > 0:
            yield self.switchToForeground
            self.progress.start( T_('Tags %(count)d') )

            yield self.switchToBackground
            try:
                all_tag_nodes = svn_project.cmdTagsForFile( filename, all_commit_nodes[-1]['revision'].number )

                all_commit_nodes.extend( all_tag_nodes )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e, 'Cannot get tags for %s:%s' % (svn_project.projectName(), filename) )
                # continue to show the logs we have got

        def key( node ):
            return -node['revision'].number

        all_commit_nodes.sort( key=key )

        yield self.switchToForeground
        self.progress.end()
        self.setStatusAction()

        log_history_view = self.factory.logHistoryView(
                self.app,
                T_('Commit Log for %(project)s:%(path)s') %
                        {'project': svn_project.projectName()
                        ,'path': filename} )

        log_history_view.showCommitLogForFile( svn_project, filename, all_commit_nodes )
        log_history_view.show()

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

    @thread_switcher
    def treeActionSvnAdd_Bg( self, checked=None ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_svn_dialogs.WbAddFolderDialog( self.app, self.main_window, tree_node.relativePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdAdd( tree_node.relativePath(), depth=dialog.getDepth(), force=dialog.getForce() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            yield from self.main_window.updateTableView_Bg()

    @thread_switcher
    def treeActionSvnRevert_Bg( self, checked=None ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_svn_dialogs.WbRevertFolderDialog( self.app, self.main_window, tree_node.absolutePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdRevert( tree_node.relativePath(), depth=dialog.getDepth() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            yield from self.main_window.updateTableView_Bg()

    @thread_switcher
    def treeActionSvnMkdir_Bg( self, checked=None ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        dialog = wb_common_dialogs.WbNewFolderDialog( self.app, self.main_window, tree_node.absolutePath() )
        if dialog.exec_():
            try:
                tree_node.project.cmdMkdir( tree_node.relativePath() / dialog.getFolderName() )

            except wb_svn_project.ClientError as e:
                tree_node.project.logClientError( e )

            yield from self.main_window.updateTableView_Bg()

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

    @thread_switcher
    def treeActionSvnProperties_Bg( self, checked=None ):
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

        yield from self.main_window.updateTableView_Bg()

    def treeActionSvnCleanup( self, checked=None ):
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
    def treeActionSvnUpdate_Bg( self, checked=None ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return

        path = tree_node.relativePath()
        if path == pathlib.Path( '.' ):
            msg = (T_('Update %(project)s') %
                        {'project': tree_node.project.projectName()})

        else:
            msg = (T_('Update %(project)s:%(filename)s') %
                        {'project': tree_node.project.projectName()
                        ,'filename': path})

        self.log.infoheader( msg )
        self.setStatusAction( msg )
        self.progress.start( T_('Updated %(count)d') )

        yield self.switchToBackground
        try:
            svn_project = tree_node.project
            filename = tree_node.relativePath()

            svn_project.initNotificationOfFilesInConflictCount()

            rev_list = svn_project.cmdUpdate(
                                filename,
                                svn_project.svn_rev_head,
                                svn_project.svn_depth_infinity )
            yield self.switchToForeground
            self.__updateToRevisionProcessResults( tree_node, rev_list )

        except pysvn.ClientError as e:
            svn_project.logClientError( e )

            yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()

        yield from self.main_window.updateTableView_Bg()

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
    def enablerTableSvnResolveConflict( self ):
        tree_node = self.selectedSvnProjectTreeNode()
        if tree_node is None:
            return False

        tree_node.relativePath()

        if not tree_node.project.hasFileState( tree_node.relativePath() ):
            return False

        file_state = tree_node.project.getFileState( tree_node.relativePath() )
        return file_state.isConflicted()

    def enablerTableSvnDiffBaseVsWorking( self ):
        if not self.main_window.isScmTypeActive( 'svn' ):
            return False

        all_file_state = self.tableSelectedAllFileStates()
        if len(all_file_state) == 0:
            return False

        for file_state in all_file_state:
            if not file_state.isModified():
                return False

        return True

    def enablerTableSvnDiffHeadVsWorking( self ):
        if not self.main_window.isScmTypeActive( 'svn' ):
            return False

        return True

    def enablerTableSvnInfo( self ):
        return self._enablerTableSvnIsControlled()

    def enablerTableSvnProperties( self ):
        return self._enablerTableSvnIsControlled()

    def enablerTableSvnAdd( self ):
        # can only add uncontrolled files
        return self.__enablerTableSvnIsUncontrolled()

    def enablerTableSvnRevert( self ):
        # can only revert uncontrolled files
        return self._enablerTableSvnIsControlled()

    def enablerSvnCommitInclude( self ):
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

    @thread_switcher
    def tableActionSvnInfo_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            try:
                info = svn_project.cmdInfo( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

            dialog = wb_svn_info_dialog.InfoDialog( self.app, self.main_window, filename, svn_project.pathForSvn( filename ), info )
            dialog.exec_()

        self._tableActionSvnCmd_Bg( execute_function )

    @thread_switcher
    def tableActionSvnProperties_Bg( self, checked=None ):
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

        yield from self._tableActionSvnCmd_Bg( execute_function )

    @thread_switcher
    def tableActionSvnAdd_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            svn_project.cmdAdd( filename )

        yield from self._tableActionSvnCmd_Bg( execute_function )

    @thread_switcher
    def tableActionSvnRevert_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            try:
                svn_project.cmdRevert( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

        yield from self._tableActionSvnCmd_Bg( execute_function, are_you_sure )

    @thread_switcher
    def tableActionSvnResolveConflict_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            try:
                svn_project.cmdResolved( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureResolveConflict( self.main_window, all_filenames )

        yield from self._tableActionSvnCmd_Bg( execute_function, are_you_sure )

    @thread_switcher
    def tableActionSvnDelete_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            file_state = svn_project.getFileState( filename )

            if file_state.isControlled():
                try:
                    svn_project.cmdDelete( filename )

                except wb_svn_project.ClientError as e:
                    svn_project.logClientError( e )
                    return
            else:
                try:
                    file_state.absolutePath().unlink()

                except IOError as e:
                    self.log.error( 'Error deleting %s' % (filename,) )
                    self.log.error( str(e) )


        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureDelete( self.main_window, all_filenames )

        yield from self._tableActionSvnCmd_Bg( execute_function, are_you_sure )

    @thread_switcher
    def tableActionSvnRename_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            rename = wb_common_dialogs.WbRenameFilenameDialog( self.app, self.main_window )
            rename.setName( filename.name )

            if rename.exec_():
                try:
                    # handles rename for controlled and uncontrolled files
                    svn_project.cmdRename( filename, filename.with_name( rename.getName() ) )

                except wb_svn_project.ClientError as e:
                    svn_project.logClientError( e )

        yield from self._tableActionSvnCmd_Bg( execute_function )

    @thread_switcher
    def _tableActionSvnCmd_Bg( self, execute_function, are_you_sure_function=None ):
        svn_project = self.selectedSvnProject()
        if svn_project is None:
            return

        try:
            @thread_switcher
            def finalise_Bg( svn_project ):
                # take account of the change
                yield from self.top_window.updateTableView()

            self.table_view.tableActionViewRepo( execute_function, are_you_sure_function, finalise_Bg )

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e )

        yield from self.main_window.updateTableView_Bg()

    # ------------------------------------------------------------
    def selectedSvnProjectTreeNode( self ):
        if not self.main_window.isScmTypeActive( 'svn' ):
            return None

        tree_node = self.table_view.table_model.selectedScmProjectTreeNode()

        # if the place holder is being used return none
        if not isinstance( tree_node, wb_svn_project.SvnProjectTreeNode ):
            return None

        return tree_node

    def enablerTableSvnAnnotate( self ):
        return self._enablerTableSvnIsControlled()

    @thread_switcher
    def tableActionSvnAnnotate_Bg( self, checked=None ):
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
        commit_dialog.commitAccepted.connect( self.__commitAccepted )
        commit_dialog.commitClosed.connect( self.__commitClosed )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        self.app.wrapWithThreadSwitcher( self.__commitAccepted_Bg )()

    @thread_switcher
    def __commitAccepted_Bg( self ):
        print( 'qqq svn __commitAccepted_Bg' )
        svn_project = self.selectedSvnProject()

        commit_dialog = self.app.getSingleton( self.commit_key )

        message = commit_dialog.getMessage()
        all_commit_files = commit_dialog.getAllCommitIncludedFiles()

        # hide the dialog
        commit_dialog.hide()

        msg = T_('Check in %s') % (svn_project.projectName(),)
        self.log.infoheader( msg )
        self.setStatusAction( msg )
        self.progress.start( T_('Sent %(count)d'), 0 )

        yield self.switchToBackground

        try:
            commit_id = svn_project.cmdCommit( message, all_commit_files )

            headline = message.split('\n')[0]
            self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') %
                    {'headline': headline, 'commit_id': commit_id} )

        except wb_svn_project.ClientError as e:
            svn_project.logClientError( e, 'Cannot Check in %s' % (svn_project.projectName(),) )

        yield self.switchToForeground

        self.setStatusAction( T_('Ready') )
        self.progress.end()

        # close with cause the commitClosed signal to be emitted
        commit_dialog.close()

    def __commitClosed( self ):
        print( 'qqq svn __commitClosed' )
        self.app.wrapWithThreadSwitcher( self.__svn_commitClosed_Bg )()

    @thread_switcher
    def __svn_commitClosed_Bg( self ):
        print( 'qqq svn __svn_commitClosed_Bg' )
        commit_dialog = self.app.popSingleton( self.commit_key )

        # take account of any changes
        yield from self.main_window.updateTableView_Bg()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

        del commit_dialog

    #============================================================
    #
    # actions for commit dialog
    #
    #============================================================
    @thread_switcher
    def tableActionSvnAddAndInclude_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            svn_project.cmdAdd( filename )
            self.main_window.addCommitIncludedFile( filename )

        yield from self._tableActionSvnCmd_Bg( execute_function )

    @thread_switcher
    def tableActionSvnRevertAndExclude_Bg( self, checked=None ):
        def execute_function( svn_project, filename ):
            try:
                svn_project.cmdRevert( filename )
                self.main_window.removeCommitIncludedFile( filename )

            except wb_svn_project.ClientError as e:
                svn_project.logClientError( e )
                return

        def are_you_sure( all_filenames ):
            return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

        yield from self._tableActionSvnCmd_Bg( execute_function, are_you_sure )

    @thread_switcher
    def tableActionCommitInclude_Bg( self, checked=None ):
        all_file_states = self.tableSelectedAllFileStates()
        if len(all_file_states) == 0:
            return

        for entry in all_file_states:
            if checked:
                self.main_window.addCommitIncludedFile( entry.relativePath() )

            else:

                self.main_window.removeCommitIncludedFile( entry.relativePath() )

        # take account of the changes
        yield from self.top_window.updateTableView_Bg()

    def checkerActionCommitInclude( self ):
        all_file_states = self.tableSelectedAllFileStates()
        if len(all_file_states) == 0:
            return False

        tv = self.main_window.table_view

        for entry in all_file_states:
            if entry.relativePath() not in self.main_window.all_included_files:
                return False

        return True

    #============================================================
    #
    # actions for log history view
    #
    #============================================================
    def enablerTableSvnDiffLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_commit_selections) in (1,2)

        elif focus == 'changes':
            if len(mw.current_file_selection) == 0:
                return False

            node = mw.changes_model.changesNode( mw.current_file_selection[0] )
            return node.action in 'M'

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def tableActionSvnDiffLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        try:
            if focus == 'commits':
                self.diffLogHistory()

            elif focus == 'changes':
                self.diffFileChanges()

            else:
                assert False, 'focus not as expected: %r' % (focus,)

        except wb_svn_project.ClientError as e:
            mw.svn_project.logClientError( e )

    def enablerTableSvnAnnotateLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_commit_selections) in (1,2)

        else:
            return False

    def diffLogHistory( self ):
        mw = self.main_window

        filestate = mw.svn_project.getFileState( mw.filename )

        if len( mw.current_commit_selections ) == 1:
            # diff working against rev
            rev_new = mw.svn_project.svn_rev_working
            rev_old = mw.log_model.revForRow( mw.current_commit_selections[0] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )

            title_vars = {'rev_old': rev_old.number
                         ,'date_old': date_old}

            heading_new = T_('Working')
            heading_old = T_('r%(rev_old)d date %(date_old)s') % title_vars

        else:
            rev_new = mw.log_model.revForRow( mw.current_commit_selections[0] )
            date_new = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )
            rev_old = mw.log_model.revForRow( mw.current_commit_selections[-1] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[-1] )

            title_vars = {'rev_old': rev_old.number
                         ,'date_old': date_old
                         ,'rev_new': rev_new.number
                         ,'date_new': date_new}


            heading_new = T_('r%(rev_new)d date %(date_new)s') % title_vars
            heading_old = T_('r%(rev_old)d date %(date_old)s') % title_vars

        if filestate.isDir():
            title = T_('Diff %s') % (mw.filename,)
            text = mw.svn_project.cmdDiffRevisionVsRevision( mw.filename, rev_old, rev_new )
            self.showDiffText( title, text.split('\n') )

        else:
            title = T_('Diff %s') % (mw.filename,)
            if rev_new == mw.svn_project.svn_rev_working:
                text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForRevision( rev_new )

            text_old = filestate.getTextLinesForRevision( rev_old )

            self.diffTwoFiles(
                    title,
                    text_old,
                    text_new,
                    heading_old,
                    heading_new
                    )

    def diffFileChanges( self ):
        mw = self.main_window

        node = mw.changes_model.changesNode( mw.current_file_selection[0] )
        filename = node.path

        rev_new = mw.log_model.revForRow( mw.current_commit_selections[0] ).number
        rev_old = rev_new - 1

        heading_new = 'r%d' % (rev_new,)
        heading_old = 'r%d' % (rev_old,)

        title = T_('Diff %s') % (filename,)


        info = mw.svn_project.cmdInfo( pathlib.Path('.') )

        url = info[ 'repos_root_URL' ] + filename

        text_new = mw.svn_project.getTextLinesForRevisionFromUrl( url, rev_new )
        text_old = mw.svn_project.getTextLinesForRevisionFromUrl( url, rev_old )

        self.diffTwoFiles(
                title,
                text_old,
                text_new,
                heading_old,
                heading_new
                )

    def tableActionSvnAnnotateLogHistory( self ):
        self.log.error( 'annotateLogHistory TBD' )
