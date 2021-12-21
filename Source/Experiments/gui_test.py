#!/usr/bin/env python
import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtCore import QSize

class HelloWindow(QMainWindow):
    def __init__( self ):
        super().__init__()

        if sys.maxsize > (2**31):
            size_int_t = 64
        else:
            size_int_t = 32

        py_ver = '%d.%d-%d' % (sys.version_info.major, sys.version_info.minor, size_int_t)

        self.setMinimumSize( QSize(350, 100) )
        self.setWindowTitle( 'GUI test - python %s' % (py_ver,) )

        self.setCentralWidget( QLabel( ' GUI test - python %s ' % (py_ver,), self ) )

def main( argv ):
    app = QtWidgets.QApplication( argv )
    main_win = HelloWindow()
    main_win.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
