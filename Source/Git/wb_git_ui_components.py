'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_ui_components.py.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import difflib

import wb_diff_unified_view
import wb_diff_side_by_side_view

import wb_ui_components

import wb_git_project
import wb_git_commit_dialog
import wb_git_log_history
import wb_git_status_view

class GitMainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__()

    def setupDebug( self ):
        self._debug = self.main_window.app._debugGitUi

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Git Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m.addSeparator()
        addMenu( m, T_('Status'), self.treeActionGitStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Git Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )

        m.addSeparator()
        addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.main_window.enablerFilesExists )

        m.addSeparator()
        addMenu( m, T_('Commit…'), self.treeActionCommit, self.enablerCommit, 'toolbar_images/commit.png' )

        m.addSeparator()
        addMenu( m, T_('Push…'), self.treeActionPush, self.enablerPush, 'toolbar_images/push.png' )
        addMenu( m, T_('Pull…'), self.treeActionPull, icon_name='toolbar_images/pull.png' )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('git logo'), style='font-size: 20pt; width: 32px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'Git', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('git info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionGitDiffSmart, self.enablerDiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Commit History'), self.treeTableActionGitLogHistory, self.enablerLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('git state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        addTool( t, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        addTool( t, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Commit'), self.treeActionCommit, self.enablerCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        addTool( t, T_('Push'), self.treeActionPush, self.enablerPush, 'toolbar_images/push.png' )
        addTool( t, T_('Pull'), self.treeActionPull, icon_name='toolbar_images/pull.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m.addSection( T_('Git Actions') )
        addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.main_window.enablerFilesExists )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerFilesStage( self, cache ):
        key = 'enablerFilesStage'
        if key not in cache:
            #with_status = (pyscm2.SCM_STATUS_WT_MODIFIED|pyscm2.SCM_STATUS_WT_NEW|pyscm2.SCM_STATUS_WT_DELETED)
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )
            cache[ key ] = True

        return cache[ key ]

    def enablerFilesUnstage( self, cache ):
        key = 'enablerFilesUnstage'
        if key not in cache:
            #with_status = pyscm2.SCM_STATUS_INDEX_MODIFIED|pyscm2.SCM_STATUS_INDEX_NEW|pyscm2.SCM_STATUS_INDEX_DELETED
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )
            cache[ key ] = True

        return cache[ key ]

    def enablerFilesRevert( self, cache ):
        key = 'enablerFilesRevert'
        if key not in cache:
            #with_status = pyscm2.SCM_STATUS_WT_MODIFIED|pyscm2.SCM_STATUS_WT_DELETED
            #without_status = pyscm2.SCM_STATUS_INDEX_MODIFIED
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, without_status )
            cache[ key ] = True

        return cache[ key ]

    def enablerDiffHeadVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsWorking', wb_git_project.WbGitFileState.canDiffHeadVsWorking )

    def enablerDiffStagedVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffStagedVsWorking', wb_git_project.WbGitFileState.canDiffStagedVsWorking )

    def enablerDiffHeadVsStaged( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsStaged', wb_git_project.WbGitFileState.canDiffHeadVsStaged )

    def __enablerDiff( self, cache, key, predicate ):
        if key not in cache:
            focus = self.main_window._enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_file_states = self.main_window._enablerTableSelectedStatus( cache )
                enable = True
                for obj in all_file_states:
                    if not predicate( obj ):
                        enable = False
                        break

                cache[ key ] = enable

            else:
                cache[ key ] = False

        return cache[ key ]

    def enablerDiffSmart( self, cache ):
        key = 'enablerDiffSmart'
        if key not in cache:
            focus = self.main_window._enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_file_states = self.main_window._enablerTableSelectedStatus( cache )
                enable = True
                for obj in all_file_states:
                    if not (obj.canDiffStagedVsWorking()
                            or obj.canDiffHeadVsWorking()
                            or obj.canDiffHeadVsStaged()):
                        enable = False
                        break

                cache[ key ] = enable

            else:
                cache[ key ] = False

        return cache[ key ]

    def enablerCommit( self, cache ):
        key = 'enablerCommit'
        if key not in cache:
            # enable if any files staged
            git_project = self.__treeSelectedGitProject()

            can_commit = False
            if( git_project is not None
            and self.commit_dialog is None
            and git_project.numStagedFiles() > 0 ):
                can_commit = True

            cache[ key ] = can_commit

        return cache[ key ]

    def enablerPush( self, cache ):
        key = 'enablerPush'
        if key not in cache:
            git_project = self.__treeSelectedGitProject()
            cache[ key ] = git_project is not None and git_project.canPush()

        return cache[ key ]

    def enablerLogHistory( self, cache ):
        return True


    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def treeTableActionGitDiffSmart( self ):
        self.main_window._callTreeOrTableFunction( self.treeActionGitDiffSmart, self.tableActionGitDiffSmart )

    def treeTableActionGitDiffStagedVsWorking( self ):
        self.main_window._callTreeOrTableFunction( self.treeActionGitDiffStagedVsWorking, self.tableActionGitDiffStagedVsWorking )

    def treeTableActionGitDiffHeadVsStaged( self ):
        self.main_window._callTreeOrTableFunction( self.treeActionGitDiffHeadVsStaged, self.tableActionGitDiffHeadVsStaged )

    def treeTableActionGitDiffHeadVsWorking( self ):
        self.main_window._callTreeOrTableFunction( self.treeActionGitDiffHeadVsWorking, self.tableActionGitDiffHeadVsWorking )

    def treeTableActionGitLogHistory( self ):
        self.main_window._callTreeOrTableFunction( self.treeActionGitLogHistory, self.tableActionGitLogHistory )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------

    def __treeSelectedGitProject( self ):
        git_project = self.main_window._treeSelectedScmProject()
        if git_project is None:
            return None

        if not isinstance( git_project, wb_git_project.GitProject ):
            return None

        return git_project

    def treeActionGitDiffSmart( self ):
        self._debug( 'treeActionGitDiffSmart()' )

    def treeActionGitDiffStagedVsWorking( self ):
        self._debug( 'treeActionGitDiffStagedVsWorking()' )

    def treeActionGitDiffHeadVsStaged( self ):
        self._debug( 'treeActionGitDiffHeadVsStaged()' )

    def treeActionGitDiffHeadVsWorking( self ):
        self._debug( 'treeActionGitDiffHeadVsWorking()' )

    def treeActionCommit( self ):
        git_project = self.__treeSelectedGitProject()

        self.commit_dialog = wb_git_commit_dialog.WbGitCommitDialog(
                    self.app, self.main_window,
                    T_('Commit %s') % (git_project.projectName(),) )
        self.commit_dialog.setStatus(
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )
        self.commit_dialog.finished.connect( self.__commitDialogFinished )

        # show to the user
        self.commit_dialog.show()

    def __commitDialogFinished( self, result ):
        if result:
            git_project = self.__treeSelectedGitProject()
            message = self.commit_dialog.getMessage()
            commit_id = git_project.cmdCommit( message )

            # take account of the change
            self.main_window.updateTableView()

            headline = message.split('\n')[0]

            self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        self.commit_dialog = None

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __logGitCommandError( self, e ):
        self.log.error( "'%s' returned with exit code %i" %
                        (' '.join(str(i) for i in e.command), e.status) )
        if e.stderr:
            all_lines = e.stderr.split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    def treeActionPush( self ):
        git_project = self.__treeSelectedGitProject().newInstance()
        self.setStatusText( 'Push…' )

        self.app.backgroundProcess( self.treeActionPushBg, (git_project,) )

    def treeActionPushBg( self, git_project ):
        try:
            git_project.cmdPush( self.pushProgressHandlerBg, self.pushInfoHandlerBg )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

        self.app.foregroundProcess( self.setStatusText, ('',) )
        self.app.foregroundProcess( self.main_window.updateActionEnabledStates, () )

    def pushInfoHandlerBg( self, info ):
        self.app.foregroundProcess( self.pushInfoHandler, (info,) )

    def pushInfoHandler( self, info ):
        self.log.info( 'Push summary: %s' % (info.summary,) )

    def pushProgressHandlerBg( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        self.app.foregroundProcess( self.pushProgressHandler, (is_begin, is_end, stage_name, cur_count, max_count, message) )

    def pushProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Push %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Push %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Push %s' % (stage_name,)

        if message != '':
            status = '%s - %s' % (status, message)
           
        self.setStatusText( status )
        if is_end:
            self.log.info( status )

    # ------------------------------------------------------------
    def treeActionPull( self ):
        git_project = self.__treeSelectedGitProject().newInstance()
        self.setStatusText( 'Pull...' )

        self.app.backgroundProcess( self.treeActionPullBg, (git_project,) )

    def treeActionPullBg( self, git_project ):
        try:
            git_project.cmdPull( self.pullProgressHandlerBg, self.pullInfoHandlerBg )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

        self.app.foregroundProcess( self.setStatusText, ('',) )
        self.app.foregroundProcess( self.main_window.updateActionEnabledStates, () )

    def pullInfoHandlerBg( self, info ):
        self.app.foregroundProcess( self.pullInfoHandler, (info,) )

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

    def pullProgressHandlerBg( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        self.app.foregroundProcess( self.pullProgressHandler, (is_begin, is_end, stage_name, cur_count, max_count, message) )

    def pullProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Pull %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Pull %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Push %s' % (stage_name,)

        if message != '':
            status = '%s - %s' % (status, message)
           
        self.setStatusText( status )
        if is_end:
            self.log.info( status )

    # ------------------------------------------------------------
    def treeActionGitLogHistory( self ):
        options = wb_git_log_history.WbGitLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            git_project = self.__treeSelectedGitProject()

            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app,
                    T_('Commit Log for %s') % (git_project.projectName(),),
                    self.main_window.getQIcon( 'wb.png' ) )
            commit_log_view.showCommitLogForRepository( git_project, options )
            commit_log_view.show()

    def treeActionGitStatus( self ):
        git_project = self.__treeSelectedGitProject()

        commit_status_view = wb_git_status_view.WbGitStatusView(
                self.app,
                T_('Status for %s') % (git_project.projectName(),),
                self.main_window.getQIcon( 'wb.png' ) )
        commit_status_view.setStatus(
                    git_project.getUnpushedCommits(),
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )
        commit_status_view.show()

    # ------------------------------------------------------------
    def tableActionGitStage( self ):
        self.__tableActionChangeRepo( self.__areYouSureAlways, self.__actionGitStage )

    def tableActionGitUnstage( self ):
        self.__tableActionChangeRepo( self.__areYouSureAlways, self.__actionGitUnStage )

    def tableActionGitRevert( self ):
        self.__tableActionChangeRepo( self.__areYouSureRevert, self.__actionGitRevert )

    def tableActionGitDelete( self ):
        self.__tableActionChangeRepo( self.__areYouSureDelete, self.__actionGitDelete )

    def tableActionGitDiffSmart( self ):
        self._debug( 'tableActionGitDiffSmart()' )
        self.main_window._tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffSmart )

    def tableActionGitDiffStagedVsWorking( self ):
        self._debug( 'tableActionGitDiffStagedVsWorking()' )
        self.main_window._tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffStagedVsWorking )

    def tableActionGitDiffHeadVsStaged( self ):
        self._debug( 'tableActionGitDiffHeadVsStaged()' )
        self.main_window._tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffHeadVsStaged )

    def tableActionGitDiffHeadVsWorking( self ):
        self._debug( 'tableActionGitDiffHeadVsWorking()' )
        self.main_window._tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffHeadVsWorking )

    def tableActionGitLogHistory( self ):
        self.main_window._tableActionViewRepo( self.__areYouSureAlways, self.__actionGitLogHistory )

    def __actionGitStage( self, git_project, filename ):
        git_project.cmdStage( filename )

    def __actionGitUnStage( self, git_project, filename ):
        git_project.cmdUnstage( 'HEAD', filename )
        pass

    def __actionGitRevert( self, git_project, filename ):
        git_project.cmdRevert( 'HEAD', filename )

    def __actionGitDelete( self, git_project, filename ):
        git_project.cmdDelete( filename )

    def __actionGitDiffSmart( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        if file_state.canDiffStagedVsWorking():
            self.__actionGitDiffStagedVsWorking( git_project, filename )

        elif file_state.canDiffHeadVsStaged():
            self.__actionGitDiffHeadVsStaged( git_project, filename )

        elif file_state.canDiffHeadVsWorking():
            self.__actionGitDiffHeadVsWorking( git_project, filename )

    def __diffUnified( self, old_lines, new_lines ):
        return list( difflib.unified_diff( old_lines, new_lines ) )

    def __actionGitDiffHeadVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.main_window.diffTwoFiles(
                file_state.getTextLinesHead(),
                file_state.getTextLinesWorking(),
                T_('Diff HEAD vs. Work %s') % (filename,),
                T_('HEAD %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def __actionGitDiffStagedVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.main_window.diffTwoFiles(
                file_state.getTextLinesStaged(),
                file_state.getTextLinesWorking(),
                T_('Diff Staged vs. Work %s') % (filename,),
                T_('Staged %s') % (filename,),
                T_('Work %s') % (filename,)
                )

    def __actionGitDiffHeadVsStaged( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        self.main_window.diffTwoFiles(
                file_state.getTextLinesHead(),
                file_state.getTextLinesStaged(),
                T_('Diff HEAD vs. Staged %s') % (filename,),
                T_('HEAD %s') % (filename,),
                T_('Staged %s') % (filename,)
                )

    def __actionGitLogHistory( self, git_project, filename ):
        options = wb_git_log_history.WbGitLogHistoryOptions( self.app, self.main_window )

        if options.exec_():
            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app, T_('Commit Log for %s') % (filename,), self.main_window.getQIcon( 'wb.png' ) )

            commit_log_view.showCommitLogForFile( git_project, filename, options )
            commit_log_view.show()

    #------------------------------------------------------------
    def __areYouSureAlways( self, all_filenames ):
        return True

    def __areYouSureRevert( self, all_filenames ):
        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Revert')
        all_parts = [T_('Are you sure you wish to revert:')]
        all_parts.extend( [str(filename) for filename in all_filenames] )

        message = '\n'.join( all_parts )

        rc = QtWidgets.QMessageBox.question( self.main_window, title, message, defaultButton=default_button )
        return rc == QtWidgets.QMessageBox.Yes

    def __areYouSureDelete( self, all_filenames ):
        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Delete')
        all_parts = [T_('Are you sure you wish to delete:')]
        all_parts.extend( [str(filename) for filename in all_filenames] )

        message = '\n'.join( all_parts )

        rc = QtWidgets.QMessageBox.question( self.main_window, title, message, defaultButton=default_button )
        return rc == QtWidgets.QMessageBox.Yes

    def __tableActionChangeRepo( self, are_you_sure_function, execute_function ):
        if self.main_window._tableActionViewRepo( are_you_sure_function, execute_function ):
            git_project = self.__treeSelectedGitProject()
            git_project.saveChanges()

            # take account of the change
            self.main_window.updateTableView()
