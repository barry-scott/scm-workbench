'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_credential_dialogs.py

'''
from PyQt6 import QtWidgets

import wb_dialog_bases

class WbHgGetLoginDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, url, realm ):
        super().__init__( parent )

        self.setWindowTitle( T_('Mercurial Credentials - %s') % (' '.join( app.app_name_parts ),) )

        self.username = QtWidgets.QLineEdit( '' )
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        em = self.fontMetrics().horizontalAdvance( 'M' )

        self.addRow( T_('URL'), url )
        self.addRow( T_('Realm'), realm )
        self.addRow( T_('Username'), self.username, min_width=50*em )
        self.addRow( T_('Password'), self.password )

        self.addButtons()

    def completeInit( self ):
        # set focus
        self.username.setFocus()


    def nameTextChanged( self, text ):
        self.ok_button.setEnabled( self.getUsername() != '' and self.getPassword() != '' )

    def getUsername( self ):
        return self.username.text().strip()

    def getPassword( self ):
        return self.password.text().strip()
