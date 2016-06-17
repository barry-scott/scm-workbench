'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_diff_main.py

'''

VERSION_STRING = "Uncontrolled"

import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_main

import wb_diff_side_by_side_view
import wb_platform_specific
import wb_debug

def noTranslation( msg ):
    return msg

def noPluralTranslation( singlar, plural, n ):
    if n == 1:
        return singlar

    else:
        return plural

import builtins
# T_( 'non plural' )
builtins.__dict__['T_'] = noTranslation
# S_( 'singular', 'plural', n )
builtins.__dict__['S_'] = noPluralTranslation
# U_( 'static string' )
# already setup in wb_main

class WbDiff_App(QtWidgets.QApplication, wb_debug.WbDebug):
    def __init__( self, file1, file2 ):
        self._debugDiffEnabled = True

        self.file1 = file1
        self.file2 = file2

        self.log = self

        wb_debug.WbDebug.__init__( self )
        super().__init__( [sys.argv[0]] )

        # self is log and app
        self.main_window = wb_diff_side_by_side_view.DiffSideBySideView( self, None, self.file1, self.file1, self.file2, self.file2 )
        self.main_window.resize( 800, 600 )

    def info( self, *args ):
        print( 'Info: %r' % (args,) )

def createDiffApp( argv ):
    return WbDiff_App( argv[1], argv[2] )

if __name__ == '__main__':
    sys.exit( wb_main.main( createDiffApp, sys.argv ) )
