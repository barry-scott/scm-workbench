'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_window_chrome_setup.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbMainWindow(QtWidgets.QMainWindow):
    def __init__( self, app, image_store, debug_fn, parent=None ):
        self.app = app
        self.log = self.app.log
        self._debug = app._debugMainWindow

        super().__init__( parent )

        self.__image_store = image_store
        self.icon_size = QtCore.QSize( 32, 32 )

        # list of all the WbActionState for the menus and toolbars
        self.__action_state_manager = WbActionStateManager( self._debug )

    # override to do what is required on app becoming active.
    def appActiveHandler( self ):
        pass

    def getQIcon( self, icon_name ):
        return self.__image_store.getQIcon( icon_name )

    def updateEnableStates( self ):
        self.__action_state_manager.update()

    def setupMenuBar( self, menu_bar ):
        pass

    def setupToolBar( self, tool_bar ):
        pass

    def setupStatusBar( self, status_bar ):
        pass

    def _addMenu( self, menu, name, handler, enabler=None, icon_name=None, checker=None, role=QtWidgets.QAction.NoRole ):
        if icon_name is None:
            action = menu.addAction( name )
        else:
            icon = self.getQIcon( icon_name )
            action = menu.addAction( icon, name )

        if handler is not None:
            if checker is not None:
                action.toggled.connect( handler )

            else:
                action.triggered.connect( handler )

        if role is not None:
            action.setMenuRole( role )

        if enabler is not None:
            self.__action_state_manager.addEnabler( action, enabler )

        if checker is not None:
            action.setCheckable( True )
            self.__action_state_manager.addChecker( action, checker )

    def _addToolBar( self, name, style=None ):
        bar = self.addToolBar( name )
        bar.setIconSize( self.icon_size )
        if style is not None:
            bar.setStyleSheet( 'QToolButton{%s}' % (style,) )
        return bar

    def _addTool( self, bar, name, handler, enabler=None, icon_name=None, checker=None ):
        if icon_name is None:
            action = bar.addAction( name )

        else:
            icon = self.getQIcon( icon_name )
            action = bar.addAction( icon, name )

        if handler is not None:
            if checker is not None:
                action.toggled.connect( handler )

            else:
                action.triggered.connect( handler )

        if enabler is not None:
            self.__action_state_manager.addEnabler( action, enabler )

        if checker is not None:
            action.setCheckable( True )
            self.__action_state_manager.addChecker( action, enabler )

class WbActionStateManager:
    def __init__( self, debug_fn ):
        self._debug = debug_fn

        self.__all_action_enablers = []
        self.__all_action_checkers = []

        self.__update_running = False

    def addEnabler( self, action, enabler_handler ):
        self.__all_action_enablers.append( WbActionEnabledState( action, enabler_handler ) )

    def addChecker( self, action, checker_handler ):
        self.__all_action_checkers.append( WbActionCheckedState( action, checker_handler ) )

    def update( self ):
        if self.__update_running:
            return

        self.__update_running = True
        self._debug( 'WbActionState.update running' )

        # use a cache to avoid calling state queries more then once on any one update
        cache = {}
        for enabler in self.__all_action_enablers:
            enabler.setEnableState( cache )

        for checker in self.__all_action_checkers:
            checker.setCheckedState( cache )

        self._debug( 'WbActionState.update done' )
        self.__update_running = False

class WbActionEnabledState:
    def __init__( self, action, enabler_handler ):
        self.action = action
        self.enabler_handler = enabler_handler

    def __repr__( self ):
        return '<WbActionEnabledState: %r>' % (self.enabler_handler,)

    def setEnableState( self, cache ):
        self.action.setEnabled( self.enabler_handler( cache ) )

class WbActionCheckedState:
    def __init__( self, action, checker_handler ):
        self.action = action
        self.checker_handler = checker_handler

    def __repr__( self ):
        return '<WbActionCheckedState: %r>' % (self.checker_handler,)

    def setCheckedState( self, cache ):
        state = self.checker_handler( cache )
        self.action.setChecked( state )
