'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_log_history.py


'''
import sys
import time
import datetime

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget
import wb_config
import wb_main_window

import wb_scm_images

import wb_git_ui_actions

#------------------------------------------------------------
#
#   WbGitLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------
#
#   add tool bars and menu for use in the log history window
#
class GitLogHistoryWindowComponents(wb_git_ui_actions.GitMainWindowActions):
    def __init__( self ):
        super().__init__()

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('git info') )
        addTool( t, T_('Diff'), self.tableActionGitDiffLogHistory, self.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )
        addTool( t, T_('Annotate'), self.tableActionGitAnnotateLogHistory, self.enablerTableGitAnnotateLogHistory )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff'), self.tableActionGitDiffLogHistory, self.enablerTableGitDiffLogHistory, 'toolbar_images/diff.png' )

    def enablerTableGitDiffLogHistory( self ):
        return len(self.main_window.current_commit_selections) in (1,2)

    def tableActionGitDiffLogHistory( self ):
        self.main_window.diffLogHistory()

    def enablerTableGitAnnotateLogHistory( self ):
        return len(self.main_window.current_commit_selections) in (1,2)

    def tableActionGitAnnotateLogHistory( self ):
        self.main_window.annotateLogHistory()

    def __logHistoryProgress( self, count, total ):
        if total > 0:
            if count == 0:
                self.progress.start( '%(count)s of %(total)d commits loaded. %(percent)d%%', total )

            else:
                self.progress.incEventCount()

    def deferedLogHistoryProgress( self ):
        return self.app.deferRunInForeground( self.__logHistoryProgress )

class WbGitLogHistoryView(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    def __init__( self, app, title, icon ):
        self.app = app
        self._debug = self.app._debugLogHistory

        super().__init__( app, wb_scm_images, app._debugMainWindow )


        self.current_commit_selections = []
        self.current_file_selection = []

        self.filename = None
        self.git_project = None

        self.ui_component = GitLogHistoryWindowComponents()

        self.log_model = WbGitLogHistoryModel( self.app )
        self.changes_model = WbGitChangedFilesModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.font = QtGui.QFont( wb_config.face, wb_config.point_size )

        #----------------------------------------
        self.log_table = WbLogTableView( self )
        self.log_table.setSelectionBehavior( self.log_table.SelectRows )
        self.log_table.setSelectionMode( self.log_table.ExtendedSelection )
        self.log_table.setModel( self.log_model )

        # size columns
        char_width = 10
        self.log_table.setColumnWidth( self.log_model.col_author, char_width*16 )
        self.log_table.setColumnWidth( self.log_model.col_date, char_width*16 )
        self.log_table.setColumnWidth( self.log_model.col_message, char_width*40 )

        #----------------------------------------
        self.commit_message = QtWidgets.QTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setCurrentFont( self.font )

        #----------------------------------------
        self.commit_id = QtWidgets.QLineEdit()
        self.commit_id.setReadOnly( True )
        self.commit_id.setFont( self.font )

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
        self.layout.addWidget( QtWidgets.QLabel( T_('Commit ID') ) )
        self.layout.addWidget( self.commit_id )
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
        return scm_type == 'git'

    def showCommitLogForRepository( self, git_project, options ):
        self.filename = None
        self.git_project = git_project

        yield self.app.switchToBackground

        self.log_model.loadCommitLogForRepository( self.ui_component.deferedLogHistoryProgress(), git_project, options.getLimit(), options.getSince(), options.getUntil() )

        yield self.app.switchToForeground

        self.ui_component.progress.end()
        self.updateEnableStates()
        self.show()

    def showCommitLogForFile( self, git_project, filename, options ):
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
        if len(self.current_file_selection) == 0:
            return

        node = self.changes_model.changesNode( self.current_file_selection[0] )

    def diffLogHistory( self ):
        if len( self.current_commit_selections ) == 1:
            # diff working against rev
            commit_new = None
            commit_old = self.log_model.commitForRow( self.current_commit_selections[0] )

            title = T_('Working vs. %s') % (commit_old,)
            heading_new = 'Working'
            heading_old = commit_old

        else:
            commit_new = self.log_model.commitForRow( self.current_commit_selections[0] )
            commit_old = self.log_model.commitForRow( self.current_commit_selections[-1] )

            title = T_('%s vs. %s') % (commit_old, commit_new)
            heading_new = commit_new
            heading_old = commit_old

        if self.filename is None:
            if commit_new is None:
                text = self.git_project.cmdDiffWorkingVsCommit( '.', commit_old )
                self.ui_component.showDiffText( title, text.split('\n') )

            else:
                text = self.git_project.cmdDiffCommitVsCommit( '.', commit_old, commit_new )
                self.ui_component.showDiffText( title, text.split('\n') )

        else:
            filestate = self.git_project.getFileState( self.filename )
            if commit_new is None:
                text_new = filestate.getTextLinesWorking()

            else:
                text_new = filestate.getTextLinesForCommit( commit_new )

            text_old = filestate.getTextLinesForCommit( commit_old )

            self.ui_component.diffTwoFiles(
                    text_old,
                    text_new,
                    title,
                    heading_old,
                    heading_new
                    )

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


class WbGitLogHistoryModel(QtCore.QAbstractTableModel):
    col_author = 0
    col_date = 1
    col_message = 2

    column_titles = (U_('Author'), U_('Date'), U_('Message'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugLogHistory

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
                return node.commitDate().strftime( '%Y-%m-%d %H:%M:%S' )

            elif col == self.col_message:
                return node.commitMessage().split('\n')[0]

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

class WbGitChangedFilesModel(QtCore.QAbstractTableModel):
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
