'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_favorites_dialogs.py

'''
from PyQt6 import QtWidgets

import wb_dialog_bases

class WbFavoriteDialogBase(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, project_name, path, all_existing_menus ):
        self.app = app

        super().__init__( parent )

        self.all_existing_menus = all_existing_menus
        self.project_name = project_name
        self.favorite_path = path
        self.menu_text_original = ''

        self.menu = QtWidgets.QLineEdit()
        self.menu.textChanged.connect( self.menuTextChanged )

        self.menuTextChanged( '' )

        em = self.fontMetrics().horizontalAdvance( 'M' )
        self.addRow( T_('Favorite project'), self.project_name, min_width=em*80 )
        self.addRow( T_('Favorite path'), self.favorite_path, min_width=em*80 )
        self.addRow( T_('Favorite menu'), self.menu, min_width=em*80 )
        self.addButtons()

    def menuTextChanged( self, text ):
        menu_text = self.getMenu()
        self.ok_button.setEnabled( menu_text not in self.all_existing_menus and menu_text != self.menu_text_original )

    def getMenu( self ):
        return self.menu.text().strip()

class WbFavoriteAddDialog(WbFavoriteDialogBase):
    def __init__( self, app, parent, project_name, path, all_existing_menus ):
        super().__init__( app, parent, project_name, path, all_existing_menus )

        self.setWindowTitle( T_('Add Favorite - %s') % (' '.join( app.app_name_parts ),) )
        self.menu.setText( '%s;%s' % (self.project_name, self.favorite_path) )

class WbFavoriteEditDialog(WbFavoriteDialogBase):
    def __init__( self, app, parent, favorite, all_existing_menus ):
        project = app.prefs.getProjectByPath( favorite.project_path )
        super().__init__( app, parent, project.name, favorite.path, all_existing_menus )

        self.setWindowTitle( T_('Edit Favorite - %s') % (' '.join( app.app_name_parts ),) )
        self.menu.setText( favorite.menu )
        self.menu_text_original = favorite.menu
