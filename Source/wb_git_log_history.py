'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_history.py


'''
import sys
import datetime

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


class WbGitHistoryOptions(QtWidgets.QDialog):
    def __init__( self, parent ):
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
        self.radio_show_all.setChecked( True )
        self.radio_show_limit.setChecked( False )
        self.spin_show_limit.setEnabled( False )
        self.radio_show_since.setChecked( False )
        self.date_since.setEnabled( False )

        self.spin_show_limit.setValue( 20 )

        since = QtCore.QDate.currentDate()
        since = since.addDays( -7 )

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

if __name__ == '__main__':
    def T_(s):
        return s

    app = QtWidgets.QApplication( ['foo'] )

    options = WbGitHistoryOptions( None )
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
