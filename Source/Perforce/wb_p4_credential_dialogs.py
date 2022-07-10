'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_credential_dialogs.py

'''
from PyQt6 import QtWidgets

import wb_dialog_bases

class WbP4GetLoginDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, username ):
        super().__init__( parent )

        self.setWindowTitle( T_('P4 Credentials - %s') % (' '.join( app.app_name_parts ),) )

        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )

        self.password.textChanged.connect( self.passwordTextChanged )

        em = self.fontMetrics().width( 'M' )

        self.addRow( T_('Username'), username, min_width=50*em )
        self.addRow( T_('Password'), self.password )

        self.addButtons()

    def completeInit( self ):
        # set focus
        self.password.setFocus()

    def passwordTextChanged( self, text ):
        self.ok_button.setEnabled( self.getPassword() != '' )

    def getPassword( self ):
        return self.password.text().strip()
