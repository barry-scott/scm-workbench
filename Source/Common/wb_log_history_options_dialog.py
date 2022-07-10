'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_log_history.py


'''
import time
import datetime

from PyQt6 import QtWidgets
from PyQt6 import QtCore

#------------------------------------------------------------
#
#   WbLogHistoryOptions - option to control which commit logs to show
#
#------------------------------------------------------------
class WbLogHistoryOptions(QtWidgets.QDialog):
    def __init__( self, app, all_tags, parent ):
        self.app = app
        prefs = self.app.prefs.log_history

        super().__init__( parent )

        self.setWindowTitle( T_('Commit Log History Options - %s') % (' '.join( app.app_name_parts ),) )

        self.grp_show = QtWidgets.QButtonGroup()
        self.show_all = QtWidgets.QRadioButton( T_('Show All Commits') )
        self.grp_show.addButton( self.show_all )
        if all_tags:
            self.show_since_tag = QtWidgets.QRadioButton( T_('Show Since Tag') )
            self.grp_show.addButton( self.show_since_tag )
        else:
            self.show_since_tag = None

        self.show_only = QtWidgets.QRadioButton( T_('Show only:') )
        self.grp_show.addButton( self.show_only )
        self.use_limit = QtWidgets.QCheckBox( T_('Limit') )
        self.use_until = QtWidgets.QCheckBox( T_('Until') )
        self.use_since = QtWidgets.QCheckBox( T_('Since') )

        if self.show_since_tag:
            self.tag = QtWidgets.QComboBox()
            self.tag.addItems( all_tags )
            self.tag.setCurrentText( all_tags[0] )

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
        row = 0
        layout.addWidget( self.show_all,    row, 0, 1, 6 )
        row += 1
        if self.show_since_tag:
            layout.addWidget( self.show_since_tag,  row, 0, 1, 2 )
            layout.addWidget( self.tag,         row, 2, 1, 4 )
            row += 1

        layout.addWidget( self.show_only,   row, 0, 1, 6 )
        row += 1
        layout.addWidget( self.use_limit,   row, 1 )
        layout.addWidget( self.limit,       row, 2, 1, 4 )
        row += 1
        layout.addWidget( self.use_since,   row, 1 )
        layout.addWidget( self.since,       row, 2 )
        layout.addWidget( self.use_until,   row, 3 )
        layout.addWidget( self.until,       row, 4 )
        row += 1
        layout.addWidget( self.buttons,     row, 0, 1, 6 )

        self.setLayout( layout )

        # --- radio buttons
        if self.show_since_tag is not None and prefs.use_default_since_tag:
            self.show_since_tag.setChecked( True )

        elif( prefs.use_default_limit
        or prefs.use_default_until_days_interval
        or prefs.use_default_since_days_interval ):
            self.show_only.setChecked( True )

        else:
            self.show_all.setChecked( True )

        # --- tag
        if self.show_since_tag:
            self.show_since_tag.setChecked( prefs.use_default_since_tag )
            self.tag.setEnabled( prefs.use_default_since_tag )

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
        if self.show_since_tag:
            # enabling since tag turns off the other filters
            self.show_since_tag.toggled.connect( self.tag.setEnabled )

        self.show_only.toggled.connect( self.use_limit.setEnabled )
        self.show_only.toggled.connect( self.use_until.setEnabled )
        self.show_only.toggled.connect( self.use_since.setEnabled )

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

    def __useTag( self ):
        return self.show_since_tag is not None and self.show_since_tag.isChecked()

    def getTag( self ):
        if self.__useTag():
            return self.tag.currentText()

        else:
            return None

    def getLimit( self ):
        if not self.__useTag() and self.use_limit.isChecked():
            return self.limit.value()

        else:
            return None

    def getUntil( self ):
        if not self.__useTag() and self.use_until.isChecked():
            qt_until = self.until.selectedDate()
            until = datetime.date( qt_until.year(), qt_until.month(), qt_until.day() )
            return time.mktime( until.timetuple() )

        else:
            return None

    def getSince( self ):
        if not self.__useTag() and self.use_since.isChecked():
            qt_since = self.since.selectedDate()
            since = datetime.date( qt_since.year(), qt_since.month(), qt_since.day() )
            return time.mktime( since.timetuple() )

        else:
            return None
