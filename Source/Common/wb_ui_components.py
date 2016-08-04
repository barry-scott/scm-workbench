'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_ui_components.py.py

'''
import difflib

import wb_diff_unified_view
import wb_diff_side_by_side_view

class WbMainWindowComponents:
    def __init__( self, scm_type ):
        self.scm_type = scm_type

        self.top_window = None
        self.main_window = None
        self.table_view = None
        self.app = None
        self._debug = None

        self.all_menus = []
        self.all_toolbars = []

        self.table_context_menu = None
        self.tree_context_menu = None

    def setTopWindow( self, top_window ):
        self.top_window = top_window

        # short cuts
        self.setStatusGeneral = top_window.setStatusGeneral
        self.setStatusAction =  top_window.setStatusAction

        self.progress =         top_window.progress

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

    def setupDebug( self ):
        self._debug = self.main_window.app._debugMainWindow

    def getTableContextMenu( self ):
        return self.table_context_menu

    def getTreeContextMenu( self ):
        return self.tree_context_menu

    def showUiComponents( self ):
        for menu in self.all_menus:
            menu.menuAction().setVisible( True )

        for toolbar in self.all_toolbars:
            toolbar.setVisible( True )

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

    # qqqzzz: is this right to put here?
    def tableSelectedAllFileStates( self ):
        if self.table_view is None:
            return []

        return self.table_view.selectedAllFileStates()

    # ------------------------------------------------------------
    def diffTwoFiles( self, title, old_lines, new_lines, header_left, header_right ):
        if self.app.prefs.view.isDiffUnified():
            all_lines = list( difflib.unified_diff( old_lines, new_lines ) )

            self.showDiffText( title, all_lines )

        elif self.app.prefs.view.isDiffSideBySide():
            window = wb_diff_side_by_side_view.DiffSideBySideView(
                        self.app, None,
                        title,
                        old_lines, header_left,
                        new_lines, header_right )
            window.show()

    def showDiffText( self, title, all_lines ):
        assert type(all_lines) == list

        window = wb_diff_unified_view.WbDiffViewText( self.app, title, self.main_window.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( all_lines )
        window.show()
