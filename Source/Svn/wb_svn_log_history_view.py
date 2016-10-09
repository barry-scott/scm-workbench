'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_log_history.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget
import wb_main_window
import wb_ui_components
import wb_table_view

import wb_svn_project


#------------------------------------------------------------
#
#   WbSvnLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class SvnLogHistoryWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        super().__init__( 'svn', factory )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        addTool( t, T_('Diff'), act.tableActionSvnDiffLogHistory, act.enablerTableSvnDiffLogHistory, 'toolbar_images/diff.png' )
        addTool( t, T_('Annotate'), act.tableActionSvnAnnotateLogHistory, act.enablerTableSvnAnnotateLogHistory )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), act.tableActionSvnDiffLogHistory, act.enablerTableSvnDiffLogHistory, 'toolbar_images/diff.png' )


class WbSvnLogHistoryView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    focus_is_in_names = ('commits', 'changes')
    def __init__( self, app, title ):
        self.app = app
        self._debug = self.app._debug_options._debugLogHistory

        super().__init__( app, app._debug_options._debugMainWindow )

        self.current_commit_selections = []
        self.current_file_selection = []

        self.filename = None
        self.svn_project = None

        self.ui_component = SvnLogHistoryWindowComponents( self.app.getScmFactory( 'svn' ) )

        self.log_model = WbSvnLogHistoryModel( self.app )
        self.changes_model = WbSvnChangedFilesModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        self.code_font = self.app.getCodeFont()

        #----------------------------------------
        self.log_table = WbLogHistoryTableView( self )
        self.log_table.setSelectionBehavior( self.log_table.SelectRows )
        self.log_table.setSelectionMode( self.log_table.ExtendedSelection )
        self.log_table.setModel( self.log_model )

        # size columns
        em = self.app.fontMetrics().width( 'm' )
        self.log_table.setColumnWidth( self.log_model.col_revision, em*6 )
        self.log_table.setColumnWidth( self.log_model.col_author, em*16 )
        self.log_table.setColumnWidth( self.log_model.col_date, em*16 )
        self.log_table.setColumnWidth( self.log_model.col_message, em*40 )

        #----------------------------------------
        self.commit_message = QtWidgets.QTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setCurrentFont( self.code_font )

        #----------------------------------------
        self.changes_table = WbChangesTableView( self )
        self.changes_table.setSelectionBehavior( self.changes_table.SelectRows )
        self.changes_table.setSelectionMode( self.changes_table.SingleSelection )
        self.changes_table.setModel( self.changes_model )

        # size columns
        self.changes_table.setColumnWidth( self.changes_model.col_action, em*6 )
        self.changes_table.setColumnWidth( self.changes_model.col_path, em*60 )
        self.changes_table.setColumnWidth( self.changes_model.col_copyfrom, em*60 )

        #----------------------------------------
        self.commit_info_layout = QtWidgets.QVBoxLayout()
        self.commit_info_layout.addWidget( self.log_table )
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
        return scm_type == 'svn'

    def showCommitLogForFile( self, svn_project, filename, all_commit_nodes ):
        self.filename = filename
        self.svn_project = svn_project

        self.log_model.loadCommitLogForFile( all_commit_nodes )
        self.updateEnableStates()

    def selectionChangedCommit( self ):
        self.current_commit_selections = [index.row() for index in self.log_table.selectedIndexes() if index.column() == 0]

        if len(self.current_commit_selections) == 0:
            self.updateEnableStates()
            return

        self.current_commit_selections.sort()

        node = self.log_model.commitNode( self.current_commit_selections[0] )

        self.commit_message.clear()
        self.commit_message.insertPlainText( node.message )

        self.changes_model.loadChanges( node.changed_paths )

        self.updateEnableStates()

    def selectionChangedFile( self ):
        self.current_file_selection = [index.row() for index in self.changes_table.selectedIndexes() if index.column() == 0]
        self.updateEnableStates()

class WbLogHistoryTableView(wb_table_view.WbTableView):
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

class WbSvnLogHistoryModel(QtCore.QAbstractTableModel):
    col_revision = 0
    col_author = 1
    col_date = 2
    col_message = 3

    column_titles = (U_('Revision'), U_('Author'), U_('Date'), U_('Message'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debug_options._debugLogHistory

        super().__init__()

        self.all_commit_nodes  = []

        self.__brush_is_tag = QtGui.QBrush( QtGui.QColor( 0, 0, 255 ) )

    def loadCommitLogForFile( self, all_commit_nodes ):
        self.beginResetModel()
        self.all_commit_nodes = all_commit_nodes
        self.endResetModel()

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

    def revForRow( self, row ):
        return self.all_commit_nodes[ row ].revision

    def dateStringForRow( self, row ):
        return self.app.formatDatetime( self.all_commit_nodes[ row ].date )

    def data( self, index, role ):
        if role == QtCore.Qt.UserRole:
            return self.all_commit_nodes[ index.row() ]


        if role == QtCore.Qt.DisplayRole:
            node = self.all_commit_nodes[ index.row() ]

            col = index.column()

            if col == self.col_revision:
                return '%d' % (node.revision.number,)

            elif col == self.col_author:
                return node.author

            elif col == self.col_date:
                return self.app.formatDatetime( node.date )

            elif col == self.col_message:
                return node.message.split('\n')[0]

            assert False

        elif role == QtCore.Qt.ForegroundRole:
            node = self.all_commit_nodes[ index.row() ]
            if hasattr( node, 'is_tag' ):
                return self.__brush_is_tag

        return None

class WbChangesTableView(wb_table_view.WbTableView):
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

class WbSvnChangedFilesModel(QtCore.QAbstractTableModel):
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
            node = self.all_changes[ index.row() ]

            col = index.column()

            if col == self.col_action:
                return node.action

            elif col == self.col_path:
                return node.path

            elif col == self.col_copyfrom:
                if node.copyfrom_path is None:
                    return ''
                else:
                    return '%s@%d' % (node.copyfrom_path, node.copyfrom_revision.number)

            assert False

        return None
