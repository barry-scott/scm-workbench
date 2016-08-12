'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_common_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import pathlib

class WbDialog(QtWidgets.QDialog):
    def __init__( self, parent=None ):
        super().__init__( parent )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.grid_layout = QtWidgets.QGridLayout()
        self.grid_layout.setAlignment( QtCore.Qt.AlignTop )

        self.setLayout( self.grid_layout )

    def addRow( self, label, value ):
        label = QtWidgets.QLabel( label )
        if not isinstance( value, QtWidgets.QWidget ):
            value = QtWidgets.QLabel( str(value) )

        row = self.nextRow()

        self.grid_layout.addWidget( label, row, 0 )
        self.grid_layout.addWidget( value, row, 1 )

    def addButtons( self ):
        self.grid_layout.addWidget( self.buttons, self.nextRow(), 0, 1, 2 )

    def nextRow( self ):
        return self.grid_layout.rowCount()

