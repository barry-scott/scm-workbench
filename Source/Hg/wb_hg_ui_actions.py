'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_ui_components.py.py

'''
import sys
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_log_history_options_dialog
import wb_ui_actions
import wb_common_dialogs

import wb_hg_commit_dialog
import wb_hg_project
import wb_hg_status_view
import wb_hg_credential_dialogs 
import wb_hg_annotate

from wb_background_thread import thread_switcher

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the commit window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class HgMainWindowActions(wb_ui_actions.WbMainWindowActions):
    def __init__( self, factory ):
        super().__init__( 'hg', factory )

        self.__hg_credential_cache = HgCredentialCache()

    def setupDebug( self ):
        self._debug = self.main_window.app._debug_options._debugHgUi

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

    def enablerHgDiffHeadVsWorking( self ):
        return self.__enablerDiff( wb_hg_project.WbHgFileState.canDiffHeadVsWorking )

    def __enablerDiff( self, predicate ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return False

        focus = self.main_window.focusIsIn()
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

        focus = self.main_window.focusIsIn()

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

    @thread_switcher
    def treeTableActionHgLogHistory_Bg( self, checked=None ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionHgLogHistory_Bg, self.tableActionHgLogHistory_Bg )

    @thread_switcher
    def tableActionHgLogHistory_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self._actionHgLogHistory_Bg )

    def _actionHgLogHistory_Bg( self, hg_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        commit_log_view = self.factory.logHistoryView(
                self.app,
                T_('Commit Log for %s') % (filename,) )

        yield from commit_log_view.showCommitLogForFile_Bg( hg_project, filename, options )

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
        if e.out:
            all_lines = e.out.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.info( line )

        self.log.error( "Hg command '%s' returned with exit code %i" %
                        (' '.join( [arg.decode( sys.getdefaultencoding() ) for arg in e.args] ), e.ret) )
        if e.err:
            all_lines = e.err.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionHgPush_Bg( self, checked=None ):
        hg_project = self.selectedHgProject().newInstance()
        msg = T_('Push %s') % (hg_project.projectName(),)
        self.log.infoheader( msg )
        self.setStatusAction( msg )

        yield self.switchToBackground

        try:
            hg_project.cmdPush(
                self.deferRunInForeground( self.hgOutputHandler ),
                self.deferRunInForeground( self.hgErrorHandler ),
                self.hgCredentialsPrompt,
                self.hgAuthFailed )

        except wb_hg_project.HgCommandError as e:
            self.__logHgCommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()

        self.main_window.updateActionEnabledStates()

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionHgPull_Bg( self, checked=None ):
        hg_project = self.selectedHgProject().newInstance()
        msg = T_('Pull %s') % (hg_project.projectName(),)
        self.log.infoheader( msg )
        self.setStatusAction( msg )

        yield self.switchToBackground

        try:
            hg_project.cmdPull(
                self.deferRunInForeground( self.hgOutputHandler ),
                self.deferRunInForeground( self.hgErrorHandler ),
                self.hgCredentialsPrompt,
                self.hgAuthFailed )

        except wb_hg_project.HgCommandError as e:
            self.__logHgCommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()
        self.main_window.updateActionEnabledStates()

    #------------------------------------------------------------
    def hgOutputHandler( self, line ):
        self.log.info( line )

    def hgErrorHandler( self, line ):
        self.log.error( line )

    hg_username_prompt = 'user:'
    hg_password_prompt = 'password:'
    def hgCredentialsPrompt( self, url, realm, prompt ):
        if prompt not in (self.hg_username_prompt, self.hg_password_prompt):
            self.log.error( 'Unknown prompt "%s"' % (prompt,) )
            return ''

        if not self.__hg_credential_cache.hasCredentials( url ):
            dialog = wb_hg_credential_dialogs.WbHgGetLoginDialog( self.main_window, url, realm )
            if not dialog.exec_():
                return ''

            self.__hg_credential_cache.addCredentials( url, dialog.getUsername(), dialog.getPassword() )

        if prompt == self.hg_username_prompt:
            return self.__hg_credential_cache.username( url )

        elif prompt == self.hg_password_prompt:
            return self.__hg_credential_cache.password( url )

    def hgAuthFailed( self, url ):
        self.__hg_credential_cache.removeCredentials( url )

    #------------------------------------------------------------
    @thread_switcher
    def treeActionHgStatus_Bg( self, checked=None ):
        hg_project = self.selectedHgProject()

        yield self.app.switchToBackground

        all_outgoing_commits = hg_project.cmdOutgoingCommits(
                                    None,   # self.deferRunInForeground( self.hgOutputHandler ),
                                    self.deferRunInForeground( self.hgErrorHandler ),
                                    self.hgCredentialsPrompt,
                                    self.hgAuthFailed )
        all_incoming_commits = hg_project.cmdIncomingCommits(
                                    None,   # self.deferRunInForeground( self.hgOutputHandler ),
                                    self.deferRunInForeground( self.hgErrorHandler ),
                                    self.hgCredentialsPrompt,
                                    self.hgAuthFailed )

        yield self.app.switchToForeground

        commit_status_view = wb_hg_status_view.WbHgStatusView(
                self.app,
                T_('Status for %s') % (hg_project.projectName(),) )

        commit_status_view.setStatus(
                    all_outgoing_commits,
                    all_incoming_commits,
                    hg_project.getReportModifiedFiles(),
                    hg_project.getReportUntrackedFiles() )
        commit_status_view.show()

    # ------------------------------------------------------------
    @thread_switcher
    def tableActionHgAdd_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionHgAdd )

    @thread_switcher
    def tableActionHgRevert_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionHgRevert, self.__areYouSureRevert )

    @thread_switcher
    def tableActionHgDelete_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionHgDelete, self.__areYouSureDelete )

    def tableActionHgDiffSmart( self ):
        self._debug( 'tableActionHgDiffSmart()' )
        self.table_view.tableActionViewRepo( self.__actionHgDiffSmart )

    def tableActionHgDiffHeadVsWorking( self ):
        self._debug( 'tableActionHgDiffHeadVsWorking()' )
        self.table_view.tableActionViewRepo( self.__actionHgDiffHeadVsWorking )

    def __actionHgAdd( self, hg_project, filename ):
        hg_project.cmdAdd( filename )

    def __actionHgRevert( self, hg_project, filename ):
        hg_project.cmdRevert( filename )

    def __actionHgDelete( self, hg_project, filename ):
        file_state = hg_project.getFileState( filename )
        if file_state.isControlled():
            hg_project.cmdDelete( filename )

        else:
            try:
                file_state.absolutePath().unlink()

            except IOError as e:
                self.log.error( 'Error deleting %s' % (filename,) )
                self.log.error( str(e) )

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

    @thread_switcher
    def __tableActionChangeRepo_Bg( self, execute_function, are_you_sure_function=None ):
        @thread_switcher
        def finalise( hg_project ):
            # take account of the change
            yield from self.top_window.updateTableView_Bg()

        yield from self.table_view.tableActionViewRepo_Bg( execute_function, are_you_sure_function, finalise )

    # ------------------------------------------------------------
    def selectedHgProjectTreeNode( self ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return None

        tree_node = self.main_window.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_hg_project.HgProjectTreeNode )
        return tree_node

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionHgLogHistory_Bg( self, checked=None ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, self.main_window )

        if not options.exec_():
            return

        hg_project = self.selectedHgProject()

        commit_log_view = self.factory.logHistoryView(
                self.app,
                T_('Commit Log for %s') % (hg_project.projectName(),) )

        yield from commit_log_view.showCommitLogForRepository_Bg( hg_project, options )

    def enablerTableHgAnnotate( self ):
        if not self.main_window.isScmTypeActive( 'hg' ):
            return False

        return True

    @thread_switcher
    def tableActionHgAnnotate_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionHgAnnotate_Bg )

    @thread_switcher
    def __actionHgAnnotate_Bg( self, hg_project, filename ):
        self.setStatusAction( T_('Annotate %s') % (filename,) )
        self.progress.start( T_('Annotate %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_annotation_nodes = hg_project.cmdAnnotationForFile( filename )

        all_annotate_revs = set()
        for node in all_annotation_nodes:
            all_annotate_revs.add( node.log_id )

        yield self.switchToForeground

        self.progress.end()
        self.progress.start( T_('Annotate Commit Logs %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_commit_logs = hg_project.cmdCommitLogForAnnotateFile( filename, all_annotate_revs )

        yield self.switchToForeground

        self.setStatusAction()
        self.progress.end()

        annotate_view = wb_hg_annotate.WbHgAnnotateView(
                            self.app,
                            T_('Annotation of %s') % (filename,) )
        annotate_view.showAnnotationForFile( all_annotation_nodes, all_commit_logs )
        annotate_view.show()

    commit_key = 'hg-commit-dialog'
    def treeActionHgCommit( self ):
        if self.app.hasSingleton( self.commit_key ):
            commit_dialog = self.app.getSingleton( self.commit_key )
            commit_dialog.raise_()
            return

        hg_project = self.selectedHgProject()

        commit_dialog = wb_hg_commit_dialog.WbHgCommitDialog( self.app, hg_project )
        commit_dialog.commitAccepted.connect( self.__commitAccepted )
        commit_dialog.commitClosed.connect( self.app.wrapWithThreadSwitcher( self.__commitClosed_Bg ) )

        # show to the user
        commit_dialog.show()

        self.app.addSingleton( self.commit_key, commit_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    def __commitAccepted( self ):
        commit_dialog = self.app.getSingleton( self.commit_key )

        hg_project = self.selectedHgProject()
        message = commit_dialog.getMessage()
        commit_id = hg_project.cmdCommit( message )

        headline = message.split('\n')[0]
        self.log.infoheader( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        # close will emit the commitCLose signal
        commit_dialog.close()

    def __commitClosed_Bg( self ):
        commit_dialog = self.app.popSingleton( self.commit_key )

        # take account of any changes
        yield from self.main_window.updateTableView_Bg()

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    #============================================================
    #
    # actions for log history view
    #
    #============================================================
    def enablerTableHgDiffLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_commit_selections) in (1,2)

        elif focus == 'changes':
            if len(mw.current_file_selection) == 0:
                return False

            type_, filename = mw.changes_model.changesNode( mw.current_file_selection[0] )
            return type_ in 'M'

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def enablerTableHgAnnotateLogHistory( self ):
        mw = self.main_window
        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_commit_selections) in (1,2)

        else:
            return False

    def tableActionHgDiffLogHistory( self ):
        focus = self.main_window.focusIsIn()
        if focus == 'commits':
            self.diffLogHistory()

        elif focus == 'changes':
            self.diffFileChanges()

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def diffLogHistory( self ):
        mw = self.main_window

        #
        #   Figure out the refs for the diff and set up title and headings
        #
        if len( mw.current_commit_selections ) == 1:
            # diff working against rev
            commit_new = None
            commit_old = mw.log_model.revisionForRow( mw.current_commit_selections[0] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )

            title_vars = {'commit_old': commit_old
                         ,'date_old': date_old}

            if mw.filename is not None:
                filestate = mw.hg_project.getFileState( mw.filename )

                if filestate.isModified():
                    heading_new = 'Working'

                else:
                    heading_new = 'HEAD'

            else: # Repository
                heading_new = 'Working'

        else:
            commit_new = mw.log_model.revisionForRow( mw.current_commit_selections[0] )
            date_new = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )
            commit_old = mw.log_model.revisionForRow( mw.current_commit_selections[-1] )
            date_old = mw.log_model.dateStringForRow( mw.current_commit_selections[-1] )

            title_vars = {'commit_old': commit_old
                         ,'date_old': date_old
                         ,'commit_new': commit_new
                         ,'date_new': date_new}

            heading_new = T_('commit %(commit_new)s date %(date_new)s') % title_vars

        if mw.filename is not None:
            title = T_('Diff File %s') % (mw.filename,)

        else:
            title = T_('Diff Project %s' % (mw.hg_project.projectName(),) )

        heading_old = T_('commit %(commit_old)s date %(date_old)s') % title_vars

        #
        #   figure out the text to diff
        #
        if mw.filename is not None:
            filestate = mw.hg_project.getFileState( mw.filename )

            if commit_new is None:
                # either we want HEAD or the modified working
                text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForRevision( commit_new )

            text_old = filestate.getTextLinesForRevision( commit_old )

            self.diffTwoFiles(
                    title,
                    text_old,
                    text_new,
                    heading_old,
                    heading_new
                    )

        else: # folder
            repo_path = pathlib.Path( '.' )
            if commit_new is None:
                text = mw.hg_project.cmdDiffWorkingVsCommit( repo_path, commit_old )
                self.showDiffText( title, text.split('\n') )

            else:
                text = mw.hg_project.cmdDiffCommitVsCommit( repo_path, commit_old, commit_new )
                self.showDiffText( title, text.split('\n') )

    def diffFileChanges( self ):
        mw = self.main_window

        type_, filename = mw.changes_model.changesNode( mw.current_file_selection[0] )

        rev_new = mw.log_model.revisionForRow( mw.current_commit_selections[0] )
        rev_old = rev_new - 1
        date_new = mw.log_model.dateStringForRow( mw.current_commit_selections[0] )

        title_vars = {'rev_old': rev_old
                     ,'rev_new': rev_new
                     ,'date_new': date_new}

        heading_new = T_('commit %(rev_new)s date %(date_new)s') % title_vars
        heading_old = T_('commit %(rev_old)s') % title_vars

        title = T_('Diff %s') % (filename,)

        filepath = pathlib.Path( filename )

        text_new = mw.hg_project.getTextLinesForRevision( filepath, rev_new )
        text_old = mw.hg_project.getTextLinesForRevision( filepath, rev_old )

        self.diffTwoFiles(
                title,
                text_old,
                text_new,
                heading_old,
                heading_new
                )

    def tableActionHgAnnotateLogHistory( self ):
        self.log.error( 'annotateLogHistory TBD' )

class HgCredentialCache:
    def __init__( self ):
        self.__username = {}
        self.__password = {}

    def addCredentials( self, url, username, password ):
        self.__username[ url ] = username
        self.__password[ url ] = password

    def hasCredentials( self, url ):
        return url in self.__username

    def removeCredentials( self, url ):
        self.__username.pop( url, None )
        self.__password.pop( url, None )

    def username( self, url ):
        return self.__username[ url ]

    def password( self, url ):
        return self.__password[ url ]
