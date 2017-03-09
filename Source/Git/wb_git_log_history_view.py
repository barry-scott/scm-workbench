'''
 ====================================================================
 Copyright (c) 2016-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_log_history.py


'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from wb_background_thread import thread_switcher

import wb_tracked_qwidget
import wb_main_window
import wb_table_view
import wb_dialog_bases

import wb_ui_components

def U_( s: str ) -> str:
    return s

#------------------------------------------------------------
#
#   WbGitLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------
#
#   add tool bars and menu for use in the log history window
#
class GitLogHistoryWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory, view ):
        self.view = view
        super().__init__( 'git', factory )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('git info') )
        addTool( t, T_('Diff'), act.tableActionGitDiffLogHistory, act.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )
        #addTool( t, T_('Annotate'), act.tableActionGitAnnotateLogHistory, act.enablerTableGitAnnotateLogHistory )
        t = addToolBar( T_('git actions') )
        addTool( t, T_('Tag'), self.view.tableActionGitTag, self.view.enablerTableGitTag )

    def setupTableContextMenu( self, m, addMenu ):
        act = self.ui_actions

        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), act.tableActionGitDiffLogHistory, act.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )
        addMenu( m, T_('Tag'), self.view.tableActionGitTag, self.view.enablerTableGitTag )
        m.addSection( T_('Rebase') )
        addMenu( m, T_('Reword commit message'), self.view.tableActionGitRebaseReword, self.view.enablerTableGitRebaseReword )
        addMenu( m, T_('Squash commits together'), self.view.tableActionGitRebaseSquash, self.view.enablerTableGitRebaseSquash )
        addMenu( m, T_('Drop commit'), self.view.tableActionGitRebaseDrop, self.view.enablerTableGitRebaseDrop )


    def setupChangedFilesContextMenu( self, m, addMenu ):
        self.changed_files_context_menu = m

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), act.tableActionGitDiffLogHistory, act.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )

    def getChangedFilesContextMenu( self ):
        return self.changed_files_context_menu

    def deferedLogHistoryProgress( self ):
        return self.app.deferRunInForeground( self.__logHistoryProgress )

    def __logHistoryProgress( self, count, total ):
        if total > 0:
            if count == 0:
                self.progress.start( '%(count)s of %(total)d commits loaded. %(percent)d%%', total )

            else:
                self.progress.incEventCount()

class WbTagNameDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, git_project ):
        self.app = app
        self.git_project = git_project

        super().__init__( parent )

        self.setWindowTitle( T_('Add Tag') )

        self.name = QtWidgets.QLineEdit()
        self.name.textChanged.connect( self.nameTextChanged )

        em = self.fontMetrics().width( 'M' )
        self.addRow( T_('Tag Name'), self.name, min_width=50*em )
        self.addButtons()
        self.ok_button.setEnabled( False )

    def nameTextChanged( self ):
        tag_name = self.getTagName()
        enable = not self.git_project.doesTagExist( tag_name )
        self.ok_button.setEnabled( enable )

    def getTagName( self ):
        return self.name.text().strip()

class WbRebaseConfirmDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, title, all_rebase_commands, commit_message=None ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( title )

        em = self.fontMetrics().width( 'M' )

        self.rebase_details = QtWidgets.QPlainTextEdit()
        self.rebase_details.setReadOnly( True )
        self.rebase_details.setFont( app.getCodeFont() )

        self.addNamedDivider( T_('Rebase Details') )
        self.addRow( None, self.rebase_details, min_width=em*80 )

        if commit_message is not None:
            self.commit_message = QtWidgets.QPlainTextEdit()
            self.commit_message.setFont( app.getCodeFont() )
            self.commit_message.textChanged.connect( self.commitMessageChanged )

            self.addNamedDivider( T_('New Commit Message') )
            self.addRow( None, self.commit_message, min_width=em*80 )

        else:
            self.commit_message = None

        self.addButtons()

        # turn rebase details into a block of text
        all_details_text = []
        for detail_row in all_rebase_commands:
            all_details_text.append( ' '.join( detail_row ) )

        self.rebase_details.setPlainText( '\n'.join( all_details_text ) )

        if commit_message is not None:
            self.commit_message.setPlainText( commit_message )
            self.commitMessageChanged()

    def commitMessageChanged( self ):
        self.ok_button.setEnabled( self.commitMessage() != '' )

    def commitMessage( self ):
        return self.commit_message.toPlainText().strip()

class WbGitLogHistoryView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    focus_is_in_names = ('commits', 'changes')
    def __init__( self, app, title ):
        self.app = app
        self._debug = self.app._debug_options._debugLogHistory

        super().__init__( app, app._debug_options._debugMainWindow )

        self.current_commit_selections = []
        self.current_file_selection = []

        self.filename = None
        self.git_project = None
        self.reload_commit_log_options = None

        self.ui_component = GitLogHistoryWindowComponents( self.app.getScmFactory( 'git' ), self )

        self.log_model = WbGitLogHistoryModel( self.app )
        self.changes_model = WbGitChangedFilesModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        self.code_font = self.app.getCodeFont()

        #----------------------------------------
        self.log_table = WbLogTableView( self )
        self.log_table.setSelectionBehavior( self.log_table.SelectRows )
        self.log_table.setSelectionMode( self.log_table.ExtendedSelection )
        self.log_table.setModel( self.log_model )

        # size columns
        em = self.log_table.fontMetrics().width( 'm' )
        self.log_table.setColumnWidth( self.log_model.col_author, em*16 )
        self.log_table.setColumnWidth( self.log_model.col_date, em*20 )
        self.log_table.setColumnWidth( self.log_model.col_tag, em*5 )
        self.log_table.setColumnWidth( self.log_model.col_message, em*40 )
        self.log_table.setColumnWidth( self.log_model.col_commit_id, em*30 )

        #----------------------------------------
        self.commit_message = QtWidgets.QPlainTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setFont( self.code_font )

        #----------------------------------------
        self.commit_id = QtWidgets.QLineEdit()
        self.commit_id.setReadOnly( True )
        self.commit_id.setFont( self.code_font )

        #----------------------------------------
        self.changes_table = WbChangesTableView( self )
        self.changes_table.setSelectionBehavior( self.changes_table.SelectRows )
        self.changes_table.setSelectionMode( self.changes_table.SingleSelection )
        self.changes_table.setModel( self.changes_model )

        # size columns
        em = self.changes_table.fontMetrics().width( 'm' )
        self.changes_table.setColumnWidth( self.changes_model.col_action, em*6 )
        self.changes_table.setColumnWidth( self.changes_model.col_path, em*60 )
        self.changes_table.setColumnWidth( self.changes_model.col_copyfrom, em*60 )

        #----------------------------------------
        self.commit_info_layout = QtWidgets.QVBoxLayout()
        self.commit_info_layout.addWidget( self.log_table )
        self.commit_info_layout.addWidget( QtWidgets.QLabel( T_('Commit ID') ) )
        self.commit_info_layout.addWidget( self.commit_id )
        self.commit_info_layout.addWidget( QtWidgets.QLabel( T_('Commit Message') ) )
        self.commit_info_layout.addWidget( self.commit_message )

        self.commit_info = QtWidgets.QWidget()
        self.commit_info.setLayout( self.commit_info_layout )

        #----------------------------------------
        self.changed_files_layout = QtWidgets.QVBoxLayout()
        self.changed_files_layout.addWidget( QtWidgets.QLabel( T_('Changed Files') ) )
        self.changed_files_layout.addWidget( self.changes_table )

        self.changed_files = QtWidgets.QWidget()
        self.changed_files.setLayout( self.changed_files_layout )

        #----------------------------------------
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )

        self.v_split.addWidget( self.log_table )
        self.v_split.setStretchFactor( self.v_split.count()-1, 15 )
        self.v_split.addWidget( self.commit_info )
        self.v_split.setStretchFactor( self.v_split.count()-1, 6 )
        self.v_split.addWidget( self.changed_files )
        self.v_split.setStretchFactor( self.v_split.count()-1, 9 )

        self.setCentralWidget( self.v_split )

        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 90*em, 40*ex )

        self.ui_component.setTopWindow( self.app.top_window )
        self.ui_component.setMainWindow( self, None )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.__setupTableContextMenus()

    def completeInit( self ):
        self._debug( 'completeInit()' )

        # set focus
        self.log_table.setFocus()

    def setupMenuBar( self, mb ):
        self.ui_component.setupMenuBar( mb, self._addMenu )

    def __setupTableContextMenus( self ):
        self._debug( '__setupTableContextMenus' )

        m = QtWidgets.QMenu( self )
        self.ui_component.setupTableContextMenu( m, self._addMenu )

        m = QtWidgets.QMenu( self )
        self.ui_component.setupChangedFilesContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup scm_type specific tool bars
        self.ui_component.setupToolBarAtRight( self._addToolBar, self._addTool )

    def isScmTypeActive( self, scm_type ):
        return scm_type == 'git'

    #------------------------------------------------------------
    def enablerTableGitTag( self ):
        return len(self.current_commit_selections) == 1 and self.git_project is not None

    def tableActionGitTag( self ):
        node = self.log_model.commitNode( self.current_commit_selections[0] )

        dialog = WbTagNameDialog( self.app, self, self.git_project )
        if dialog.exec_():
            tag_name = dialog.getTagName()
            self.app.log.infoheader( 'Create tag %s for %s' % (tag_name, node.commitIdString()) )
            self.git_project.cmdCreateTag( tag_name, node.commitIdString() )
            self.log_model.updateTags( self.git_project )

    #------------------------------------------------------------
    def isRebasePossible( self ):
        # must have a git project
        if self.git_project is None:
            return False

        # reload_commit_log_options means that its a repo log history
        if self.reload_commit_log_options is None:
            return False

        # until may exclude HEAD which is needed in the rebase code
        if self.reload_commit_log_options.getUntil() is not None:
            return False

        # make sure all commits are unpushed
        for row in self.current_commit_selections:
            if not self.log_model.isCommitUnpushed( row ):
                return False

        return True

    def areSelectionsConsecutive( self ):
        if len(self.current_commit_selections) <= 1:
            return False

        for index in range( len(self.current_commit_selections) - 1 ):
            if (self.current_commit_selections[index] + 1) != self.current_commit_selections[index + 1]:
                return False

        return True

    @thread_switcher
    def finaliseRebase_Bg( self, rc, stdout, stderr, row_to_select ):
        for line in stdout:
            self.log.info( line )

        for line in stderr:
            if rc == 0:
                self.log.info( line )
            else:
                self.log.error( line )

        if len(stderr) == 0 and rc != 0:
            self.log.error( 'rebase failed rc=%d' % (rc,) )

        if rc != 0:
            return

        # reload the commit history to pick up the rebase changes
        yield self.app.switchToBackground

        options = self.reload_commit_log_options
        self.log_model.loadCommitLogForRepository(
                    self.ui_component.deferedLogHistoryProgress(), self.git_project,
                    options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

        self.log_table.resizeColumnToContents( self.log_model.col_date )

        self.log_table.setCurrentIndex( self.log_model.index( row_to_select, 0, QtCore.QModelIndex() ) )

        self.ui_component.progress.end()
        self.updateEnableStates()
        self.show()

    #------------------------------------------------------------
    def enablerTableGitRebaseSquash( self ):
        return (self.isRebasePossible()
                and self.areSelectionsConsecutive())    # need consecutive selection to squash

    @thread_switcher
    def tableActionGitRebaseSquash( self, checked=None ):
        first_to_squash = self.current_commit_selections[0]
        last_to_squash = self.current_commit_selections[-1]

        all_rebase_commands = []
        for row in range(first_to_squash):
            node = self.log_model.commitNode( row )
            all_rebase_commands.append( ('pick', node.commitIdString(), node.commitMessageHeadline()) )

        all_commit_messages = []
        for row in range(first_to_squash, last_to_squash):
            node = self.log_model.commitNode( row )
            all_rebase_commands.append( ('squash', node.commitIdString(), node.commitMessageHeadline()) )
            all_commit_messages.append( node )

        node = self.log_model.commitNode( last_to_squash )
        all_rebase_commands.append( ('pick', node.commitIdString(), node.commitMessageHeadline()) )
        all_commit_messages.append( node )

        all_commit_text = []
        for node in all_commit_messages:
            all_commit_text.append( node.commitMessage() )
            all_commit_text.append( '' )

        del all_commit_text[-1]

        dialog = WbRebaseConfirmDialog(
                    self.app, self,
                    T_('Rebase Squash commits'),
                    all_rebase_commands,
                    '\n'.join( all_commit_text ) )
        if dialog.exec_():
            commit_message = dialog.commitMessage()
            commit_id = self.log_model.commitNode( last_to_squash ).commitIdString()

            self.log.infoheader( 'Rebase Squash from commit %s' % (commit_id,) )

            all_rebase_commands.reverse()

            rc, stdout, stderr = self.git_project.cmdRebase(
                    commit_id,
                    all_rebase_commands,
                    commit_message
                    )

            yield from self.finaliseRebase_Bg( rc, stdout, stderr, first_to_squash )

    #------------------------------------------------------------
    def enablerTableGitRebaseReword( self ):
        return (self.isRebasePossible()
                and len(self.current_commit_selections) == 1)   # reword one entry only

    @thread_switcher
    def tableActionGitRebaseReword( self, checked=None ):
        reword_row = self.current_commit_selections[0]

        all_rebase_commands = []
        for row in range(reword_row):
            node = self.log_model.commitNode( row )
            all_rebase_commands.append( ('pick', node.commitIdString(), node.commitMessageHeadline()) )

        node = self.log_model.commitNode( reword_row )
        all_rebase_commands.append( ('reword', node.commitIdString(), node.commitMessageHeadline()) )
        commit_message = node.commitMessage()

        dialog = WbRebaseConfirmDialog(
                    self.app, self,
                    T_('Rebase Reword commit message'),
                    all_rebase_commands, commit_message )
        if dialog.exec_():
            commit_message = dialog.commitMessage()
            commit_id = self.log_model.commitNode( reword_row ).commitIdString()

            self.log.infoheader( 'Rebase Reword commit %s' % (commit_id,) )

            all_rebase_commands.reverse()

            rc, stdout, stderr = self.git_project.cmdRebase(
                    commit_id,
                    all_rebase_commands,
                    commit_message
                    )

            yield from self.finaliseRebase_Bg( rc, stdout, stderr, reword_row )

    #------------------------------------------------------------
    def enablerTableGitRebaseDrop( self ):
        return (self.isRebasePossible()
                and len(self.current_commit_selections) > 1)

    @thread_switcher
    def tableActionGitRebaseDrop( self, checked=None ):
        last_drop_row = self.current_commit_selections[-1]

        all_rebase_commands = []
        for row in range(last_drop_row+1):
            node = self.log_model.commitNode( row )
            if row in self.current_commit_selections:
                all_rebase_commands.append( ('drop', node.commitIdString(), node.commitMessageHeadline()) )
            else:
                all_rebase_commands.append( ('pick', node.commitIdString(), node.commitMessageHeadline()) )

        dialog = WbRebaseConfirmDialog(
                    self.app, self,
                    T_('Rebase Drop commits'),
                    all_rebase_commands )
        if dialog.exec_():
            all_rebase_commands.reverse()

            commit_id = self.log_model.commitNode( last_drop_row ).commitIdString()
            self.log.infoheader( 'Rebase Drop from commit %s' % (commit_id,) )

            rc, stdout, stderr = self.git_project.cmdRebase(
                    commit_id,
                    all_rebase_commands
                    )

            yield from self.finaliseRebase_Bg( rc, stdout, stderr, self.current_commit_selections[0] )

    #------------------------------------------------------------
    @thread_switcher
    def showCommitLogForRepository_Bg( self, git_project, options ):
        self.filename = None
        self.reload_commit_log_options = options
        self.git_project = git_project

        yield self.app.switchToBackground

        self.log_model.loadCommitLogForRepository(
                    self.ui_component.deferedLogHistoryProgress(), git_project,
                    options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

        self.log_table.resizeColumnToContents( self.log_model.col_date )

        self.ui_component.progress.end()
        self.updateEnableStates()
        self.show()

    @thread_switcher
    def showCommitLogForFile_Bg( self, git_project, filename, options ):
        self.filename = filename
        self.git_project = git_project

        yield self.app.switchToBackground

        self.log_model.loadCommitLogForFile(
                    self.ui_component.deferedLogHistoryProgress(), git_project,
                    filename, options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

        self.log_table.resizeColumnToContents( self.log_model.col_date )

        self.ui_component.progress.end()
        self.updateEnableStates()
        self.show()

    def selectionChangedCommit( self ):
        self.current_commit_selections = [index.row() for index in self.log_table.selectedIndexes() if index.column() == 0]

        if len(self.current_commit_selections) == 0:
            self.updateEnableStates()
            return

        self.current_commit_selections.sort()

        node = self.log_model.commitNode( self.current_commit_selections[0] )

        self.commit_id.clear()
        self.commit_id.setText( node.commitIdString() )

        self.commit_message.clear()
        self.commit_message.insertPlainText( node.commitMessage() )

        self.changes_model.loadChanges( node.commitFileChanges() )

        self.updateEnableStates()

    def selectionChangedFile( self ):
        self.current_file_selection = [index.row() for index in self.changes_table.selectedIndexes() if index.column() == 0]
        self.updateEnableStates()

class WbLogTableView(wb_table_view.WbTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

        # connect up signals
        self.customContextMenuRequested.connect( self.tableContextMenu )
        self.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.main_window.selectionChangedCommit()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'commits' )

    def tableContextMenu( self, pos ):
        self._debug( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.viewport().mapToGlobal( pos )

        self.main_window.ui_component.getTableContextMenu().exec_( global_pos )


class WbGitLogHistoryModel(QtCore.QAbstractTableModel):
    col_author = 0
    col_date = 1
    col_tag = 2
    col_message = 3
    col_commit_id = 4

    column_titles = (U_('Author'), U_('Date'), U_('Tag'), U_('Message'), U_('Commit ID'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debug_options._debugLogHistory

        super().__init__()

        self.all_commit_nodes  = []
        self.all_tags_by_id = {}
        self.all_unpushed_commit_ids = set()

        self.__brush_is_tag = QtGui.QBrush( QtGui.QColor( 0, 0, 255 ) )
        self.__brush_is_unpushed = QtGui.QBrush( QtGui.QColor( 192, 0, 192 ) )

    def loadCommitLogForRepository( self, progress_callback, git_project, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForRepository( progress_callback, limit, since, until )
        self.all_tags_by_id = git_project.cmdTagsForRepository()
        self.all_unpushed_commit_ids = set( [commit.hexsha for commit in git_project.getUnpushedCommits()] )
        self.endResetModel()

    def loadCommitLogForFile( self, progress_callback, git_project, filename, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForFile( progress_callback, filename, limit, since, until )
        self.all_tags_by_id = git_project.cmdTagsForRepository()
        self.all_unpushed_commit_ids = set( git_project.getUnpushedCommits() )
        self.endResetModel()

    def updateTags( self, git_project ):
        self.beginResetModel()
        self.all_tags_by_id = git_project.cmdTagsForRepository()
        self.endResetModel()

    def commitForRow( self, row ):
        node = self.all_commit_nodes[ row ]
        return node.commitIdString()

    def isCommitUnpushed( self, row ):
        return self.commitForRow( row ) in self.all_unpushed_commit_ids

    def dateStringForRow( self, row ):
        node = self.all_commit_nodes[ row ]
        return self.app.formatDatetime( node.commitDate() )

    def rowCount( self, parent ):
        return len( self.all_commit_nodes )

    def columnCount( self, parent ):
        return len( self.column_titles )

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return T_( self.column_titles[section] )

            if orientation == QtCore.Qt.Vertical:
                return ''

        elif role == QtCore.Qt.TextAlignmentRole and orientation == QtCore.Qt.Horizontal:
            return QtCore.Qt.AlignLeft

        return None

    def commitNode( self, row ):
        return self.all_commit_nodes[ row ]

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_commit_nodes[ index.row() ]

        if role == QtCore.Qt.DisplayRole:
            node = self.all_commit_nodes[ index.row() ]

            col = index.column()

            if col == self.col_author:
                return '%s <%s>' % (node.commitAuthor(), node.commitAuthorEmail())

            elif col == self.col_date:
                return self.app.formatDatetime( node.commitDate() )

            elif col == self.col_tag:
                return self.all_tags_by_id.get( node.commitIdString(), '' )

            elif col == self.col_message:
                return node.commitMessageHeadline()

            elif col == self.col_commit_id:
                return node.commitIdString()

            assert False

        elif role == QtCore.Qt.ForegroundRole:
            node = self.all_commit_nodes[ index.row() ]
            commit_id = node.commitIdString()

            col = index.column()
            if commit_id in self.all_tags_by_id and col == self.col_tag:
                return self.__brush_is_tag

            if commit_id in self.all_unpushed_commit_ids:
                return self.__brush_is_unpushed

        return None

class WbChangesTableView(wb_table_view.WbTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

        # connect up signals
        self.customContextMenuRequested.connect( self.tableContextMenu )
        self.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

        self.setShowGrid( False )

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbChangesTableView.selectionChanged()' )

        self.main_window.selectionChangedFile()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'changes' )

    def tableContextMenu( self, pos ):
        self._debug( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.viewport().mapToGlobal( pos )

        self.main_window.ui_component.getChangedFilesContextMenu().exec_( global_pos )

class WbGitChangedFilesModel(QtCore.QAbstractTableModel):
    col_action = 0
    col_path = 1
    col_copyfrom = 2

    column_titles = (U_('Action'), U_('Filename'), U_('Copied from'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debug_options._debugLogHistory

        super().__init__()

        self.all_changes  = []

    def loadChanges( self, all_changed_paths ):
        self.beginResetModel()
        self.all_changes = all_changed_paths
        self.endResetModel()

    def rowCount( self, parent ):
        return len( self.all_changes )

    def columnCount( self, parent ):
        return len( self.column_titles )

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return T_( self.column_titles[section] )

            if orientation == QtCore.Qt.Vertical:
                return ''

        elif role == QtCore.Qt.TextAlignmentRole and orientation == QtCore.Qt.Horizontal:
            return QtCore.Qt.AlignLeft

        return None

    def changesNode( self, row ):
        return self.all_changes[ row ]

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_changes[ index.row() ]


        if role == QtCore.Qt.DisplayRole:
            type_, filename, old_filename = self.all_changes[ index.row() ]

            col = index.column()

            if col == self.col_action:
                return type_

            elif col == self.col_path:
                return filename

            elif col == self.col_copyfrom:
                if type_ in ('A', 'D', 'M'):
                    return ''

                else:
                    return old_filename

            assert False

        return None
