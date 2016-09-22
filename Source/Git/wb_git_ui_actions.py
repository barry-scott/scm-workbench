'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_components.py.py

'''
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_ui_components
import wb_common_dialogs

import wb_git_project
import wb_git_status_view

from wb_background_thread import thread_switcher

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the commit window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class GitMainWindowActions(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__( 'git' )

    def setupDebug( self ):
        self._debug = self.main_window.app._debugGitUi

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerGitFilesStage( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canStage )

    def enablerGitFilesUnstage( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canUnstage )

    def enablerGitFilesRevert( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canRevert )

    def __enablerGitFiles( self, predicate ):
        if not self.main_window.isScmTypeActive( 'git' ):
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

    def enablerGitDiffHeadVsWorking( self ):
        return self.__enablerDiff( wb_git_project.WbGitFileState.canDiffHeadVsWorking )

    def enablerGitDiffStagedVsWorking( self ):
        return self.__enablerDiff( wb_git_project.WbGitFileState.canDiffStagedVsWorking )

    def enablerGitDiffHeadVsStaged( self ):
        return self.__enablerDiff( wb_git_project.WbGitFileState.canDiffHeadVsStaged )

    def __enablerDiff( self, predicate ):
        if not self.main_window.isScmTypeActive( 'git' ):
            return False

        focus = self.main_window.scmFocusWidget()
        if focus == 'tree':
            git_project = self.selectedGitProject()
            if git_project is None:
                return False

            return git_project.hasCommits()

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

    def enablerGitDiffSmart( self ):
        if not self.main_window.isScmTypeActive( 'git' ):
            return False

        focus = self.main_window.scmFocusWidget()

        if focus == 'tree':
            git_project = self.selectedGitProject()
            if git_project is None:
                return False

            return git_project.hasCommits()

        elif focus == 'table':
            # make sure all the selected entries is modified
            all_file_states = self.tableSelectedAllFileStates()
            enable = True
            for obj in all_file_states:
                if not (obj.canDiffStagedVsWorking()
                        or obj.canDiffHeadVsWorking()
                        or obj.canDiffHeadVsStaged()):
                    enable = False
                    break

            return enable

        else:
            return False

    def enablerGitCommit( self ):
        # enable if any files staged
        git_project = self.selectedGitProject()
        if git_project is None:
            return False

        # allow the commit dialog to appear
        # if there are staged files or modified files
        # which can be staged using the commit dialog
        if( git_project.numStagedFiles() == 0
        and git_project.numModifiedFiles() == 0 ):
            return False

        return True

    def treeActionGitDebug1( self ):
        self.log.error( '  enablerGitCommit -> %r' % (self.enablerGitCommit(),) )
        git_project = self.selectedGitProject()
        self.log.error( '       git_project -> %r' % (git_project,) )

        if git_project is None:
            return

        self.log.error( '     commit_dialog -> %r' % (self.app.hasSingleton( self.commit_key ),) )
        self.log.error( '    numStagedFiles -> %r' % (git_project.numStagedFiles(),) )
        self.log.error( '  numModifiedFiles -> %r' % (git_project.numModifiedFiles(),) )

    def enablerGitPush( self ):
        git_project = self.selectedGitProject()
        return git_project is not None and git_project.canPush()

    def enablerGitLogHistory( self ):
        return True

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def treeTableActionGitDiffSmart( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionGitDiffSmart, self.tableActionGitDiffSmart )

    def treeTableActionGitDiffStagedVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionGitDiffStagedVsWorking, self.tableActionGitDiffStagedVsWorking )

    def treeTableActionGitDiffHeadVsStaged( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionGitDiffHeadVsStaged, self.tableActionGitDiffHeadVsStaged )

    def treeTableActionGitDiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionGitDiffHeadVsWorking, self.tableActionGitDiffHeadVsWorking )

    @thread_switcher
    def treeTableActionGitLogHistory_Bg( self, checked ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionGitLogHistory_Bg, self.tableActionGitLogHistory_Bg )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def selectedGitProject( self ):
        scm_project = self.table_view.selectedScmProject()
        if scm_project is None:
            return None

        if not isinstance( scm_project, wb_git_project.GitProject ):
            return None

        return scm_project

    def treeActionGitDiffSmart( self ):
        self._debug( 'treeActionGitDiffSmart()' )

    def treeActionGitDiffStagedVsWorking( self ):
        tree_node = self.selectedGitProjectTreeNode()
        if tree_node is None:
            return

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=False, staged=False )
        self.showDiffText( T_('Diff Staged vs. Working for %s') %
                                        (tree_node.relativePath(),), diff_text.split('\n') )

    def treeActionGitDiffHeadVsStaged( self ):
        tree_node = self.selectedGitProjectTreeNode()
        if tree_node is None:
            return

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=True, staged=True )
        self.showDiffText( T_('Diff Head vs. Staged for %s') %
                                        (tree_node.relativePath(),), diff_text.split('\n') )

    def treeActionGitDiffHeadVsWorking( self ):
        tree_node = self.selectedGitProjectTreeNode()
        if tree_node is None:
            return

        diff_text = tree_node.project.cmdDiffFolder( tree_node.relativePath(), head=True, staged=False )
        self.showDiffText( T_('Diff Head vs. Working for %s') %
                                        (tree_node.relativePath(),), diff_text.split('\n') )

    def __logGitCommandError( self, e ):
        self.log.error( "'%s' returned with exit code %i" %
                        (' '.join(str(i) for i in e.command), e.status) )
        if e.stderr:
            all_lines = e.stderr.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionGitPush_Bg( self, checked ):
        git_project = self.selectedGitProject().newInstance()
        self.setStatusAction( T_('Push %s') % (git_project.projectName(),) )

        yield self.switchToBackground

        try:
            git_project.cmdPush(
                self.deferRunInForeground( self.pushProgressHandler ),
                self.deferRunInForeground( self.pushInfoHandler ) )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

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
    @thread_switcher
    def treeActionGitPull_Bg( self, checked ):
        git_project = self.selectedGitProject().newInstance()
        self.setStatusAction( T_('Pull %s') % (git_project.projectName(),) )

        yield self.switchToBackground

        try:
            git_project.cmdPull(
                self.deferRunInForeground( self.pullProgressHandler ),
                self.deferRunInForeground( self.pullInfoHandler ) )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

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
            status = '%s %s' % (status, message)

        self.progress.start( status )
        if is_end:
            self.log.info( status )

    def treeActionGitStatus( self ):
        git_project = self.selectedGitProject()

        commit_status_view = wb_git_status_view.WbGitStatusView(
                self.app,
                T_('Status for %s') % (git_project.projectName(),) )
        commit_status_view.setStatus(
                    git_project.getUnpushedCommits(),
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )
        commit_status_view.show()

    # ------------------------------------------------------------
    def tableActionGitStage( self ):
        self.__tableActionChangeRepo( self.__actionGitStage )

    def tableActionGitUnstage( self ):
        self.__tableActionChangeRepo( self.__actionGitUnStage )

    def tableActionGitRevert( self ):
        self.__tableActionChangeRepo( self.__actionGitRevert, self.__areYouSureRevert )

    def tableActionGitDelete( self ):
        self.__tableActionChangeRepo( self.__actionGitDelete, self.__areYouSureDelete )

    def tableActionGitRename( self ):
        self.__tableActionChangeRepo( self.__actionGitRename )

    def tableActionGitDiffSmart( self ):
        self._debug( 'tableActionGitDiffSmart()' )
        self.table_view.tableActionViewRepo( self.__actionGitDiffSmart )

    def tableActionGitDiffStagedVsWorking( self ):
        self._debug( 'tableActionGitDiffStagedVsWorking()' )
        self.table_view.tableActionViewRepo( self.__actionGitDiffStagedVsWorking )

    def tableActionGitDiffHeadVsStaged( self ):
        self._debug( 'tableActionGitDiffHeadVsStaged()' )
        self.table_view.tableActionViewRepo( self.__actionGitDiffHeadVsStaged )

    def tableActionGitDiffHeadVsWorking( self ):
        self._debug( 'tableActionGitDiffHeadVsWorking()' )
        self.table_view.tableActionViewRepo( self.__actionGitDiffHeadVsWorking )

    @thread_switcher
    def tableActionGitLogHistory_Bg( self ):
        yield from self.table_view.tableActionViewRepo_Bg( self._actionGitLogHistory_Bg )

    def __actionGitStage( self, git_project, filename ):
        git_project.cmdStage( filename )

    def __actionGitUnStage( self, git_project, filename ):
        git_project.cmdUnstage( 'HEAD', filename )

    def __actionGitRevert( self, git_project, filename ):
        git_project.cmdRevert( 'HEAD', filename )

    def __actionGitDelete( self, git_project, filename ):
        git_project.cmdDelete( filename )

    def __actionGitRename( self, git_project, filename ):
        filestate = git_project.getFileState( filename )

        rename = wb_common_dialogs.WbRenameFilenameDialog( self.app, self.main_window )
        rename.setName( filename.name )

        if rename.exec_():
            # handles rename for controlled and uncontrolled files
            git_project.cmdRename( filename, filename.with_name( rename.getName() ) )

    def __actionGitDiffSmart( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        if file_state.canDiffStagedVsWorking():
            self.__actionGitDiffStagedVsWorking( git_project, filename )

        elif file_state.canDiffHeadVsStaged():
            self.__actionGitDiffHeadVsStaged( git_project, filename )

        elif file_state.canDiffHeadVsWorking():
            self.__actionGitDiffHeadVsWorking( git_project, filename )

    def __actionGitDiffHeadVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff HEAD vs. Work %s') % (filename,),
                file_state.getTextLinesHead(),
                file_state.getTextLinesWorking(),
                T_('HEAD %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def __actionGitDiffStagedVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff Staged vs. Work %s') % (filename,),
                file_state.getTextLinesStaged(),
                file_state.getTextLinesWorking(),
                T_('Staged %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def __actionGitDiffHeadVsStaged( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff HEAD vs. Staged %s') % (filename,),
                file_state.getTextLinesHead(),
                file_state.getTextLinesStaged(),
                T_('HEAD %s') % (filename,),
                T_('Staged %s') % (filename,)
                )

    #------------------------------------------------------------
    def __areYouSureRevert( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

    def __areYouSureDelete( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureDelete( self.main_window, all_filenames )

    def __tableActionChangeRepo( self, execute_function, are_you_sure_function=None ):
        def finalise( git_project ):
            git_project.saveChanges()

            # take account of the change
            self.top_window.updateTableView()

        self.table_view.tableActionViewRepo( execute_function, are_you_sure_function, finalise )

    # ------------------------------------------------------------
    def selectedGitProjectTreeNode( self ):
        if not self.isScmTypeActive():
            return None

        tree_node = self.main_window.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_git_project.GitProjectTreeNode )
        return tree_node
