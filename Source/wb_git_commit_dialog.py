'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_commit_dialog.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui

class WbGitCommitDialog(QtWidgets.QDialog):
    def __init__( self, app, parent, all_staged_files, title ):
        self.app = app

        super().__init__( parent )

        status_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_staged_files )] )

        self.setWindowTitle( title )

        self.label_status = QtWidgets.QLabel( T_('Status') )
        self.status = QtWidgets.QPlainTextEdit( status_text )
        self.label_message = QtWidgets.QLabel( T_('Commit Log Message') )
        self.message = QtWidgets.QPlainTextEdit( '' )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_status )
        self.layout.addWidget( self.status )
        self.layout.addWidget( self.label_message )
        self.layout.addWidget( self.message )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        self.status.setReadOnly( True )

        self.resize( 800, 600 )

        self.ok_button.setEnabled( False )

        # connections
        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )
        self.message.textChanged.connect( self.enableOkButton )

        # set focus
        self.message.setFocus()

    def enableOkButton( self ):
        text = self.message.toPlainText()
        self.ok_button.setEnabled( text.strip() != '' )

    def getMessage( self ):
        return self.message.toPlainText().strip()
