'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_debug.py

'''
import time

class WbDebug:
    def __init__( self ):
        self.__speed_start_time = time.time()
        self.__speed_last_event_time = self.__speed_start_time

        self._debug_speed = False
        self._debug_app = False
        self._debug_threading = False
        self._debug_main_window = False
        self._debug_tree_model = False
        self._debug_table_model = False
        self._debug_diff = False

    def setDebug( self, str_options ):
        for option in [s.strip().lower() for s in str_options.split(',')]:
            name = '_debug_%s' % (option.replace( '-', '_' ),)
            if hasattr( self, name ):
                setattr( self, name, True )

            else:
                msg = 'Unknown debug option %s - see wb_debug.py for available options' % (option,)
                print( msg )

    def _debugSpeed( self, msg, start_timer=False ):
        if self._debug_speed:
            now = time.time()
            if start_timer:
                self.__speed_start_time = now
                self.__speed_last_event_time = now

            start_delta = now - self.__speed_start_time
            last_delta = now - self.__speed_last_event_time
            self.__speed_last_event_time = now

            self.log.debug( 'SPEED %.6f %.6f %s' % (start_delta, last_delta, msg,) )

    # wb_app
    def _debugApp( self, msg ):
        if self._debug_app:
            self.log.debug( 'APP %s' % (msg,) )

    # wb_app and wb_background_thread
    def _debugThreading( self, msg ):
        if self._debug_threading:
            self.log.debug( 'THREADING %s' % (msg,) )

    # wb_tree_model
    def _debugTreeModel( self, msg ):
        if self._debug_tree_model:
            self.log.debug( 'TREE-MODEL %s' % (msg,) )

    # wb_table_model
    def _debugTableModel( self, msg ):
        if self._debug_table_model:
            self.log.debug( 'TABLE-MODEL %s' % (msg,) )

    # wb_main_window
    def _debugMainWindow( self, msg ):
        if self._debug_main_window:
            self.log.debug( 'MAIN-WINDOW %s' % (msg,) )

    # wb_diff*
    def _debugDiff( self, msg ):
        if self._debug_diff:
            self.log.debug( 'DIFF %s' % (msg,) )
