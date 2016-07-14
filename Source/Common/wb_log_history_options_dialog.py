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

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

#------------------------------------------------------------
#
#   WbLogHistoryOptions - option to control which commit logs to show
#
#------------------------------------------------------------
class WbLogHistoryOptions(QtWidgets.QDialog):
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
        row = 0
        layout.addWidget( self.use_limit,   row, 0 )
        layout.addWidget( self.limit,       row, 1, 1, 3 )
        row += 1
        layout.addWidget( self.use_since,   row, 0 )
        layout.addWidget( self.since,       row, 1 )
        layout.addWidget( self.use_until,   row, 2 )
        layout.addWidget( self.until,       row, 3 )
        row += 1
        layout.addWidget( self.buttons,     row, 0, 1, 4 )

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
