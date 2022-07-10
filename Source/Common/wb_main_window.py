'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_window_main.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtCore

class WbMainWindow(QtWidgets.QMainWindow):
    focus_is_in_names = ('tree', 'table')

    def __init__( self, app, debug_fn, parent=None ):
        self.app = app
        self.log = self.app.log
        self.debugLog = app.debug_options.debugLogMainWindow

        super().__init__( parent )

        self.icon_size = QtCore.QSize( 32, 32 )

        # list of all the WbActionState for the menus and toolbars
        self.__action_state_manager = WbActionStateManager( self.debugLog )

        self.__focus_is_in = self.focus_is_in_names[0]

        # Often the rest of init has to be done after the widgets are rendered
        # for example to set focus on a widget
        self.__timer_init = QtCore.QTimer()
        self.__timer_init.timeout.connect( self.__completeInit )
        self.__timer_init.setSingleShot( True )
        self.__timer_init.start( 0 )

    def __completeInit( self ):
        self.__timer_init = None

        self.app.wrapWithThreadSwitcher( self.completeInit, 'main_window.completeInit' )()

    def completeInit( self ):
        pass

    def close( self ):
        super().close()

    #------------------------------------------------------------
    def setFocusIsIn( self, widget_type ):
        assert widget_type in self.focus_is_in_names
        self.__focus_is_in = widget_type

    def focusIsIn( self ):
        assert self.__focus_is_in in self.focus_is_in_names
        return self.__focus_is_in

    #------------------------------------------------------------
    # override to do what is required on app becoming active.
    def appActiveHandler( self ):
        pass

    def updateEnableStates( self, force_disabled=False ):
        self.__action_state_manager.update( force_disabled )

    def setupMenuBar( self, menu_bar ):
        pass

    def setupToolBar( self, tool_bar ):
        pass

    def setupStatusBar( self, status_bar ):
        pass

    def _addMenu( self, menu, name, handler, enabler=None, icon_name=None, checker=None, group=None, role=QtWidgets.QAction.MenuRole.NoRole ):
        if icon_name is None:
            icon_name = 'toolbar_images/blank.png'

        icon = self.app.getQIcon( icon_name )
        action = menu.addAction( icon, name )

        if handler is not None:
            handler = self.app.wrapWithThreadSwitcher( handler, 'menu: %s' % (name,) )

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

        if group is not None:
            group.addAction( action )

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
            icon = self.app.getQIcon( icon_name )
            action = bar.addAction( icon, name )

        if handler is not None:
            handler = self.app.wrapWithThreadSwitcher( handler, 'toolbar: %s' % (name,) )

            if checker is not None:
                action.toggled.connect( handler )

            else:
                action.triggered.connect( handler )

        if enabler is not None:
            self.__action_state_manager.addEnabler( action, enabler )

        if checker is not None:
            action.setCheckable( True )
            self.__action_state_manager.addChecker( action, checker )

class WbActionStateManager:
    def __init__( self, debug_fn ):
        self.debugLog = debug_fn

        self.__all_action_enablers = []
        self.__all_action_checkers = []

        self.__update_running = False

    def addEnabler( self, action, enabler_handler ):
        self.__all_action_enablers.append( WbActionEnabledState( action, enabler_handler ) )

    def addChecker( self, action, checker_handler ):
        self.__all_action_checkers.append( WbActionCheckedState( action, checker_handler ) )

    def update( self, force_disabled ):
        if self.__update_running:
            return

        self.__update_running = True
        self.debugLog( 'WbActionState.update running' )

        # use a cache to avoid calling state queries more then once on any one update
        cache = {}
        for enabler in self.__all_action_enablers:
            enabler.setState( cache, force_disabled=force_disabled )

        for checker in self.__all_action_checkers:
            checker.setState( cache, force_disabled=False )

        self.debugLog( 'WbActionState.update done' )
        self.__update_running = False

class WbActionSetStateBase:
    def __init__( self, action, handler ):
        self.action = action
        self.handler = handler
        self.__key = self.handler.__name__

    def __repr__( self ):
        return '<WbActionEnabledState: %r>' % (self.enabler_handler,)

    def setState( self, cache, force_disabled ):
        state = False if force_disabled else self.__callHandler( cache )
        assert state in (True, False), 'setState "%r" return %r not bool' % (self.handler, state)

        self.setActionState( state )

    def setActionState( self, state ):
        raise NotImplementedError()

    def __callHandler( self, cache ):
        if self.__key not in cache:
            cache[ self.__key ] = self.handler()

        return cache[ self.__key ]

class WbActionEnabledState(WbActionSetStateBase):
    def __init__( self, action, enabler_handler ):
        super().__init__( action, enabler_handler )

    def __repr__( self ):
        return '<WbActionEnabledState: %r>' % (self.handler,)

    def setActionState( self, state ):
        self.action.setEnabled( state )

class WbActionCheckedState(WbActionSetStateBase):
    def __init__( self, action, checker_handler ):
        super().__init__( action, checker_handler )

    def __repr__( self ):
        return '<WbActionCheckedState: %r>' % (self.handler,)

    def setActionState( self, state ):
        self.action.setChecked( state )
