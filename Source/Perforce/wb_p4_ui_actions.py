'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_ui_components.py.py

'''
import sys
import os
import pathlib

import wb_log_history_options_dialog
import wb_ui_actions
import wb_common_dialogs

import wb_p4_change_dialog
import wb_p4_project
import wb_p4_status_view
import wb_p4_credential_dialogs
import wb_p4_annotate

from wb_background_thread import thread_switcher

#
#   Start with the main window components interface
#   and add actions used by the main window
#   and the change window
#
#   then derive to add tool bars and menus
#   appropiate to each context
#
class P4MainWindowActions(wb_ui_actions.WbMainWindowActions):
    def __init__( self, factory ):
        super().__init__( 'p4', factory )

        self.__p4_credential_cache = P4CredentialCache()

    def setupDebug( self ):
        self.debugLog = self.main_window.app.debug_options.debugLogP4Ui

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerP4FilesEdit( self ):
        return self.__enablerP4Files( wb_p4_project.WbP4FileState.canEdit )

    def enablerP4FilesAdd( self ):
        return self.__enablerP4Files( wb_p4_project.WbP4FileState.canAdd )

    def enablerP4FilesRevert( self ):
        return self.__enablerP4Files( wb_p4_project.WbP4FileState.canRevert )

    def enablerP4ChangeInclude( self ):
        return len(self.main_window.all_included_files) != 0

    def __enablerP4Files( self, predicate ):
        if not self.main_window.isScmTypeActive( 'p4' ):
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

    def enablerP4DiffHeadVsWorking( self ):
        return self.__enablerDiff( wb_p4_project.WbP4FileState.canDiffHeadVsWorking )

    def __enablerDiff( self, predicate ):
        if not self.main_window.isScmTypeActive( 'p4' ):
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

    def enablerP4DiffSmart( self ):
        if not self.main_window.isScmTypeActive( 'p4' ):
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

    def enablerP4LogHistory( self ):
        return True

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def treeActionP4Debug1( self ):
        self.log.info( 'P4MainWindowActions.treeActionP4Debug1()' )
        p4_project = self.selectedP4Project()
        self.log.info( 'P4 Project: %r' % (p4_project,) )

    @thread_switcher
    def treeActionP4Connect_Bg( self, _arg=None ):
        p4_project = self.selectedP4Project()
        if p4_project.cmdConnect():
            yield from self.top_window.updateTableView_Bg()

    @thread_switcher
    def treeActionP4Login_Bg( self, _arg=None ):
        p4_project = self.selectedP4Project()
        username = os.environ['USER']
        dialog = wb_p4_credential_dialogs.WbP4GetLoginDialog( self.app, self.main_window, username )
        if not dialog.exec():
            return

        if p4_project.cmdLogin( username, dialog.getPassword() ):
            yield from self.top_window.updateTableView_Bg()

    def treeTableActionP4DiffSmart( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionP4DiffSmart, self.tableActionP4DiffSmart )

    def treeTableActionP4DiffHeadVsWorking( self ):
        self.main_window.callTreeOrTableFunction( self.treeActionP4DiffHeadVsWorking, self.tableActionP4DiffHeadVsWorking )

    @thread_switcher
    def treeTableActionP4LogHistory_Bg( self, checked=None ):
        yield from self.main_window.callTreeOrTableFunction_Bg( self.treeActionP4LogHistory_Bg, self.tableActionP4LogHistory_Bg )

    @thread_switcher
    def tableActionP4LogHistory_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self._actionP4LogHistory_Bg )

    @thread_switcher
    def _actionP4LogHistory_Bg( self, p4_project, filename ):
        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, None, self.main_window )

        if not options.exec():
            return

        change_log_view = self.factory.logHistoryView(
                self.app,
                T_('Change Log for %s') % (filename,) )

        yield from change_log_view.showChangeLogForFile_Bg( p4_project, filename, options )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def selectedP4Project( self ):
        scm_project = self.table_view.selectedScmProject()
        if scm_project is None:
            return None

        if not isinstance( scm_project, wb_p4_project.P4Project ):
            return None

        return scm_project

    def treeActionP4DiffSmart( self ):
        self.debugLog( 'treeActionP4DiffSmart()' )

    def treeActionP4DiffHeadVsWorking( self ):
        tree_node = self.selectedP4ProjectTreeNode()
        if tree_node is None:
            return

        diff_list = tree_node.project.cmdDiffFolder( tree_node.relativePath() )
        if len(diff_list) == 0:
            self.log.info( 'Nothing to diff' )

        else:
            self.p4ShowDiffText( T_('Head vs. Working for %s') %
                                        (tree_node.relativePath(),),
                                        diff_list )

    def p4ShowDiffText( self, title, diff_list ):
        diff_text = []
        for diff in diff_list:
            if type(diff) == dict:
                diff_text.append( 'Diff %(clientFile)s@%(rev)s' % diff )

            else:
                diff_text.append( diff )

        self.showDiffText( title, diff_text )

    def __logP4CommandError( self, e ):
        if e.out:
            all_lines = e.out.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.info( line )

        self.log.error( "P4 command '%s' returned with exit code %i" %
                        (' '.join( [arg.decode( sys.getdefaultencoding() ) for arg in e.args] ), e.ret) )
        if e.err:
            all_lines = e.err.decode( sys.getdefaultencoding() ).split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionP4Push_Bg( self, checked=None ):
        p4_project = self.selectedP4Project().newInstance()
        msg = T_('Push %s') % (p4_project.projectName(),)
        self.log.infoheader( msg )
        self.setStatusAction( msg )

        yield self.switchToBackground

        try:
            p4_project.cmdPush(
                self.deferRunInForeground( self.p4OutputHandler ),
                self.deferRunInForeground( self.p4ErrorHandler ),
                self.p4CredentialsPrompt,
                self.p4AuthFailed )

        except wb_p4_project.P4CommandError as e:
            self.__logP4CommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()

        self.main_window.updateActionEnabledStates()

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionP4Pull_Bg( self, checked=None ):
        p4_project = self.selectedP4Project().newInstance()
        msg = T_('Pull %s') % (p4_project.projectName(),)
        self.log.infoheader( msg )
        self.setStatusAction( msg )

        yield self.switchToBackground

        try:
            p4_project.cmdPull(
                self.deferRunInForeground( self.p4OutputHandler ),
                self.deferRunInForeground( self.p4ErrorHandler ),
                self.p4CredentialsPrompt,
                self.p4AuthFailed )

        except wb_p4_project.P4CommandError as e:
            self.__logP4CommandError( e )

        yield self.switchToForeground

        self.progress.end()
        self.setStatusAction()
        self.setStatusGeneral()
        self.main_window.updateActionEnabledStates()

    #------------------------------------------------------------
    def p4OutputHandler( self, line ):
        self.log.info( line )

    def p4ErrorHandler( self, line ):
        self.log.error( line )

    #------------------------------------------------------------
    @thread_switcher
    def treeActionP4Status_Bg( self, checked=None ):
        p4_project = self.selectedP4Project()

        yield self.app.switchToBackground

        all_opened_files = p4_project.cmdOpenedFiles()
        all_changes_pending = p4_project.cmdChangesPending()
        all_changes_shelved = p4_project.cmdChangesShelved()

        yield self.app.switchToForeground

        change_status_view = wb_p4_status_view.WbP4StatusView(
                self.app,
                T_('Status for %s') % (p4_project.projectName(),) )

        change_status_view.setStatus(
                    all_opened_files,
                    all_changes_pending,
                    all_changes_shelved )
        change_status_view.show()

    # ------------------------------------------------------------
    @thread_switcher
    def tableActionP4Edit_Bg( self, checked=None ):
        # p4 edit filename ...
        yield from self.__tableActionChangeRepo_Bg( self.__actionP4Edit )

        self.table_view.tableActionEdit()

    @thread_switcher
    def tableActionP4Add_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionP4Add )

    @thread_switcher
    def tableActionP4Revert_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionP4Revert, self.__areYouSureRevert )

    @thread_switcher
    def tableActionP4Delete_Bg( self, checked=None ):
        yield from self.__tableActionChangeRepo_Bg( self.__actionP4Delete, self.__areYouSureDelete )

    def tableActionP4DiffSmart( self ):
        self.debugLog( 'tableActionP4DiffSmart()' )
        self.table_view.tableActionViewRepo( self.__actionP4DiffSmart )

    def tableActionP4DiffHeadVsWorking( self ):
        self.debugLog( 'tableActionP4DiffHeadVsWorking()' )
        self.table_view.tableActionViewRepo( self.__actionP4DiffHeadVsWorking )

    def __actionP4Edit( self, p4_project, filename ):
        p4_project.cmdEdit( filename )

    def __actionP4Add( self, p4_project, filename ):
        p4_project.cmdAdd( filename )

    def __actionP4Revert( self, p4_project, filename ):
        p4_project.cmdRevert( filename )

    def __actionP4Delete( self, p4_project, filename ):
        file_state = p4_project.getFileState( filename )
        if file_state.isControlled():
            p4_project.cmdDelete( filename )

        else:
            try:
                file_state.absolutePath().unlink()

            except IOError as e:
                self.log.error( 'Error deleting %s' % (filename,) )
                self.log.error( str(e) )

    def __actionP4DiffSmart( self, p4_project, filename ):
        file_state = p4_project.getFileState( filename )

        if file_state.canDiffHeadVsWorking():
            self.__actionP4DiffHeadVsWorking( p4_project, filename )

    def __actionP4DiffHeadVsWorking( self, p4_project, filename ):
        file_state = p4_project.getFileState( filename )

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
        def finalise( p4_project ):
            # take account of the change
            yield from self.top_window.updateTableView_Bg()

        yield from self.table_view.tableActionViewRepo_Bg( execute_function, are_you_sure_function, finalise )

    # ------------------------------------------------------------
    def selectedP4ProjectTreeNode( self ):
        if not self.main_window.isScmTypeActive( 'p4' ):
            return None

        tree_node = self.main_window.selectedScmProjectTreeNode()
        assert isinstance( tree_node, wb_p4_project.P4ProjectTreeNode )
        return tree_node

    # ------------------------------------------------------------
    @thread_switcher
    def treeActionP4LogHistory_Bg( self, checked=None ):
        folder_path = self.table_view.selectedAbsoluteFolder()
        if folder_path is None:
            return

        options = wb_log_history_options_dialog.WbLogHistoryOptions( self.app, None, self.main_window )

        if not options.exec():
            return

        p4_project = self.selectedP4Project()

        change_log_view = self.factory.logHistoryView(
                self.app,
                T_('Change Log for %s') % (p4_project.projectName(),) )

        yield from change_log_view.showChangeLogForFolder_Bg( p4_project, folder_path, options )

    def enablerTableP4Annotate( self ):
        if not self.main_window.isScmTypeActive( 'p4' ):
            return False

        return True

    @thread_switcher
    def tableActionP4Annotate_Bg( self, checked=None ):
        yield from self.table_view.tableActionViewRepo_Bg( self.__actionP4Annotate_Bg )

    @thread_switcher
    def __actionP4Annotate_Bg( self, p4_project, filename ):
        self.setStatusAction( T_('Annotate %s') % (filename,) )
        self.progress.start( T_('Annotate %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_annotation_nodes = p4_project.cmdAnnotationForFile( filename )

        all_annotate_revs = set()
        for node in all_annotation_nodes:
            all_annotate_revs.add( node.log_id )

        yield self.switchToForeground

        self.progress.end()
        self.progress.start( T_('Annotate Change Logs %(count)d'), 0 )

        yield self.switchToBackground

        # when we know that exception can be raised catch it...
        all_change_logs = p4_project.cmdChangeLogForAnnotateFile( filename, all_annotate_revs )

        yield self.switchToForeground

        self.setStatusAction()
        self.progress.end()

        annotate_view = wb_p4_annotate.WbP4AnnotateView(
                            self.app,
                            T_('Annotation of %s') % (filename,) )
        annotate_view.showAnnotationForFile( all_annotation_nodes, all_change_logs )
        annotate_view.show()

    change_key = 'p4-change-dialog'
    def treeActionP4Change( self ):
        if self.app.hasSingleton( self.change_key ):
            change_dialog = self.app.getSingleton( self.change_key )
            change_dialog.raise_()
            return

        p4_project = self.selectedP4Project()

        change_dialog = wb_p4_change_dialog.WbP4ChangeDialog( self.app, p4_project )
        change_dialog.changeAccepted.connect( self.app.wrapWithThreadSwitcher( self.__changeAccepted_Bg ) )
        change_dialog.changeClosed.connect( self.__changeClosed )

        # show to the user
        change_dialog.show()

        self.app.addSingleton( self.change_key, change_dialog )

        # enabled states may have changed
        self.main_window.updateActionEnabledStates()

    @thread_switcher
    def __changeAccepted_Bg( self ):
        change_dialog = self.app.popSingleton( self.change_key )

        changespec = change_dialog.getChangeSpec()
        self.app.log.info( 'QQQ changespec %r' % (changespec,) )
        headline = changespec['Description'].split('\n')[0]
        self.log.infoheader( T_('Change "%(headline)s"') % {'headline': headline} )

        p4_project = self.selectedP4Project()
        change_id = p4_project.cmdSaveChange( changespec )

        # close will emit the changeClose signal
        change_dialog.close()

        # take account of any changes
        yield from self.main_window.updateTableView_Bg()

    def __changeClosed( self ):
        if self.app.hasSingleton( self.change_key ):
            self.app.popSingleton( self.change_key )

    def tableActionChangeInclude( self, checked=None ):
        all_file_states = self.tableSelectedAllFileStates()
        if len(all_file_states) == 0:
            return

        for entry in all_file_states:
            if checked:
                self.main_window.addChangeIncludedFile( entry.relativePath() )

            else:

                self.main_window.removeChangeIncludedFile( entry.relativePath() )

        # take account of the changes
        yield from self.top_window.updateTableView_Bg()

    def checkerActionChangeInclude( self ):
        all_file_states = self.tableSelectedAllFileStates()
        if len(all_file_states) == 0:
            return False

        for entry in all_file_states:
            if entry.relativePath() not in self.main_window.all_included_files:
                return False

        return True

    #============================================================
    #
    # actions for log history view
    #
    #============================================================
    def enablerTableP4DiffLogHistory( self ):
        mw = self.main_window

        focus = mw.focusIsIn()
        if focus == 'commits':
            return len(mw.current_change_selections) in (1,2)

        elif focus == 'changes':
            if len(mw.current_file_selection) == 0:
                return False

            type_, filename = mw.changes_model.changesNode( mw.current_file_selection[0] )
            return type_ in ('edit',)

        else:
            assert False, 'focus not as expected: %r' % (focus,)

    def enablerTableP4AnnotateLogHistory( self ):
        mw = self.main_window
        focus = mw.focusIsIn()
        if focus == 'changes':
            return len(mw.current_change_selections) in (1,2)

        else:
            return False

    def tableActionP4DiffLogHistory( self ):
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
        if len( mw.current_change_selections ) == 1:
            # diff working against rev
            change_new = None
            change_old = mw.log_model.changeForRow( mw.current_change_selections[0] )
            date_old = mw.log_model.dateStringForRow( mw.current_change_selections[0] )

            title_vars = {'change_old': change_old
                         ,'date_old': date_old}

            if mw.filename is not None:
                filestate = mw.p4_project.getFileState( mw.filename )

                if filestate.isOpened():
                    heading_new = 'Working'

                else:
                    heading_new = 'HEAD'

            else: # Repository
                heading_new = 'Working'

        else:
            change_new = mw.log_model.changeForRow( mw.current_change_selections[0] )
            date_new = mw.log_model.dateStringForRow( mw.current_change_selections[0] )
            change_old = mw.log_model.changeForRow( mw.current_change_selections[-1] )
            date_old = mw.log_model.dateStringForRow( mw.current_change_selections[-1] )

            title_vars = {'change_old': change_old
                         ,'date_old': date_old
                         ,'change_new': change_new
                         ,'date_new': date_new}

            heading_new = T_('Change %(change_new)s date %(date_new)s') % title_vars

        if mw.filename is not None:
            title = T_('Diff File %s') % (mw.filename,)

        else:
            title = T_('Diff Project %s' % (mw.p4_project.projectName(),) )

        heading_old = T_('Change %(change_old)s date %(date_old)s') % title_vars

        #
        #   figure out the text to diff
        #
        if mw.filename is not None:
            filestate = mw.p4_project.getFileState( mw.filename )

            if change_new is None:
                # either we want HEAD or the modified working
                text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForRevision( change_new )

            text_old = filestate.getTextLinesForRevision( change_old )

            self.diffTwoFiles(
                    title,
                    text_old,
                    text_new,
                    heading_old,
                    heading_new
                    )

        else: # folder
            repo_path = pathlib.Path( '.' )
            if change_new is None:
                diff_list = mw.p4_project.cmdDiffWorkingVsChange( repo_path, change_old )
                self.p4ShowDiffText( title, diff_list )

            else:
                diff_list = mw.p4_project.cmdDiffChangeVsChange( repo_path, change_old, change_new )
                self.p4ShowDiffText( title, diff_list )

    def diffFileChanges( self ):
        mw = self.main_window

        type_, filename = mw.changes_model.changesNode( mw.current_file_selection[0] )

        rev_new = mw.log_model.changeForRow( mw.current_change_selections[0] )
        rev_old = rev_new - 1
        date_new = mw.log_model.dateStringForRow( mw.current_change_selections[0] )

        title_vars = {'rev_old': rev_old
                     ,'rev_new': rev_new
                     ,'date_new': date_new}

        heading_new = T_('change %(rev_new)s date %(date_new)s') % title_vars
        heading_old = T_('change %(rev_old)s') % title_vars

        title = T_('Diff %s') % (filename,)

        filepath = pathlib.Path( filename )

        text_new = mw.p4_project.getTextLinesForRevision( filepath, rev_new )
        text_old = mw.p4_project.getTextLinesForRevision( filepath, rev_old )

        self.diffTwoFiles(
                title,
                text_old,
                text_new,
                heading_old,
                heading_new
                )

    def tableActionP4AnnotateLogHistory( self ):
        self.log.error( 'annotateLogHistory TBD' )

class P4CredentialCache:
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
