#!/usr/bin/env python
import sys
import threading
import time

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QProgressBar
from PyQt6.QtCore import QSize


def backgroundActivitity(window):
    for value in range( 1, 11 ):
        time.sleep( 1 )
        window.foreground_progress_signal.emit( value )

class HelloWindow(QMainWindow):
    foreground_progress_signal = QtCore.pyqtSignal( [int] )

    def __init__( self ):
        super().__init__()

        if sys.maxsize > (2**31):
            size_int_t = 64
        else:
            size_int_t = 32

        py_ver = '%d.%d-%d' % (sys.version_info.major, sys.version_info.minor, size_int_t)

        self.label = QLabel( ' GUI test - python %s ' % (py_ver,), self )
        self.progress = QProgressBar( self )
        self.progress.setRange( 0, 10 )

        self.widget = QWidget()
        self.grid = QGridLayout( self.widget )
        self.grid.addWidget( self.label, 0, 0 )
        self.grid.addWidget( self.progress, 1, 0 )

        self.progress.setValue( 0 )

        self.setMinimumSize( QSize(350, 100) )
        self.setWindowTitle( 'GUI test - python %s' % (py_ver,) )

        self.setCentralWidget( self.widget )

        self.foreground_progress_signal.connect( self.updateProgress, type=QtCore.Qt.ConnectionType.QueuedConnection )

        self.thread = threading.Thread( target=backgroundActivitity, args=(self,) )
        self.thread.start()

    def updateProgress( self, value ):
        self.progress.setValue( value )

def main( argv ):
    app = QtWidgets.QApplication( argv )
    main_win = HelloWindow()
    main_win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )

