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
    WbTrackedModelessQWidget.closeAllWindows()

class WbTrackedModelessQWidget(QtWidgets.QWidget):
    uid = 0
    all_windows = {}

    @staticmethod
    def closeAllWindows():
        # use list to make a copy of the values as the all_windows is updated by close.
        for window in list( WbTrackedModelessQWidget.all_windows.values() ):
            window.close()

    def __init__( self ):
        super().__init__( None )

        self.__trackWidget()

    def __trackWidget( self ):
        WbTrackedModelessQWidget.uid += 1
        self.__window_uid = WbTrackedModelessQWidget.uid

        # remember this window to keep the object alive
        WbTrackedModelessQWidget.all_windows[ self.__window_uid ] = self

    def closeEvent( self, event ):
        del WbTrackedModelessQWidget.all_windows[ self.__window_uid ]

        super().closeEvent( event )
