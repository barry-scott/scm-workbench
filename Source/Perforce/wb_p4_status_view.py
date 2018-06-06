'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_status_view.py

'''
from PyQt5 import QtWidgets

import wb_tracked_qwidget

class WbP4StatusView(wb_tracked_qwidget.WbTrackedModelessQWidget):
    def __init__( self, app, title ):
        self.app = app

        super().__init__()

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

        self.label_opened_files = QtWidgets.QLabel( T_('Opened files') )
        self.opened_files = QtWidgets.QPlainTextEdit( '' )
        self.opened_files.setReadOnly( True )

        self.label_changes_pending = QtWidgets.QLabel( T_('Pending Changes ') )
        self.changes_pending = QtWidgets.QPlainTextEdit( '' )
        self.changes_pending.setReadOnly( True )

        self.label_changes_shelved = QtWidgets.QLabel( T_('Shelved changes ') )
        self.changes_shelved = QtWidgets.QPlainTextEdit( '' )
        self.changes_shelved.setReadOnly( True )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.label_opened_files )
        self.layout.addWidget( self.opened_files )
        self.layout.addWidget( self.label_changes_pending )
        self.layout.addWidget( self.changes_pending )
        self.layout.addWidget( self.label_changes_shelved )
        self.layout.addWidget( self.changes_shelved )

        self.setLayout( self.layout )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 100*em, 50*ex )

    def setStatus( self, all_opened_files, all_changes_pending, all_changes_shelved ):
        self.opened_files.setPlainText( '\n'.join( ['%(change)s: %(action)s %(clientFile)s' % fstat for fstat in all_opened_files] ) )
        self.changes_pending.setPlainText( '\n'.join( [repr(x) for x in all_changes_pending] ) )
        self.changes_shelved.setPlainText( '\n'.join( [repr(x) for x in all_changes_shelved] ) )
