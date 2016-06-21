'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_ui_components.py.py

'''
class WbMainWindowComponents:
    def __init__( self, scm_type ):
        self.scm_type = scm_type

        self.main_window = None
        self.app = None
        self._debug = None

        self.commit_dialog = None

        self.all_menus = []
        self.all_toolbars = []

        self.table_context_menu = None
        self.tree_context_menu = None

    def setMainWindow( self, main_window ):
        self.main_window = main_window

        self.app = self.main_window.app
        self.log = self.app.log

        self.setStatusText = self.main_window.setStatusText

        # shorts cut to main window functions
        self.setStatusText = self.main_window.setStatusText

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
        self.main_window.isScmTypeActive( self.scm_type )

    def tableSelectedAllFileStates( self ):
        tree_node = self.selectedProjectTreeNode()
        if tree_node is None:
            return []

        all_names = self.main_window._tableSelectedFiles()
        if len(all_names) == 0:
            return []

        scm_project = tree_node.project
        relative_folder = tree_node.relative_folder()

        return [scm_project.getFileState( relative_folder / name ) for name in all_names]
