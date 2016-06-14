'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_ui_components.py.py

'''
import wb_hg_project

class HgMainWindowComponents:
    def __init__( self ):
        self.main_window = None

        self.all_menus = []
        self.all_toolbars = []

        self.hg_table_context_menu = None
        self.hg_tree_context_menu = None

    def setMainWindow( self, main_window ):
        self.main_window = main_window

    def getTableContextMenu( self ):
        return self.hg_table_context_menu

    def getTreeContextMenu( self ):
        return self.hg_tree_context_menu

    def showUiComponents( self ):
        for menu in self.all_menus:
            menu.menuAction().setVisible( True )

        for toolbar in self.all_toolbars:
            self.main_window.addToolBar( toolbar )

    def hideUiComponents( self ):
        for menu in self.all_menus:
            menu.menuAction().setVisible( False )

        for toolbar in self.all_toolbars:
            self.main_window.removeToolBar( toolbar )

    def setupMenuBar( self, mb, addMenu ):
        pass

    def setupToolBar( self, addToolBar, addTool ):
        pass

    def setupTableContextMenu( self, m, addMenu ):
        self.hg_table_context_menu = m

    def setupTreeContextMenu( self, m, addMenu ):
        self.hg_tre_context_menu = m
