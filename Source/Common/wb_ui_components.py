'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_ui_components.py

'''
class WbMainWindowComponents:
    def __init__( self, scm_type, factory ):
        self.scm_type = scm_type
        self.factory = factory

        self.top_window = None
        self.main_window = None
        self.table_view = None
        self.app = None
        self._debug = None

        self.all_menus = []
        self.all_toolbars = []

        self.table_context_menu = None
        self.tree_context_menu = None

        self.ui_actions = factory.uiActions()

    # ---- called from main_window ----
    def setTopWindow( self, top_window ):
        self.top_window = top_window

        # short cuts
        self.setStatusGeneral = top_window.setStatusGeneral
        self.setStatusAction =  top_window.setStatusAction

        self.progress =         top_window.progress

        self.ui_actions.setTopWindow( top_window )

    # ---- called from main_window ----
    def setMainWindow( self, main_window, table_view ):
        assert main_window is not None
        self.main_window = main_window

        self.table_view = table_view

        self.app = self.main_window.app
        self.log = self.app.log

        # shorts cut to main window functions
        self.switchToForeground = self.app.switchToForeground
        self.switchToBackground = self.app.switchToBackground
        self.deferRunInForeground = self.app.deferRunInForeground

        self.setupDebug()

        self.ui_actions.setMainWindow( main_window, table_view )

    def setupDebug( self ):
        self._debug = self.main_window.app._debug_options._debugMainWindow

    def getAllPerferenceTabs( self ):
        return []

    def getTableContextMenu( self ):
        return self.table_context_menu

    def getTreeContextMenu( self ):
        return self.tree_context_menu

    def showUiComponents( self ):
        for menu in self.all_menus:
            menu.menuAction().setVisible( True )

        for toolbar in self.all_toolbars:
            toolbar.setVisible( True )

        self.table_view.setVisibleColumns( self.all_visible_table_columns )

    def hideUiComponents( self ):
        for menu in self.all_menus:
            menu.menuAction().setVisible( False )

        for toolbar in self.all_toolbars:
            toolbar.setVisible( False )

    def setupMenuBar( self, mb, addMenu ):
        pass

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        pass

    def setupToolBarAtRight( self, addToolBar, addTool ):
        pass

    def setupTableContextMenu( self, m, addMenu ):
        self.table_context_menu = m

    def setupTreeContextMenu( self, m, addMenu ):
        self.tree_context_menu = m

    # ------------------------------------------------------------
    def isScmTypeActive( self ):
        return self.main_window.isScmTypeActive( self.scm_type )

