#!/usr/bin/env python
import sys
import os

log_filename = '%s/gui_test.log' % (os.environ['HOME'],)
sys.stdout = open( log_filename, 'a' )
sys.stderr = sys.stdout
print('---- gui_test.py ----', flush=True)

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
    print('QtWidgets.QApplication()', flush=True)
    app = QtWidgets.QApplication( argv )

    print('HelloWindow()', flush=True)
    main_win = HelloWindow()

    print('main_win.show()', flush=True)
    main_win.show()

    print('app.exec_()', flush=True)
    rc = app.exec_()

    print('rc', rc, flush=True)
    return rc

if __name__ == "__main__":
    sys.exit( main( sys.argv ) )
