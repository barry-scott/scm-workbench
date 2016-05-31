'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_window_chrome_setup.py

'''
from PyQt5 import QtCore

class WbWindowChromeSetup:
    def __init__( self, image_store ):
        self.__image_store = image_store
        self.icon_size = QtCore.QSize( 32, 32 )

        # list of all the WbActionEnableState for the menus and toolbars
        self.__enable_state_manager = WbActionEnableStateManager( self.app )

    def updateEnableStates( self ):
        self.__enable_state_manager.update()

    def setupMenuBar( self, menu_bar ):
        pass

    def setupToolBar( self, tool_bar ):
        pass

    def setupStatusBar( self, status_bar ):
        pass

    def _addMenu( self, menu, name, handler, enabler=None, icon_name=None, role=None ):
        if icon_name is None:
            action = menu.addAction( name )
        else:
            icon = self.__image_store.getQIcon( icon_name )
            action = menu.addAction( icon, name )

        if handler is not None:
           action.triggered.connect( handler )

        if role is not None:
            action.setMenuRole( role )

        if enabler is not None:
            self.__enable_state_manager.add( action, enabler )

    def _addToolBar( self, name ):
        bar = self.addToolBar( name )
        bar.setIconSize( self.icon_size )
        return bar

    def _addTool( self, bar, name, handler, enabler=None, icon_name=None ):
        if icon_name is None:
            action = bar.addAction( name )

        else:
            icon = self.__image_store.getQIcon( icon_name )
            action = bar.addAction( icon, name )

        action.triggered.connect( handler )
        if enabler is not None:
            self.__enable_state_manager.add( action, enabler )

class WbActionEnableStateManager:
    def __init__( self, app ):
        self._debug = app._debugMainWindow

        self.__all_action_enablers = []

        self.__update_running = False

    def add( self, action, enable_handler ):
        self.__all_action_enablers.append( WbActionEnableState( action, enable_handler ) )

    def update( self ):
        if self.__update_running:
            return

        self.__update_running = True
        self._debug( 'WbActionEnableState.update running' )

        # use a cache to avoid calling state queries more then once on any one update
        cache = {}
        for enabler in self.__all_action_enablers:
            enabler.setEnableState( cache )

        self._debug( 'WbActionEnableState.update done' )
        self.__update_running = False

class WbActionEnableState:
    def __init__( self, action, enable_handler ):
        self.action = action
        self.enable_handler = enable_handler

    def setEnableState( self, cache ):
        self.action.setEnabled( self.enable_handler( cache ) )
