'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_credentials_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbGitCredentialsDialog(QtWidgets.QDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Git Credentials') )

        self.url = QtWidgets.QLabel()
        self.username = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )
        self.ok_button.setEnabled( False )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        layout = QtWidgets.QGridLayout()
        row = 0
        layout.addWidget( QtWidgets.QLabel( T_('URL') ), row, 0 )
        layout.addWidget( self.url, row, 1 )
        row += 1
        layout.addWidget( QtWidgets.QLabel( T_('Username') ), row, 0 )
        layout.addWidget( self.username, row, 1 )
        row += 1
        layout.addWidget( QtWidgets.QLabel( T_('Password') ), row, 0 )
        layout.addWidget( self.password, row, 1 )
        row += 1
        layout.addWidget( self.buttons, row, 0, 1, 2 )

        self.setLayout( layout )

    def nameTextChanged( self, text ):
         self.ok_button.setEnabled( self.getUsername() != '' and self.getPassword() != '' )

    def setFields( self, url, username=None ):
        self.url.setText( url )
        if username is not None:
            self.username.setReadOnly( True )
            self.username.setText( username )
            self.password.setFocus()

        else:
            self.username.setFocus()

    def getUsername( self ):
        return self.username.text().strip()

    def getPassword( self ):
        return self.password.text().strip()

if __name__ == '__main__':
    def T_(s):
        return s

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    cred = WbGitCredentialsDialog( None, None )
    cred.setFields( 'http://fred.com/foo', 'bob' )
    if cred.exec_():
        print( cred.getUsername() )
        print( cred.getPassword() )

    del cred
    del app
