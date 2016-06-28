'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_tracked_qwidget.py

'''
from PyQt5 import QtWidgets

def closeAllWindows():
    WbTrackedModeless.closeAllWindows()

class WbTrackedModeless:
    uid = 0
    all_windows = {}

    @staticmethod
    def closeAllWindows():
        # use list to make a copy of the values as the all_windows is updated by close.
        for window in list( WbTrackedModeless.all_windows.values() ):
            window.close()

    def __init__( self ):
        self.__trackWidget()

    def __trackWidget( self ):
        WbTrackedModeless.uid += 1
        self.__window_uid = WbTrackedModeless.uid

        # remember this window to keep the object alive
        WbTrackedModeless.all_windows[ self.__window_uid ] = self

    def closeEvent( self, event ):
        del WbTrackedModeless.all_windows[ self.__window_uid ]

class WbTrackedModelessQWidget(QtWidgets.QWidget, WbTrackedModeless):
    def __init__( self ):
        # Warning: Qwidget.__init__ will call WbTrackedModeless.__init__
        QtWidgets.QWidget.__init__( self, None )

    def closeEvent( self, event ):
        WbTrackedModeless.closeEvent( self, event )

        super().closeEvent( event )
