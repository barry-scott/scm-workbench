'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_history.py


'''
import sys
import time
import datetime

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget

#------------------------------------------------------------
#
#   WbGitLogHistoryOptions - option to control which commit logs to show
#
#------------------------------------------------------------
class WbGitLogHistoryOptions(QtWidgets.QDialog):
    def __init__( self, app, parent ):
        self.app = app
        prefs = self.app.prefs.log_history

        super().__init__( parent )

        self.use_limit = QtWidgets.QCheckBox( T_('Show only') )
        self.use_until = QtWidgets.QCheckBox( T_('Show Until') )
        self.use_since = QtWidgets.QCheckBox( T_('Show Since') )

        self.limit = QtWidgets.QSpinBox()
        self.limit.setRange( 1, 1000000 )
        self.limit.setSuffix( T_(' Commits') )

        today = QtCore.QDate.currentDate()
        the_past = QtCore.QDate( 1990, 1, 1 )

        self.until = QtWidgets.QCalendarWidget()
        self.until.setDateRange( today, the_past )
        self.until.setHorizontalHeaderFormat( self.until.SingleLetterDayNames )
        self.until.setGridVisible( True )
        self.until.setDateEditEnabled( True )
        self.until.setVerticalHeaderFormat( self.until.NoVerticalHeader )

        self.since = QtWidgets.QCalendarWidget()
        self.since.setDateRange( today, the_past )
        self.since.setHorizontalHeaderFormat( self.since.SingleLetterDayNames )
        self.since.setGridVisible( True )
        self.since.setDateEditEnabled( True )
        self.since.setVerticalHeaderFormat( self.since.NoVerticalHeader )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( self.use_limit, 0, 0 )
        layout.addWidget( self.limit, 0, 1 )
        layout.addWidget( self.use_since, 1, 0 )
        layout.addWidget( self.since, 1, 1 )
        layout.addWidget( self.use_until, 2, 0 )
        layout.addWidget( self.until, 2, 1 )
        layout.addWidget( self.buttons, 3, 0, 1, 2 )

        self.setLayout( layout )

        # --- limit
        self.use_limit.setChecked( prefs.use_default_limit )
        self.limit.setValue( prefs.default_limit )
        self.limit.setEnabled( prefs.use_default_limit )

        # --- until
        self.use_until.setChecked( prefs.use_default_until_days_interval )
        until = QtCore.QDate.currentDate()
        until = until.addDays( -prefs.default_until_days_interval )

        self.until.setSelectedDate( until )
        self.until.setEnabled( prefs.use_default_until_days_interval )

        # --- since
        self.use_since.setChecked( prefs.use_default_since_days_interval )

        since = QtCore.QDate.currentDate()
        since = since.addDays( -prefs.use_default_since_days_interval )

        self.since.setSelectedDate( since )
        self.since.setEnabled( prefs.use_default_since_days_interval )

        # --- connect up behavior
        self.use_limit.stateChanged.connect( self.limit.setEnabled )
        self.use_until.stateChanged.connect( self.until.setEnabled )
        self.use_since.stateChanged.connect( self.since.setEnabled )

        self.since.selectionChanged.connect( self.__sinceChanged )
        self.until.selectionChanged.connect( self.__untilChanged )

    def __sinceChanged( self ):
        # since must be less then until
        since = self.since.selectedDate()
        until = self.until.selectedDate()

        if since >= until:
            until = since.addDays( 1 )
            self.until.setSelectedDate( until )

    def __untilChanged( self ):
        # since must be less then until
        since = self.since.selectedDate()
        until = self.until.selectedDate()

        if since >= until:
            since = until.addDays( -1 )
            self.since.setSelectedDate( since )

    def getLimit( self ):
        if self.use_limit.isChecked():
            return self.limit.value()

        else:
            return None

    def getUntil( self ):
        if self.use_until.isChecked():
            qt_until = self.until.selectedDate()
            until = datetime.date( qt_until.year(), qt_until.month(), qt_until.day() )
            return time.mktime( until.timetuple() )

        else:
            return None

    def getSince( self ):
        if self.use_since.isChecked():
            qt_since = self.since.selectedDate()
            since = datetime.date( qt_since.year(), qt_since.month(), qt_since.day() )
            return time.mktime( since.timetuple() )

        else:
            return None

#------------------------------------------------------------
#
#   WbGitLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------
class WbGitLogHistoryView(wb_tracked_qwidget.WbTrackedModelessQWidget):
    def __init__( self, app, title, icon ):
        self.app = app
        self._debug = self.app._debugLogHistory

        super().__init__()

        self.log_model = WbGitLogHistoryModel( self.app )

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.point_size = 14
        # point size and face need to chosen for platform
        if sys.platform.startswith( 'win' ):
            self.face = 'Courier New'

        elif sys.platform == 'darwin':
            self.face = 'Monaco'

        else:
            # Assuming linux/xxxBSD
            self.face = 'Liberation Mono'
            self.point_size = 11

        self.font = QtGui.QFont( self.face, self.point_size )

        self.table_view = WbLogTableView( self )
        self.table_view.setSelectionBehavior( self.table_view.SelectRows )
        self.table_view.setSelectionMode( self.table_view.SingleSelection )
        self.table_view.setModel( self.log_model )

        # size columns
        char_width = 10
        self.table_view.setColumnWidth( self.log_model.col_author, char_width*16 )
        self.table_view.setColumnWidth( self.log_model.col_date, char_width*16 )
        self.table_view.setColumnWidth( self.log_model.col_message, char_width*40 )

        self.commit_message = QtWidgets.QTextEdit()
        self.commit_message.setReadOnly( True )
        self.commit_message.setCurrentFont( self.font )

        self.commit_id = QtWidgets.QLineEdit()
        self.commit_id.setReadOnly( True )
        self.commit_id.setFont( self.font )

        self.commit_changes = QtWidgets.QTextEdit()
        self.commit_changes.setReadOnly( True )
        self.commit_changes.setCurrentFont( self.font )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.table_view )
        self.layout.addWidget( QtWidgets.QLabel( T_('Commit ID') ) )
        self.layout.addWidget( self.commit_id )
        self.layout.addWidget( QtWidgets.QLabel( T_('Commit Message') ) )
        self.layout.addWidget( self.commit_message )
        self.layout.addWidget( QtWidgets.QLabel( T_('Changed Files') ) )
        self.layout.addWidget( self.commit_changes )

        self.setLayout( self.layout )

        self.resize( 800, 600 )

    def showCommitLogForRepository( self, git_project, options ):
        self.log_model.loadCommitLogForRepository( git_project, options.getLimit(), options.getSince(), options.getUntil() )

    def showCommitLogForFile( self, git_project, filename, options ):
        self.log_model.loadCommitLogForFile( git_project, filename, options.getLimit(), options.getSince(), options.getUntil() )

    def selectionChanged( self ):
        all_indices = self.table_view.selectedIndexes()
        if len(all_indices) == 0:
            return

        index = all_indices[0]

        node = self.log_model.commitNode( index )
        self.commit_id.clear()
        self.commit_id.setText( node.commitIdString() )

        self.commit_message.clear()
        self.commit_message.insertPlainText( node.commitMessage() )

        self.commit_changes.clear()
        for type_, filename, old_filename in node.commitFileChanges():
            if type_ in ('A', 'D', 'M'):
                self.commit_changes.insertPlainText( '%s %s\n' % (type_, filename) )

            else:
                self.commit_changes.insertPlainText( '%s %s from %s\n' % (type_, filename, old_filename) )

class WbLogTableView(QtWidgets.QTableView):
    def __init__( self, log_view ):
        self.log_view = log_view

        self._debug = log_view._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.log_view.selectionChanged()

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

    def loadCommitLogForRepository( self, git_project, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForRepository( limit, since, until )
        self.endResetModel()

    def loadCommitLogForFile( self, git_project, filename, limit, since, until ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForFile( filename, limit, since, until )
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

    def commitNode( self, index ):
        return self.all_commit_nodes[ index.row() ]

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

if __name__ == '__main__':
    def T_(s):
        return s

    class FakePrefs:
        def __init__( self ):
            self.default_mode = 'show_all'
            self.default_limit = 20
            self.default_since_days_interval = 7
            self.default_include_tags = False

    app = QtWidgets.QApplication( ['foo'] )

    options = WbGitHistoryOptions( None, FakePrefs() )
    if options.exec_():
        print( 'mode', options.showMode() )
        if options.showMode() == 'show_limit':
            print( 'limit', options.showLimit() )

        elif options.showMode() == 'show_since':
            print( 'date', options.showSince() )

    else:
        print( 'Cancelled' )

    import time
    time.sleep( 1 )
