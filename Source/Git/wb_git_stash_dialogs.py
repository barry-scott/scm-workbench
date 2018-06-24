'''
 ====================================================================
 Copyright (c) 2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_stash_dialogs.py

'''
from PyQt5 import QtWidgets

import wb_table_base
import wb_dialog_bases

def U_( s: str ) -> str:
    return s

class WbGitStashSave(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, default_message ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Stash save - %s') % (' '.join( app.app_name_parts ),) )

        self.message = wb_dialog_bases.WbLineEdit( default_message )

        em = self.fontMetrics().width( 'M' )
        self.addRow( T_('Save message'), self.message, min_width=em*50 )
        self.addButtons()

    def getMessage( self ):
        value = self.message.value()
        if value == '':
            return None

        return value

class WbGitStashPick(QtWidgets.QDialog):
    def __init__( self, app, main_window, all_stashes ):
        super().__init__( main_window )

        self.app = app
        self.stash_id = None

        em = self.fontMetrics().width( 'M' )
        self.resize( 70*em, 30*em )

        self.setWindowTitle( T_('Git Stash list - %s') % (' '.join( app.app_name_parts ),) )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = self.buttons.addButton( self.buttons.Ok )
        self.ok_button.setText( T_('Stash Pop') )
        self.buttons.addButton( self.buttons.Cancel )

        self.stashes_table = wb_table_base.WbTableView(
                self.app,
                [wb_table_base.TableColumn( U_('Stash ID'), 10, 'L', 'stash_id' )
                ,wb_table_base.TableColumn( U_('Branch'),   10, 'L', 'stash_branch' )
                ,wb_table_base.TableColumn( U_('Message'),  50, 'L', 'stash_message', '1line' )] )
        self.stashes_table.setSelectionChangedCallback( self.selectionChanged )
        self.stashes_table.loadRows( all_stashes )

        self.stashes_table.setSelectionBehavior( self.stashes_table.SelectRows )
        self.stashes_table.setSelectionMode( self.stashes_table.SingleSelection )

        self.vert_layout = QtWidgets.QVBoxLayout()

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.vert_layout.addWidget( self.stashes_table )
        self.vert_layout.addWidget( self.buttons )

        self.setLayout( self.vert_layout )

    def setStashId( self, stash_id ):
        self.stash_id = stash_id

        self.ok_button.setEnabled( self.stash_id is not None )

    def getStashId( self ):
        return self.stash_id

    def selectionChanged( self, stash_info ):
        self.setStashId( stash_info.stash_id )
