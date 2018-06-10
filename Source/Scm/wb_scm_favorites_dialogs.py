'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_favorites_dialogs.py

'''
from PyQt5 import QtWidgets

import wb_dialog_bases

class WbFavoriteAddDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, project_name, path, all_existing_menus ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( T_('Add Favorite - %s') % (' '.join( app.app_name_parts ),) )

        self.all_existing_menus = all_existing_menus
        self.project_name = project_name
        self.favorite_path = path

        self.menu = QtWidgets.QLineEdit()
        self.menu.textChanged.connect( self.menuTextChanged )

        self.menu.setText( '%s;%s' % (self.project_name, self.favorite_path) )

        self.menuTextChanged( '' )

        em = self.fontMetrics().width( 'M' )
        self.addRow( T_('Favorite project'), self.project_name, min_width=em*80 )
        self.addRow( T_('Favorite path'), self.favorite_path, min_width=em*80 )
        self.addRow( T_('Favorite menu'), self.menu, min_width=em*80 )
        self.addButtons()

    def menuTextChanged( self, text ):
        self.ok_button.setEnabled( self.getMenu() not in self.all_existing_menus )

    def getMenu( self ):
        return self.menu.text().strip()
