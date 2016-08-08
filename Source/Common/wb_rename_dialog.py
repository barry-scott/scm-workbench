'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_rename_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbRenameFilenameDialog(QtWidgets.QDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Rename') )

        self.old_name = None

        self.name = QtWidgets.QLineEdit()
        self.name.textChanged.connect( self.nameTextChanged )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )
        self.ok_button.setEnabled( False )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        layout = QtWidgets.QGridLayout()
        row = 0
        layout.addWidget( QtWidgets.QLabel( T_('Name') ), row, 0 )
        layout.addWidget( self.name, row, 1 )
        row += 1
        layout.addWidget( self.buttons, row, 0, 1, 2 )

        self.setLayout( layout )

    def nameTextChanged( self, text ):
         self.ok_button.setEnabled( self.getName() != self.old_name )

    def setName( self, name ):
        self.old_name = name
        self.name.setText( self.old_name )

        # assume that the whole of the name is replaced leaving the type suffixes
        if '.' in name:
            self.name.setSelection( 0, name.index( '.' ) )

        else:
            self.name.selectAll()

    def getName( self ):
        return self.name.text().strip()

if __name__ == '__main__':
    def T_(s):
        return s

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    rename = WbRenameFilename( None, None )
    rename.setName( 'fred.txt' )
    if rename.exec_():
        print( rename.getName() )

    del rename
    del app
