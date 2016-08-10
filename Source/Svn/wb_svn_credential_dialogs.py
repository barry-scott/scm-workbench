'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_info_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbSvnGetLoginDialog(QtWidgets.QDialog):
    def __init__( self, parent, realm, username, may_save ):
        super().__init__( parent )

        self.setWindowTitle( T_('SVN Credentials') )

        self.username = QtWidgets.QLineEdit( username )
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode( self.password.Password )
        if not may_save:
            self.save_credentials = None

        else:
            self.save_credentials = QtWidgets.QCheckBox()
            self.save_credentials.setCheckState( QtCore.Qt.Unchecked )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )
        self.ok_button.setEnabled( False )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        layout = QtWidgets.QGridLayout()
        def addRow( row, label, value ):
            layout.addWidget( QtWidgets.QLabel( label ), row, 0 )
            if type(value) == str:
                layout.addWidget( QtWidgets.QLabel( value ), row, 1 )
            else:
                layout.addWidget( value, row, 1 )

            return row + 1

        row = addRow(   0, T_('Realm'), realm )
        row = addRow( row, T_('Username'), self.username )
        row = addRow( row, T_('Password'), self.password )

        if self.save_credentials is not None:
            row = addRow( row, T_('Save Credentials'), self.save_credentials )

        layout.addWidget( self.buttons, row, 0, 1, 2 )

        self.setLayout( layout )

    def nameTextChanged( self, text ):
         self.ok_button.setEnabled( self.getUsername() != '' and self.getPassword() != '' )

    def getUsername( self ):
        return self.username.text().strip()

    def getPassword( self ):
        return self.password.text().strip()

    def getSaveCredentials( self ):
        return self.save_credentials.checkState() == QtCore.Qt.Checked

class WbSvnSslServerTrustDialog(QtWidgets.QDialog):
    def __init__( self, parent, info_list ):
        super().__init__( parent )

        self.setWindowTitle( T_('SVN SSL Server Trust') )

        self.realm = QtWidgets.QLabel( realm )
        self.save_trust = QtWidgets.QCheckBox()
        self.save_trust.setCheckState( QtCore.Qt.Unchecked )

        self.username.textChanged.connect( self.nameTextChanged )
        self.password.textChanged.connect( self.nameTextChanged )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )
        self.ok_button.setEnabled( False )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        def addRow( row, label, value ):
            layout.addWidget( QtWidgets.QLabel( label ), row, 0 )
            if type(value) == str:
                layout.addWidget( QtWidgets.QLabel( value ), row, 1 )
            else:
                layout.addWidget( value, row, 1 )

            return row + 1

        layout = QtWidgets.QGridLayout()
        row = 0
        row = addRow( row, T_('Hostname'), info_list['hostname'] )
        row = addRow( row, T_('Finger Print'), info_list['finger_print'] )
        row = addRow( row, T_('Valid From'), info_list['valid_from'] )
        row = addRow( row, T_('Valid Until'), info_list['valid_until'] )
        row = addRow( row, T_('Issuer Dname'), info_list['issuer_dname'] )
        row = addRow( row, T_('Realm'), info_list['realm'] )
        row = addRow( row, T_('Save Trust'), self.save_trust )

        layout.addWidget( self.buttons, row, 0, 1, 2 )

        self.setLayout( layout )

    def getSaveTrust( self ):
        return self.save_trust.checkState() == QtCore.Qt.Checked
