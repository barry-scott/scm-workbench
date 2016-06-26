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
from PyQt5 import QtCore

import wb_main_window
import wb_tracked_qwidget

import wb_scm_images

class WbGitCommitDialog(wb_main_window.WbMainWindow, wb_tracked_qwidget.WbTrackedModeless):
    commitAccepted = QtCore.pyqtSignal()
    commitClosed = QtCore.pyqtSignal()

    def __init__( self, app, git_project ):
        self.app = app
        self.git_project = git_project

        super().__init__( app, wb_scm_images, app._debugDiff )
        wb_tracked_qwidget.WbTrackedModeless.__init__( self )

        self.setWindowTitle( T_('Commit %s') % (git_project.projectName(),) )
        self.setWindowIcon( wb_scm_images.getQIcon( 'wb.png' ) )

        self.label_staged = QtWidgets.QLabel( T_('Staged Files') )
        self.staged = QtWidgets.QPlainTextEdit( '' )
        self.staged.setReadOnly( True )

        self.label_untracked = QtWidgets.QLabel( T_('Untracked Files') )
        self.untracked = QtWidgets.QPlainTextEdit( '' )
        self.untracked.setReadOnly( True )

        self.label_message = QtWidgets.QLabel( T_('Commit Log Message') )
        self.message = QtWidgets.QPlainTextEdit( '' )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_staged )
        self.layout.addWidget( self.staged )
        self.layout.addWidget( self.label_untracked )
        self.layout.addWidget( self.untracked )
        self.layout.addWidget( self.label_message )
        self.layout.addWidget( self.message )
        self.layout.addWidget( self.buttons )

        self.widget = QtWidgets.QWidget()
        self.widget.setLayout( self.layout )

        self.setCentralWidget( self.widget )

        self.resize( 800, 600 )

        self.ok_button.setEnabled( False )

        # connections
        self.buttons.accepted.connect( self.handleAccepted )
        self.buttons.rejected.connect( self.close )

        self.message.textChanged.connect( self.enableOkButton )

        # set focus
        self.message.setFocus()

        self.updateState()

    def closeEvent( self, event ):
        super().closeEvent( event )

        self.commitClosed.emit()

    def handleAccepted( self ):
        self.commitAccepted.emit()

    def enableOkButton( self ):
        text = self.message.toPlainText()
        self.ok_button.setEnabled( text.strip() != '' )

    def getMessage( self ):
        return self.message.toPlainText().strip()

    def updateState( self ):
        all_staged_files = self.git_project.getReportStagedFiles()
        all_untracked_files = self.git_project.getReportUntrackedFiles()

        staged_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_staged_files )] )
        untracked_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_untracked_files )] )

        self.staged.setPlainText( staged_text )
        self.untracked.setPlainText( untracked_text )
