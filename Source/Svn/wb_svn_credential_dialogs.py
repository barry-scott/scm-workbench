'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_credential_dialogs.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

import wb_dialog_bases

class WbSvnGetLoginDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, realm, username, may_save ):
        super().__init__( parent )

        self.setWindowTitle( T_('Svn Credentials - %s') % (' '.join( app.app_name_parts ),) )

        self.username = QtWidgets.QLineEdit( username )
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )
        if not may_save:
            self.save_credentials = None

        else:
            self.save_credentials = QtWidgets.QCheckBox()
            self.save_credentials.setCheckState( QtCore.Qt.CheckState.Unchecked )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        em = self.fontMetrics().width( 'M' )

        self.addRow( T_('Realm'), realm )
        self.addRow( T_('Username'), self.username, min_width=50*em )
        self.addRow( T_('Password'), self.password )

        if self.save_credentials is not None:
            self.addRow( T_('Save Credentials'), self.save_credentials )

        self.addButtons()

    def nameTextChanged( self, text ):
        self.ok_button.setEnabled( self.getUsername() != '' and self.getPassword() != '' )

    def getUsername( self ):
        return self.username.text().strip()

    def getPassword( self ):
        return self.password.text().strip()

    def getSaveCredentials( self ):
        return self.save_credentials.checkState() == QtCore.Qt.CheckState.Checked

class WbSvnSslServerTrustDialog(wb_dialog_bases.WbDialog):
    def __init__( self, parent, trust_info ):
        super().__init__( parent )

        self.setWindowTitle( T_('SVN SSL Server Trust') )

        self.realm = QtWidgets.QLabel( trust_info['realm'] )
        self.save_trust = QtWidgets.QCheckBox()
        self.save_trust.setCheckState( QtCore.Qt.CheckState.Unchecked )

        em = self.fontMetrics().width( 'M' )

        self.addRow( T_('Hostname'), trust_info['hostname'], min_width=50*em )
        self.addRow( T_('Finger Print'), trust_info['finger_print'] )
        self.addRow( T_('Valid From'), trust_info['valid_from'] )
        self.addRow( T_('Valid Until'), trust_info['valid_until'] )
        self.addRow( T_('Issuer Dname'), trust_info['issuer_dname'] )
        self.addRow( T_('Realm'), trust_info['realm'] )
        self.addRow( T_('Save Trust'), self.save_trust )
        self.addButtons()

    def getSaveTrust( self ):
        return self.save_trust.checkState() == QtCore.Qt.CheckState.Checked
