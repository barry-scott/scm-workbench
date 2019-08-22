'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_tracked_qwidget.py

'''
from typing import Dict

from PyQt5 import QtWidgets

def closeAllWindows():
    WbTrackedModeless.closeAllWindows()

class WbTrackedModeless:
    uid = 0
    all_windows = {}    # type: Dict[int, WbTrackedModeless]

    @staticmethod
    def closeAllWindows() -> None:
        # use list to make a copy of the values as the all_windows is updated by close.
        for window in list( WbTrackedModeless.all_windows.values() ):
            window.close()

    def __init__( self ) -> None:
        self.__trackWidget()

    def __trackWidget( self ) -> None:
        WbTrackedModeless.uid += 1
        self.__window_uid = WbTrackedModeless.uid

        # remember this window to keep the object alive
        WbTrackedModeless.all_windows[ self.__window_uid ] = self

    def closeEvent( self, event ) -> None:
        del WbTrackedModeless.all_windows[ self.__window_uid ]

class WbTrackedModelessQWidget(QtWidgets.QWidget, WbTrackedModeless):
    def __init__( self ):
        super().__init__( None )

    def closeEvent( self, event ):
        super().closeEvent( event )
