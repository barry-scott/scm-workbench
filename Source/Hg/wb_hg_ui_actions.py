'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_ui_components.py.py

'''
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_ui_components

import wb_hg_project
import wb_hg_status_view

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the commit window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class HgMainWindowActions(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__( 'hg' )

    def setupDebug( self ):
        self._debug = self.main_window.app._debugHgUi

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerHgFilesAdd( self ):
        return self.__enablerHgFiles( wb_hg_project.WbHgFileState.canAdd )

    def enablerHgFilesRevert( self ):
        return self.__enablerHgFiles( wb_hg_project.WbHgFileState.canRevert )

    def __enablerHgFiles( self, predicate ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return False

        focus = self.main_window.scmFocusWidget()

        if focus == 'tree':
            return True

        elif focus == 'table':
            all_file_states = self.tableSelectedAllFileStates()
            if len(all_file_states) == 0:
                return False

            for obj in all_file_states:
                if not predicate( obj ):
                    return False

            return True

        else:
            return False

    def enablerHgDiffHeadVsWorking( self ):
        return self.__enablerDiff( wb_hg_project.WbHgFileState.canDiffHeadVsWorking )

    def __enablerDiff( self, predicate ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return False

        focus = self.main_window.scmFocusWidget()
        if focus == 'tree':
            return True

        elif focus == 'table':
            # make sure all the selected entries is modified
            all_file_states = self.tableSelectedAllFileStates()
            enable = True
            for obj in all_file_states:
                if not predicate( obj ):
                    enable = False
                    break

            return enable

        else:
            return False

    def enablerHgDiffSmart( self ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return False

        focus = self.main_window.scmFocusWidget()

        if focus == 'tree':
            return True

        elif focus == 'table':
            # make sure all the selected entries is modified
            all_file_states = self.tableSelectedAllFileStates()
            enable = True
            for obj in all_file_states:
                if not obj.canDiffHeadVsWorking():
                    enable = False
                    break

            return enable

        else:
            return False

    def enablerHgCommit( self ):
        # enable if any files modified
        hg_project = self.selectedHgProject()

        can_commit = False
        if hg_project is None:
            return False

        if self.app.hasSingleton( self.commit_key ):
            return False

        # allow the commit dialog to appear
        # if there are modified files
        # which can be added using the commit dialog
        if hg_project.numModifiedFiles() == 0:
            return False

        return True

    def treeActionHgDebug1( self ):
        self.log.error( '  enablerHgCommit -> %r' % (self.enablerHgCommit(),) )
        hg_project = self.selectedHgProject()
        self.log.error( '       hg_project -> %r' % (hg_project,) )
        if hg_project is None:
            return

        self.log.error( '     commit_dialog -> %r' % (self.app.hasSingleton( self.commit_key ),) )
        self.log.error( '  numModifiedFiles -> %r' % (hg_project.numModifiedFiles(),) )

    def enablerHgPush( self ):
        hg_project = self.selectedHgProject()
        return hg_project is not None and hg_project.canPush()

    def enablerHgLogHistory( self ):
        return True

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def treeTableActionHgDiffSmart( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionHgDiffSmart, self.tableActionHgDiffSmart )

    def treeTableActionHgDiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionHgDiffHeadVsWorking, self.tableActionHgDiffHeadVsWorking )

    def treeTableActionHgLogHistory( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionHgLogHistory, self.tableActionHgLogHistory )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def selectedHgProject( self ):
        scm_project = self.table_view.selectedScmProject()
        if scm_project is None:
            return None

        if not isinstance( scm_project, wb_hg_project.HgProject ):
            return None

        return scm_project

    def treeActionHgDiffSmart( self ):
        self._debug( 'treeActionHgDiffSmart()' )

    def treeActionHgDiffHeadVsWorking( self ):
        tree_node = self.selectedHgProjectTreeNode()
        if tree_node is None:
            return

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath() )
        self.showDiffText( T_('Diff Head vs. Working for %s') %
                                        (tree_node.relativePath(),), diff_text.split('\n') )

    def __logHgCommandError( self, e ):
        self.log.error( "'%s' returned with exit code %i" %
                        (' '.join(str(i) for i in e.command), e.status) )
        if e.stderr:
            all_lines = e.stderr.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    def treeActionHgPush_Bg( self, checked ):
        hg_project = self.selectedHgProject().newInstance()
        self.setStatusAction( T_('Push %s') % (hg_project.projectName(),) )

        yield self.switchToBackground

        try:
            hg_project.cmdPush(
                self.deferRunInForeground( self.pushProgressHandler ),
                self.deferRunInForeground( self.pushInfoHandler ) )

        except wb_hg_project.HgCommandError as e:
            self.__logHgCommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()

        self.main_window.updateActionEnabledStates()

    def pushInfoHandler( self, info ):
        self.log.info( 'Push summary: %s' % (info.summary,) )

    def pushProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Push %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Push %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Push %s' % (stage_name,)

        if message != '':
            self.log.info( message )

        self.progress.start( status )
        if is_end:
            self.log.info( status )

    # ------------------------------------------------------------
    def treeActionHgPull_Bg( self, checked ):
        hg_project = self.selectedHgProject().newInstance()
        self.setStatusAction( T_('Pull %s') % (hg_project.projectName(),) )

        yield self.switchToBackground

        try:
            hg_project.cmdPull(
                self.deferRunInForeground( self.pullProgressHandler ),
                self.deferRunInForeground( self.pullInfoHandler ) )

        except wb_hg_project.HgCommandError as e:
            self.__logHgCommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()
        self.main_window.updateActionEnabledStates()

    def pullInfoHandler( self, info ):
        if info.note != '':
            self.log.info( 'Pull Note: %s' % (info.note,) )

        for state, state_name in (
                    (info.NEW_TAG, T_('New tag')),
                    (info.NEW_HEAD, T_('New head')),
                    (info.HEAD_UPTODATE, T_('Head up to date')),
                    (info.TAG_UPDATE, T_('Tag update')),
                    (info.FORCED_UPDATE, T_('Forced update')),
                    (info.FAST_FORWARD, T_('Fast forward')),
                    ):
            if (info.flags&state) != 0:
                self.log.info( T_('Pull status: %(state_name)s for %(name)s') % {'state_name': state_name, 'name': info.name} )

        for state, state_name in (
                    (info.REJECTED, T_('Rejected')),
                    (info.ERROR, T_('Error'))
                    ):
            if (info.flags&state) != 0:
                self.log.error( T_('Pull status: %(state_name)s') % {'state_name': state_name} )

    def pullProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count=None, message='' ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Pull %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Pull %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Pull %s' % (stage_name,)

        if message != '':
            self.log.info( message )

        self.progress.start( status )
        if is_end:
            self.log.info( status )

    def treeActionHgStatus( self ):
        hg_project = self.selectedHgProject()

        commit_status_view = wb_hg_status_view.WbHgStatusView(
                self.app,
                T_('Status for %s') % (hg_project.projectName(),),
                self.main_window.getQIcon( 'wb.png' ) )
        commit_status_view.setStatus(
                    hg_project.getUnpushedCommits(),
                    hg_project.getReportModifiedFiles(),
                    hg_project.getReportUntrackedFiles() )
        commit_status_view.show()

    # ------------------------------------------------------------
    def tableActionHgAdd( self ):
        self.__tableActionChangeRepo( self.__actionHgAdd )

    def tableActionHgRevert( self ):
        self.__tableActionChangeRepo( self.__actionHgRevert, self.__areYouSureRevert )

    def tableActionHgDelete( self ):
        self.__tableActionChangeRepo( self.__actionHgDelete, self.__areYouSureDelete )

    def tableActionHgDiffSmart( self ):
        self._debug( 'tableActionHgDiffSmart()' )
        self.table_view.tableActionViewRepo( self.__actionHgDiffSmart )

    def tableActionHgDiffHeadVsWorking( self ):
        self._debug( 'tableActionHgDiffHeadVsWorking()' )
        self.table_view.tableActionViewRepo( self.__actionHgDiffHeadVsWorking )

    def tableActionHgLogHistory( self ):
        self.table_view.tableActionViewRepo( self._actionHgLogHistory )

    def __actionHgAdd( self, hg_project, filename ):
        hg_project.cmdAdd( filename )

    def __actionHgRevert( self, hg_project, filename ):
        hg_project.cmdRevert( 'HEAD', filename )

    def __actionHgDelete( self, hg_project, filename ):
        hg_project.cmdDelete( filename )

    def __actionHgDiffSmart( self, hg_project, filename ):
        file_state = hg_project.getFileState( filename )

        if file_state.canDiffHeadVsWorking():
            self.__actionHgDiffHeadVsWorking( hg_project, filename )

    def __actionHgDiffHeadVsWorking( self, hg_project, filename ):
        file_state = hg_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff HEAD vs. Work %s') % (filename,),
                file_state.getTextLinesHead(),
                file_state.getTextLinesWorking(),
                T_('HEAD %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    #------------------------------------------------------------
    def __areYouSureRevert( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

    def __areYouSureDelete( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureDelete( self.main_window, all_filenames )

    def __tableActionChangeRepo( self, execute_function, are_you_sure_function=None ):
        def finalise( hg_project ):
            # take account of the change
            self.top_window.updateTableView()

        self.table_view.tableActionViewRepo( execute_function, are_you_sure_function, finalise )

    # ------------------------------------------------------------
    def selectedHgProjectTreeNode( self ):
        if not self.isScmTypeActive():
            return None

        tree_node = self.main_window.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_hg_project.HgProjectTreeNode )
        return tree_node
