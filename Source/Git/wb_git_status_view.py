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

class WbGitStatusView(wb_tracked_qwidget.WbTrackedModelessQWidget):
    def __init__( self, app, title, icon ):
        self.app = app

        super().__init__()

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.label_unpushed = QtWidgets.QLabel( T_('Unpushed commits') )
        self.unpushed = QtWidgets.QPlainTextEdit( '' )
        self.unpushed.setReadOnly( True )

        self.label_staged = QtWidgets.QLabel( T_('Staged Files') )
        self.staged = QtWidgets.QPlainTextEdit( '' )
        self.staged.setReadOnly( True )

        self.label_untracked = QtWidgets.QLabel( T_('Untracked Files') )
        self.untracked = QtWidgets.QPlainTextEdit( '' )
        self.untracked.setReadOnly( True )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_unpushed )
        self.layout.addWidget( self.unpushed )
        self.layout.addWidget( self.label_staged )
        self.layout.addWidget( self.staged )
        self.layout.addWidget( self.label_untracked )
        self.layout.addWidget( self.untracked )

        self.setLayout( self.layout )

        self.resize( 800, 600 )

    def setStatus( self, all_unpushed_commits, all_staged_files, all_untracked_files ):
        unpushed_text = '\n'.join( ['"%s" id %s' % (commit.message.split('\n')[0], commit.hexsha) for commit in all_unpushed_commits] )
        all_staged_text = []
        for status, filename, renamed_to in sorted( all_staged_files ):
            if renamed_to is None:
                all_staged_text.append( '%s: %s' % (status, filename) )
            else:
                all_staged_text.append( '%s: %s -> %s' % (status, filename, renamed_to) )

        staged_text = '\n'.join( all_staged_text )
        untracked_text = '\n'.join( ['%s: %s' % (status, filename) for status, filename in sorted( all_untracked_files )] )

        self.unpushed.setPlainText( unpushed_text )
        self.staged.setPlainText( staged_text )
        self.untracked.setPlainText( untracked_text )
