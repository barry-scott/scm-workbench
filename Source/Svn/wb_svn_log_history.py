'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_history.py

'''
import time

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget
import wb_config
import wb_main_window

import wb_scm_images

import wb_svn_ui_actions


#------------------------------------------------------------
#
#   WbSvnLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------

#
#   add tool bars and menu for use in the log history window
#
class SvnLogHistoryWindowComponents(wb_svn_ui_actions.SvnMainWindowActions):
    def __init__( self ):
        super().__init__()

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        addTool( t, T_('Diff'), self.tableActionSvnDiffLogHistory, self.enablerTableSvnDiffLogHistory, 'toolbar_images/diff.png' )
        addTool( t, T_('Annotate'), self.tableActionSvnAnnotateLogHistory, self.enablerTableSvnAnnotateLogHistory )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), self.tableActionSvnDiffLogHistory, self.enablerTableSvnDiffLogHistory, 'toolbar_images/diff.png' )

    def enablerTableSvnDiffLogHistory( self ):
        return len(self.main_window.current_commit_selections) in (1,2)

    def tableActionSvnDiffLogHistory( self ):
        self.main_window.diffLogHistory()

    def enablerTableSvnAnnotateLogHistory( self ):
        return len(self.main_window.current_commit_selections) in (1,2)

    def tableActionSvnAnnotateLogHistory( self ):
        self.main_window.annotateLogHistory()

class WbSvnLogHistoryView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    def __init__( self, app, title, icon ):
        self.app = app
        self._debug = self.app._debugLogHistory

        super().__init__( app, wb_scm_images, app._debugMainWindow )

        self.current_commit_selections = []
        self.current_file_selection = []

        self.filename = None
        self.svn_project = None

        self.ui_component = SvnLogHistoryWindowComponents()

        self.log_model = WbSvnLogHistoryModel( self.app )
        self.changes_model = WbSvnChangedFilesModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.font = QtGui.QFont( wb_config.face, wb_config.point_size )

        #----------------------------------------
        self.log_table = WbLogHistoryTableView( self )
        self.log_table.setSelectionBehavior( self.log_table.SelectRows )
        self.log_table.setSelectionMode( self.log_table.ExtendedSelection )
        self.log_table.setModel( self.log_model )

        # size columns
        char_width = 10
        self.log_table.setColumnWidth( self.log_model.col_revision, char_width*6 )
        self.log_table.setColumnWidth( self.log_model.col_author, char_width*16 )
        self.log_table.setColumnWidth( self.log_model.col_date, char_width*16 )
        self.log_table.setColumnWidth( self.log_model.col_message, char_width*40 )

        #----------------------------------------
        self.commit_message = QtWidgets.QTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setCurrentFont( self.font )

        #----------------------------------------
        self.changes_table = WbChangesTableView( self )
        self.changes_table.setSelectionBehavior( self.changes_table.SelectRows )
        self.changes_table.setSelectionMode( self.changes_table.SingleSelection )
        self.changes_table.setModel( self.changes_model )

        # size columns
        char_width = 10
        self.changes_table.setColumnWidth( self.changes_model.col_action, char_width*6 )
        self.changes_table.setColumnWidth( self.changes_model.col_path, char_width*60 )
        self.changes_table.setColumnWidth( self.changes_model.col_copyfrom, char_width*60 )

        #----------------------------------------
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.log_table )
        self.layout.addWidget( QtWidgets.QLabel( T_('Commit Message') ) )
        self.layout.addWidget( self.commit_message )
        self.layout.addWidget( QtWidgets.QLabel( T_('Changed Files') ) )
        self.layout.addWidget( self.changes_table )

        #----------------------------------------
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout( self.layout )

        self.setCentralWidget( self.widget )

        self.resize( 900, 600 )

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

    def scmFocusWidget( self ):
        return 'table'

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

    def showCommitLogForFile( self, svn_project, filename, options ):
        self.filename = filename
        self.svn_project = svn_project

        self.url = svn_project.cmdInfo( self.filename ).URL

        self.log_model.loadCommitLogForFile( svn_project, filename, options.getLimit(), options.getSince(), options.getUntil() )
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
        if len(self.current_file_selection) == 0:
            return

        node = self.changes_model.changesNode( self.current_file_selection[0] )

    def diffLogHistory( self ):
        filestate = self.svn_project.getFileState( self.filename )

        if len( self.current_commit_selections ) == 1:
            # diff working against rev
            rev_new = self.svn_project.svn_rev_working
            rev_old = self.log_model.revForRow( self.current_commit_selections[0] )

            title = T_('Working vs. r%d') % (rev_old.number,)
            heading_new = 'Working'
            heading_old = 'r%d' % (rev_old.number,)

        else:
            rev_new = self.log_model.revForRow( self.current_commit_selections[0] )
            rev_old = self.log_model.revForRow( self.current_commit_selections[-1] )

            title = T_('r%d vs. r%d') % (rev_old.number, rev_new.number)
            heading_new = 'r%d' % (rev_new.number,)
            heading_old = 'r%d' % (rev_old.number,)

        if filestate.isDir():
            text = self.svn_project.cmdDiffRevisionVsRevision( self.filename, rev_old, rev_new )
            self.ui_component.showDiffText( title, text.split('\n') )

        else:
            if rev_new == self.svn_project.svn_rev_working:
                text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForRevision( rev_new )

            text_old = filestate.getTextLinesForRevision( rev_old )

            self.ui_component.diffTwoFiles(
                    title,
                    text_old,
                    text_new,
                    heading_old,
                    heading_new
                    )

class WbLogHistoryTableView(QtWidgets.QTableView):
    def __init__( self, main_window ):
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.main_window.selectionChangedCommit()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )


class WbSvnLogHistoryModel(QtCore.QAbstractTableModel):
    col_revision = 0
    col_author = 1
    col_date = 2
    col_message = 3

    column_titles = (U_('Revision'), U_('Author'), U_('Date'), U_('Message'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugLogHistory

        super().__init__()

        self.all_commit_nodes  = []

    def loadCommitLogForFile( self, svn_project, filename, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = svn_project.cmdCommitLogForFile( filename, limit, since, until )
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
                return time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( node.date ) )

            elif col == self.col_message:
                return node.message.split('\n')[0]

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

class WbSvnChangedFilesModel(QtCore.QAbstractTableModel):
    col_action = 0
    col_path = 1
    col_copyfrom = 2

    column_titles = (U_('Action'), U_('Filename'), U_('Copied from'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugLogHistory

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
