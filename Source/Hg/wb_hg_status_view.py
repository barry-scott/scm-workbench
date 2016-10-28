'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_status_view.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui

import wb_tracked_qwidget

class WbHgStatusView(wb_tracked_qwidget.WbTrackedModelessQWidget):
    def __init__( self, app, title ):
        self.app = app

        super().__init__()

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        self.label_outgoing = QtWidgets.QLabel( T_('Outgoing commits') )
        self.outgoing = QtWidgets.QPlainTextEdit( '' )
        self.outgoing.setReadOnly( True )

        self.label_incoming = QtWidgets.QLabel( T_('Incoming commits') )
        self.incoming = QtWidgets.QPlainTextEdit( '' )
        self.incoming.setReadOnly( True )

        self.label_modified = QtWidgets.QLabel( T_('Modified Files') )
        self.modified = QtWidgets.QPlainTextEdit( '' )
        self.modified.setReadOnly( True )

        self.label_untracked = QtWidgets.QLabel( T_('Untracked Files') )
        self.untracked = QtWidgets.QPlainTextEdit( '' )
        self.untracked.setReadOnly( True )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_outgoing )
        self.layout.addWidget( self.outgoing )
        self.layout.addWidget( self.label_incoming )
        self.layout.addWidget( self.incoming )
        self.layout.addWidget( self.label_modified )
        self.layout.addWidget( self.modified )
        self.layout.addWidget( self.label_untracked )
        self.layout.addWidget( self.untracked )

        self.setLayout( self.layout )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 50*ex )

    def setStatus( self, all_outgoing_commits, all_incoming_commits, all_modified_files, all_untracked_files ):
        # new to old
        all_incoming_commits.reverse()
        all_outgoing_commits.reverse()

        outgoing_text = '\n'.join( ['"%s": r%d' % (log.messageFirstLine(), log.rev) for log in all_outgoing_commits] )
        incoming_text = '\n'.join( ['"%s": r%d' % (log.messageFirstLine(), log.rev) for log in all_incoming_commits] )
        modified_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_modified_files )] )
        untracked_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_untracked_files )] )

        self.outgoing.setPlainText( outgoing_text )
        self.incoming.setPlainText( incoming_text )
        self.modified.setPlainText( modified_text )
        self.untracked.setPlainText( untracked_text )
