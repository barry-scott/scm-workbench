'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_debug.py

'''
import time
class WbDebugOption:
    __slots__ = ('__enabled', '_log', '__name', '__fmt')

    def __init__( self, log, name ):
        assert log is not None
        self.__enabled = False
        self._log = log
        self.__name = name
        self.__fmt = '%s %%s' % (name,)

    def __repr__( self ):
        return '<WbDebugOption: %s enabled=%r>' % (self.__name, self.isEnabled())

    def enable( self, state=True ):
        self.__enabled = state

    def isEnabled( self ):
        return self.__enabled

    def __call__( self, msg ):
        if self.__enabled:
            self._log.debug( self.__fmt % (msg,) )

class WbDebugSpeedOption(WbDebugOption):
    __slots__ = ('__speed_start_time', '__speed_last_event_time')

    def __init__( self, log, name ):
        super().__init__( log, name )
        self.__speed_start_time = time.time()
        self.__speed_last_event_time = self.__speed_start_time

    def __call__( self, msg, start_timer=False ):
        if self.isEnabled():
            now = time.time()
            if start_timer:
                self.__speed_start_time = now
                self.__speed_last_event_time = now

            start_delta = now - self.__speed_start_time
            last_delta = now - self.__speed_last_event_time
            self.__speed_last_event_time = now

            self._log.debug( 'SPEED %.6f %.6f %s' % (start_delta, last_delta, msg,) )

class WbDebug:
    def __init__( self, log ):
        self._log = log
        self.debugLogSpeed = WbDebugSpeedOption( self._log, 'SPEED' )
        self.debugLogApp = self.addDebugOption( 'APP' )
        self.debugLogThreading = self.addDebugOption( 'THREADING' )
        self.debugLogMainWindow = self.addDebugOption( 'MAIN WINDOW' )
        self.debugLogTreeModel = self.addDebugOption( 'TREE MODEL' )
        self.debugLogTreeModelNode = self.addDebugOption( 'TREE MODEL NODE' )
        self.debugLogTableModel = self.addDebugOption( 'TABLE MODEL' )
        self.debugLogDiff = self.addDebugOption( 'DIFF' )

    def setDebug( self, str_options ):
        for option in [s.strip().lower() for s in str_options.split(',')]:
            name = 'debugLog%s' % (''.join( s.capitalize() for s in option.lower().split('-') ),)
            if hasattr( self, name ):
                getattr( self, name ).enable( True )

            else:
                msg = 'Unknown debug option %s - see wb_debug.py for available options' % (option,)
                print( msg )

    def addDebugOption( self, name ):
        return WbDebugOption( self._log, name )
