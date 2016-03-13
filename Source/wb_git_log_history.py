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

#------------------------------------------------------------
#
#   WbGitLogHistoryOptions - option to control which commit logs to show
#
#------------------------------------------------------------
class WbGitLogHistoryOptions(QtWidgets.QDialog):
    def __init__( self, parent, prefs ):
        super().__init__( parent )

        self.radio_show_all = QtWidgets.QRadioButton( T_('Show all commits') )
        self.radio_show_limit = QtWidgets.QRadioButton( T_('Show Only') )
        self.radio_show_since = QtWidgets.QRadioButton( T_('Show commits since') )

        self.grp_show = QtWidgets.QButtonGroup()
        self.grp_show.addButton( self.radio_show_all )
        self.grp_show.addButton( self.radio_show_limit )
        self.grp_show.addButton( self.radio_show_since )

        self.spin_show_limit = QtWidgets.QSpinBox()
        self.spin_show_limit.setRange( 1, 1000000 )
        self.spin_show_limit.setSuffix( T_(' Commits') )

        today = QtCore.QDate.currentDate()
        the_past = QtCore.QDate( 1990, 1, 1 )

        self.date_since = QtWidgets.QCalendarWidget()
        self.date_since.setDateRange( today, the_past )
        self.date_since.setHorizontalHeaderFormat( self.date_since.SingleLetterDayNames )
        self.date_since.setGridVisible( True )
        self.date_since.setDateEditEnabled( True )
        self.date_since.setVerticalHeaderFormat( self.date_since.NoVerticalHeader )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( self.radio_show_all, 0, 0 )
        layout.addWidget( self.radio_show_limit, 1, 0 )
        layout.addWidget( self.spin_show_limit, 1, 1 )
        layout.addWidget( self.radio_show_since, 2, 0 )
        layout.addWidget( self.date_since, 2, 1 )
        layout.addWidget( self.buttons, 3, 0, 1, 2 )

        self.setLayout( layout )

        # wire up signals
        self.radio_show_limit.toggled.connect( self.spin_show_limit.setEnabled )
        self.radio_show_since.toggled.connect( self.date_since.setEnabled )

        # set state
        self.radio_show_all.setChecked( prefs.default_mode == 'show_all' )
        self.radio_show_limit.setChecked( prefs.default_mode == 'show_limit' )
        self.spin_show_limit.setEnabled( prefs.default_mode == 'show_limit' )
        self.radio_show_since.setChecked( prefs.default_mode == 'show_since' )
        self.date_since.setEnabled( prefs.default_mode == 'show_since' )

        self.spin_show_limit.setValue( prefs.default_limit )

        since = QtCore.QDate.currentDate()
        since = since.addDays( -prefs.default_since_days_interval )

        self.date_since.setSelectedDate( since )

    def showMode( self ):
        if self.radio_show_all.isChecked():
            return 'show_all'

        elif self.radio_show_limit.isChecked():
            return 'show_limit'

        elif self.radio_show_since.isChecked():
            return 'show_since'

    def showLimit( self ):
        assert self.showMode() == 'show_limit'
        return self.spin_show_limit.value()

    def showSince( self ):
        assert self.showMode() == 'show_since'
        return self.date_since.selectedDate()

#------------------------------------------------------------
#
#   WbGitLogHistoryView - show the commits from the log model
#
#------------------------------------------------------------
class WbGitLogHistoryView(QtWidgets.QWidget):
    uid = 0
    all_log_views = {}

    def __init__( self, app, title, icon ):
        self.app = app
        self._debug = self.app._debugLogHistory

        WbGitLogHistoryView.uid += 1
        self.window_uid = WbGitLogHistoryView.uid

        # remember this window to keep the object alive
        WbGitLogHistoryView.all_log_views[ self.window_uid ] = self

        super().__init__( None )

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

    def showCommitLogForFile( self, git_project, filename, options ):
        if options.showMode() == 'show_all':
            since = None
            limit = None

        elif options.showMode() == 'show_since':
            since = options.showSince()
            limit = None

        elif options.showMode() == 'show_limit':
            since = None
            limit = options.showLimit()

        self.log_model.loadCommitLogForFile( git_project, filename, since, limit )

    def selectionChanged( self ):
        index = self.table_view.selectedIndexes()[0]

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

    def closeEvent( self, event ):
        del WbGitLogHistoryView.all_log_views[ self.window_uid ]

        super().closeEvent( event )

class WbLogTableView(QtWidgets.QTableView):
    def __init__( self, log_view ):
        self.log_view = log_view

        self._debug = log_view._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbLogTableView.selectionChanged()' )

        self.log_view.selectionChanged()

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

    def loadCommitLogForFile( self, git_project, filename, since, limit ):
        self.beginResetModel()
        self.all_commit_nodes = git_project.cmdCommitLogForFile( filename, since, limit )
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
                return time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( node.commitDate() ) )

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
