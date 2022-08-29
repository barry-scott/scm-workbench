'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_credentials_dialog.py

'''
from PyQt6 import QtWidgets

import wb_dialog_bases

class WbGitCredentialsDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Git Credentials - %s') % (' '.join( app.app_name_parts ),) )

        self.url = QtWidgets.QLabel()
        self.username = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        em = self.fontMetrics().horizontalAdvance( 'M' )

        self.addRow( T_('URL'), self.url )
        self.addRow( T_('Username'), self.username, min_width=50*em )
        self.addRow( T_('Password'), self.password )
        self.addButtons()

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
    if cred.exec():
        print( cred.getUsername() )
        print( cred.getPassword() )

    del cred
    del app
