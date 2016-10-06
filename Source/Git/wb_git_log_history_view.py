'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

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

import wb_ui_components

#------------------------------------------------------------
#
#   WbGitLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------
#
#   add tool bars and menu for use in the log history window
#
class GitLogHistoryWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        super().__init__( 'git', factory )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('git info') )
        addTool( t, T_('Diff'), act.tableActionGitDiffLogHistory, act.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )
        addTool( t, T_('Annotate'), act.tableActionGitAnnotateLogHistory, act.enablerTableGitAnnotateLogHistory )

    def setupTableContextMenu( self, m, addMenu ):
        act = self.ui_actions

        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), act.tableActionGitDiffLogHistory, act.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )

    def deferedLogHistoryProgress( self ):
        return self.app.deferRunInForeground( self.__logHistoryProgress )

    def __logHistoryProgress( self, count, total ):
        if total > 0:
            if count == 0:
                self.progress.start( '%(count)s of %(total)d commits loaded. %(percent)d%%', total )

            else:
                self.progress.incEventCount()


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

        self.ui_component = GitLogHistoryWindowComponents( self.app.getScmFactory( 'git' ) )

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
        self.log_table.setColumnWidth( self.log_model.col_date, em*16 )
        self.log_table.setColumnWidth( self.log_model.col_message, em*40 )
        self.log_table.setColumnWidth( self.log_model.col_commit_id, em*30 )

        #----------------------------------------
        self.commit_message = QtWidgets.QTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setCurrentFont( self.code_font )

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
        self.resize( 70*em, 40*ex )

        self.ui_component.setTopWindow( self.app.top_window )
        self.ui_component.setMainWindow( self, None )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.__setupTableContextMenu()

        # The rest of init has to be done after the widgets are rendered
        self.timer_init = QtCore.QTimer()
        self.timer_init.timeout.connect( self.completeStatupInitialisation )
        self.timer_init.setSingleShot( True )
        self.timer_init.start( 0 )

    def completeStatupInitialisation( self ):
        self._debug( 'completeStatupInitialisation()' )

        # set focus
        self.log_table.setFocus()

        self.timer_init = None

    def setupMenuBar( self, mb ):
        self.ui_component.setupMenuBar( mb, self._addMenu )

    def __setupTableContextMenu( self ):
        self._debug( '__setupTableContextMenu' )

        # --- setup scm_type specific menu

        m = QtWidgets.QMenu( self )

        self.ui_component.setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup scm_type specific tool bars
        self.ui_component.setupToolBarAtRight( self._addToolBar, self._addTool )

    def isScmTypeActive( self, scm_type ):
        return scm_type == 'git'

    @thread_switcher
    def showCommitLogForRepository_Bg( self, git_project, options ):
        self.filename = None
        self.git_project = git_project

        yield self.app.switchToBackground

        self.log_model.loadCommitLogForRepository( self.ui_component.deferedLogHistoryProgress(), git_project, options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

        self.ui_component.progress.end()
        self.updateEnableStates()
        self.show()

    @thread_switcher
    def showCommitLogForFile_Bg( self, git_project, filename, options ):
        self.filename = filename
        self.git_project = git_project

        yield self.app.switchToBackground

        self.log_model.loadCommitLogForFile( self.ui_component.deferedLogHistoryProgress(), git_project, filename, options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

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


class WbLogTableView(QtWidgets.QTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.main_window.selectionChangedCommit()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'commits' )

class WbGitLogHistoryModel(QtCore.QAbstractTableModel):
    col_author = 0
    col_date = 1
    col_message = 2
    col_commit_id = 3

    column_titles = (U_('Author'), U_('Date'), U_('Message'), U_('Commit ID'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debug_options._debugLogHistory

        super().__init__()

        self.all_commit_nodes  = []

    def loadCommitLogForRepository( self, progress_callback, git_project, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForRepository( progress_callback, limit, since, until )
        self.endResetModel()

    def loadCommitLogForFile( self, progress_callback, git_project, filename, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForFile( progress_callback, filename, limit, since, until )
        self.endResetModel()

    def commitForRow( self, row ):
        node = self.all_commit_nodes[ row ]
        return node.commitIdString()

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

            elif col == self.col_message:
                return node.commitMessage().split('\n')[0]

            elif col == self.col_commit_id:
                return node.commitIdString()

            assert False

        return None

class WbChangesTableView(QtWidgets.QTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbChangesTableView.selectionChanged()' )

        self.main_window.selectionChangedFile()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'changes' )

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
