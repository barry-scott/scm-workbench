'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_actions.py.py

'''
import sys
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_log_history_options_dialog
import wb_ui_actions
import wb_common_dialogs

import wb_git_project
import wb_git_status_view
import wb_git_commit_dialog
import wb_git_annotate

from wb_background_thread import thread_switcher

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the commit window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class GitMainWindowActions(wb_ui_actions.WbMainWindowActions):
    def __init__( self, factory ):
        super().__init__( 'git', factory )

    def setupDebug( self ):
        self._debug = self.main_window.app._debug_options._debugGitUi

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerGitCommitInclude( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canCommit )

    def enablerGitFilesStage( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canStage )

    def enablerGitFilesUnstage( self ):
        return self.__enablerGitFiles( wb_git_project.WbGitFileState.canUnstage )

    def enablerGitFilesRevert( self ):
        rc = self.__enablerGitFiles( wb_git_project.WbGitFileState.canRevert )
        return rc

    def __enablerGitFiles( self, predicate ):
        if not self.main_window.isScmTypeActive( 'git' ):
            return False

        focus = self.main_window.focusIsIn()

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

        focus = self.main_window.focusIsIn()
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

        focus = self.main_window.focusIsIn()

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

    def enablerGitPull( self ):
        git_project = self.selectedGitProject()
        return git_project is not None and git_project.canPull()

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
    def treeTableActionGitLogHistory_Bg( self, checked=None ):
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
            if type( e.stderr ) == bytes:
                all_lines = e.stderr.decode( sys.getdefaultencoding() ).split('\n')
            else:
                all_lines = e.stderr.split('\n')

            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionGitPush_Bg( self, checked=None ):
        git_project = self.selectedGitProject().newInstance()
        self.setStatusAction( T_('Push %s') % (git_project.projectName(),) )

        self.app.log.infoheader( T_('Push %(project_name)s %(branch)s') %
                                {'project_name': git_project.projectName()
                                ,'branch': git_project.getTrackingBranchName()} )

        yield self.switchToBackground

        try:
            for commit in git_project.getUnpushedCommits():
                self.log.info( 'pushing "%s" id %s' % (commit.message.split('\n')[0], commit.hexsha) )

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
    def treeActionGitPull_Bg( self, checked=None ):
        git_project = self.selectedGitProject().newInstance()
        self.setStatusAction( T_('Pull %s') % (git_project.projectName(),) )

        self.app.log.infoheader( T_('Pull %(project_name)s %(branch)s') %
                                {'project_name': git_project.projectName()
                                ,'branch': git_project.getTrackingBranchName()} )

        commit_id = git_project.getHeadCommit().hexsha

        yield self.switchToBackground

        try:
            git_project.cmdPull(
                self.deferRunInForeground( self.pullProgressHandler ),
                self.deferRunInForeground( self.pullInfoHandler ) )

            for commit in git_project.cmdCommitLogAfterCommitId( commit_id ):
                self.log.info( 'pulled "%s" id %s' % (commit.commitMessage().split('\n')[0], commit.commitIdString()) )

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
    @thread_switcher
    def tableActionGitStage_Bg( self, checked=None ):
        self._debug( 'tableActionGitStage_Bg start' )
        yield from self._tableActionChangeRepo_Bg( self._actionGitStage )
        self._debug( 'tableActionGitStage_Bg done' )

    @thread_switcher
    def tableActionGitUnstage_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitUnstage )

    @thread_switcher
    def tableActionGitRevert_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitRevert, self._areYouSureRevert )

    @thread_switcher
    def tableActionGitDelete_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitDelete, self._areYouSureDelete )

    @thread_switcher
    def tableActionGitRename_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitRename )

    def tableActionGitDiffSmart( self ):
        self._debug( 'tableActionGitDiffSmart()' )
        self.table_view.tableActionViewRepo( self._actionGitDiffSmart )

    def tableActionGitDiffStagedVsWorking( self ):
        self._debug( 'tableActionGitDiffStagedVsWorking()' )
        self.table_view.tableActionViewRepo( self._actionGitDiffStagedVsWorking )

    def tableActionGitDiffHeadVsStaged( self ):
        self._debug( 'tableActionGitDiffHeadVsStaged()' )
        self.table_view.tableActionViewRepo( self._actionGitDiffHeadVsStaged )

    def tableActionGitDiffHeadVsWorking( self ):
        self._debug( 'tableActionGitDiffHeadVsWorking()' )
        self.table_view.tableActionViewRepo( self._actionGitDiffHeadVsWorking )

    @thread_switcher
    def tableActionGitLogHistory_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self._actionGitLogHistory_Bg )

    @thread_switcher
    def _actionGitLogHistory_Bg( self, git_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        commit_log_view = self.factory.logHistoryView(
                self.app, T_('Commit Log for %s') % (filename,) )

        yield from commit_log_view.showCommitLogForFile_Bg( git_project, filename, options )

    def _actionGitStage( self, git_project, filename ):
        self._debug( '_actionGitStage( %r, %s )' )
        git_project.cmdStage( filename )

    def _actionGitUnstage( self, git_project, filename ):
        self._debug( '_actionGitUnstage( %r, %s )' )
        git_project.cmdUnstage( 'HEAD', filename )

    def _actionGitRevert( self, git_project, filename ):
        file_state = git_project.getFileState( filename )
        if( file_state.isStagedModified()
        and (file_state.isUnstagedModified()
            or file_state.isUnstagedDeleted()) ):
            # revert to staged (--)
            git_project.cmdRevert( '--', filename )

        else:
            # revert to HEAD
            git_project.cmdRevert( 'HEAD', filename )

    def _actionGitDelete( self, git_project, filename ):
        file_state = git_project.getFileState( filename )
        if file_state.isControlled():
            git_project.cmdDelete( filename )

        else:
            try:
                file_state.absolutePath().unlink()

            except IOError as e:
                self.log.error( 'Error deleting %s' % (filename,) )
                self.log.error( str(e) )


    def _actionGitRename( self, git_project, filename ):
        filestate = git_project.getFileState( filename )

        rename = wb_common_dialogs.WbRenameFilenameDialog( self.app, self.main_window )
        rename.setName( filename.name )

        if rename.exec_():
            # handles rename for controlled and uncontrolled files
            git_project.cmdRename( filename, filename.with_name( rename.getName() ) )

    def _actionGitDiffSmart( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        if file_state.canDiffStagedVsWorking():
            self._actionGitDiffStagedVsWorking( git_project, filename )

        elif file_state.canDiffHeadVsStaged():
            self._actionGitDiffHeadVsStaged( git_project, filename )

        elif file_state.canDiffHeadVsWorking():
            self._actionGitDiffHeadVsWorking( git_project, filename )

    def _actionGitDiffHeadVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff HEAD vs. Work %s') % (filename,),
                file_state.getTextLinesHead(),
                file_state.getTextLinesWorking(),
                T_('HEAD %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def _actionGitDiffStagedVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff Staged vs. Work %s') % (filename,),
                file_state.getTextLinesStaged(),
                file_state.getTextLinesWorking(),
                T_('Staged %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def _actionGitDiffHeadVsStaged( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.diffTwoFiles(
                T_('Diff HEAD vs. Staged %s') % (filename,),
                file_state.getTextLinesHead(),
                file_state.getTextLinesStaged(),
                T_('HEAD %s') % (filename,),
                T_('Staged %s') % (filename,)
                )

    #------------------------------------------------------------
    def _areYouSureRevert( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureRevert( self.main_window, all_filenames )

    def _areYouSureDelete( self, all_filenames ):
        return wb_common_dialogs.WbAreYouSureDelete( self.main_window, all_filenames )

    @thread_switcher
    def _tableActionChangeRepo_Bg( self, execute_function, are_you_sure_function=None ):
        self._debug( '_tableActionChangeRepo_Bg start' )

        yield from self.table_view.tableActionViewRepo_Bg( execute_function, are_you_sure_function, self._tableActionChangeRepo_finalise_Bg )
        self._debug( '_tableActionChangeRepo_Bg done' )

    @thread_switcher
    def _tableActionChangeRepo_finalise_Bg( self, git_project ):
        self._debug( '_tableActionChangeRepo_finalise_Bg' )
        git_project.saveChanges()

        # take account of the change
        yield from self.top_window.updateTableView_Bg()

    # ------------------------------------------------------------
    def selectedGitProjectTreeNode( self ):
        mw = self.main_window

        if not mw.isScmTypeActive( 'git' ):
            return None

        tree_node = mw.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_git_project.GitProjectTreeNode )
        return tree_node

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionGitLogHistory_Bg( self, checked=None ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        git_project = self.selectedGitProject()

        commit_log_view = self.factory.logHistoryView(
                self.app,
                T_('Commit Log for %s') % (git_project.projectName(),) )

        yield from commit_log_view.showCommitLogForRepository_Bg( git_project, options )

    def enablerTableGitAnnotate( self ):
        if not self.main_window.isScmTypeActive( 'git' ):
            return False

        return True

    @thread_switcher
    def tableActionGitAnnotate_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionGitAnnotate_Bg )

    @thread_switcher
    def __actionGitAnnotate_Bg( self, git_project, filename ):
        self.setStatusAction( T_('Annotate %s') % (filename,) )
        self.progress.start( T_('Annotate %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_annotation_nodes = git_project.cmdAnnotationForFile( filename )

        all_annotate_commit_ids = set()
        for node in all_annotation_nodes:
            all_annotate_commit_ids.add( node.log_id )

        yield self.switchToForeground

        self.progress.end()
        self.progress.start( T_('Annotate Commit Logs %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_commit_logs = git_project.cmdCommitLogForAnnotateFile( filename, all_annotate_commit_ids )

        yield self.switchToForeground

        self.setStatusAction()
        self.progress.end()

        annotate_view = wb_git_annotate.WbGitAnnotateView(
                            self.app,
                            T_('Annotation of %s') % (filename,) )
        annotate_view.showAnnotationForFile( all_annotation_nodes, all_commit_logs )
        annotate_view.show()

    commit_key = 'git-commit-dialog'
    def treeActionGitCommit( self ):
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.getSingleton( self.commit_key )
            commit_dialog.raise_()
            return

        git_project = self.selectedGitProject()

        commit_dialog = wb_git_commit_dialog.WbGitCommitDialog( self.app, git_project )
        commit_dialog.commitAccepted.connect( self.__commitAccepted )
        commit_dialog.commitClosed.connect( self.app.wrapWithThreadSwitcher( self.__commitClosed_Bg ) )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        commit_dialog = self.app.getSingleton( self.commit_key )

        git_project = commit_dialog.getGitProject()
        message = commit_dialog.getMessage()
        all_commit_files = commit_dialog.getAllCommitIncludedFiles()
        # qqq TODO: cmdCommit does not support all_commit_files yet
        commit_id = git_project.cmdCommit( message )

        headline = message.split('\n')[0]
        self.log.infoheader( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        # close with cause the commitClosed signal to be emitted
        commit_dialog.close()

    @thread_switcher
    def __commitClosed_Bg( self ):
        self.app.popSingleton( self.commit_key )

    #============================================================
    #
    # actions for commit dialog
    #
    #============================================================
    @thread_switcher
    def tableActionGitStageAndInclude_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitStageAndInclude )

    def _actionGitStageAndInclude( self, git_project, filename ):
        self._actionGitStage( git_project, filename )
        self.main_window.all_included_files.add( filename )

    @thread_switcher
    def tableActionGitUnstageAndExclude_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitUnstageAndExclude )

    def _actionGitUnstageAndExclude( self, git_project, filename ):
        self._actionGitUnstage( git_project, filename )
        self.main_window.all_included_files.discard( filename )

    @thread_switcher
    def tableActionGitRevertAndExclude_Bg( self, checked=None ):
        yield from self._tableActionChangeRepo_Bg( self._actionGitRevertAndExclude, self._areYouSureRevert )

    def _actionGitRevertAndExclude( self, git_project, filename ):
        self._actionGitRevert( git_project, filename )

        if not git_project.getFileState( filename ).canCommit():
            self.main_window.all_included_files.discard( filename )

    @thread_switcher
    def tableActionCommitInclude_Bg( self, checked ):
        all_file_states = self.tableSelectedAllFileStates()
        if len(all_file_states) == 0:
            return

        for entry in all_file_states:
            if checked:
                self.main_window.all_included_files.add( entry.relativePath() )

            else:
                self.main_window.all_included_files.discard( entry.relativePath() )

        # take account of the changes
        self.top_window.updateTableView_Bg()

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
    def tableActionGitAnnotateLogHistory( self ):
        self.main_window.annotateLogHistory()

    #------------------------------------------------------------
    def enablerTableGitDiffLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_commit_selections) in (1,2)

        elif focus == 'changes':
            if len(mw.current_file_selection) == 0:
                return False

            type_, filename, old_filename = mw.changes_model.changesNode( mw.current_file_selection[0] )
            return type_ in 'M'

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def tableActionGitDiffLogHistory( self ):
        focus = self.main_window.focusIsIn()
        if focus == 'commits':
            self.diffLogHistory()

        elif focus == 'changes':
            self.diffFileChanges()

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def enablerTableGitAnnotateLogHistory( self ):
        focus = self.main_window.focusIsIn()
        if focus == 'commits':
            return len(self.main_window.current_commit_selections) in (1,2)

        else:
            return False

    def diffLogHistory( self ):
        mw = self.main_window

        #
        #   Figure out the refs for the diff and set up title and headings
        #
        if len( mw.current_commit_selections ) == 1:
            # diff working against rev
            commit_new = None
            commit_old = mw.log_model.commitForRow( mw.current_commit_selections[0] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )

            title_vars = {'commit_old': commit_old
                         ,'date_old': date_old}

            if mw.filename is not None:
                filestate = mw.git_project.getFileState( mw.filename )

                if filestate.isStagedModified():
                    heading_new = 'Staged'

                elif filestate.isUnstagedModified():
                    heading_new = 'Working'

                else:
                    heading_new = 'HEAD'

            else: # Repository
                heading_new = 'Working'

        else:
            commit_new = mw.log_model.commitForRow( mw.current_commit_selections[0] )
            date_new = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )
            commit_old = mw.log_model.commitForRow( mw.current_commit_selections[-1] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[-1] )

            title_vars = {'commit_old': commit_old
                         ,'date_old': date_old
                         ,'commit_new': commit_new
                         ,'date_new': date_new}

            heading_new = T_('commit %(commit_new)s date %(date_new)s') % title_vars

        if mw.filename is not None:
            title = T_('Diff File %s') % (mw.filename,)

        else:
            title = T_('Diff Project %s' % (mw.git_project.projectName(),) )

        heading_old = T_('commit %(commit_old)s date %(date_old)s') % title_vars

        #
        #   figure out the text to diff
        #
        if mw.filename is not None:
            filestate = mw.git_project.getFileState( mw.filename )

            if commit_new is None:
                if filestate.isStagedModified():
                    text_new = filestate.getTextLinesStaged()

                else:
                    # either we want HEAD or the modified working
                    text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForCommit( commit_new )

            text_old = filestate.getTextLinesForCommit( commit_old )

            self.diffTwoFiles(
                    title,
                    text_old,
                    text_new,
                    heading_old,
                    heading_new
                    )

        else: # folder
            if commit_new is None:
                text = mw.git_project.cmdDiffWorkingVsCommit( pathlib.Path('.'), commit_old )
                self.showDiffText( title, text.split('\n') )

            else:
                text = mw.git_project.cmdDiffCommitVsCommit( pathlib.Path('.'), commit_old, commit_new )
                self.showDiffText( title, text.split('\n') )

    def diffFileChanges( self ):
        mw = self.main_window

        type_, filename, old_filename = mw.changes_model.changesNode( mw.current_file_selection[0] )

        commit_new = mw.log_model.commitForRow( mw.current_commit_selections[0] )
        date_new = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )
        commit_old = '%s^1' % (commit_new,)

        title_vars = {'commit_old': commit_old
                     ,'commit_new': commit_new
                     ,'date_new': date_new}

        heading_new = T_('commit %(commit_new)s date %(date_new)s') % title_vars
        heading_old = T_('commit %(commit_old)s') % title_vars

        title = T_('Diff %s') % (filename,)

        filepath = pathlib.Path( filename )

        text_new = mw.git_project.getTextLinesForCommit( filepath, commit_new )
        text_old = mw.git_project.getTextLinesForCommit( filepath, commit_old )

        self.diffTwoFiles(
                title,
                text_old,
                text_new,
                heading_old,
                heading_new
                )

    def annotateLogHistory( self ):
        self.log.error( 'annotateLogHistory TBD' )

