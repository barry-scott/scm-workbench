'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_debug.py

'''
import time

#
# wb_git_app.py
#
_debug_app = False
_debug_tree_model = False
_debug_callback = False

def setDebug( str_options ):
    for option in [s.strip().lower() for s in str_options.split(',')]:
        name = '_debug_%s' % (option.replace( '-', '_' ),)
        if name in globals():
            globals()[ name ] = True
        else:
            print( 'Unknown debug option %s - see wb_git_debug.py for available options' % (option,) )

class WbGitDebugMixin:
    def __init__( self ):
        self.__speed_start_time = time.time()
        self.__speed_last_event_time = self.__speed_start_time

    def _debugSpeed( self, msg, start_timer=False ):
        if _debug_speed:
            now = time.time()
            if start_timer:
                self.__speed_start_time = now
                self.__speed_last_event_time = now

            start_delta = now - self.__speed_start_time
            last_delta = now - self.__speed_last_event_time
            self.__speed_last_event_time = now

            self.log.debug( 'SPEED %.6f %.6f %s' % (start_delta, last_delta, msg,) )

    # wb_git_app
    def _debugApp( self, msg ):
        if _debug_app:
            self.log.debug( 'APP %s' % (msg,) )

    def _debugCallback( self, msg ):
        if _debug_callback:
            self.log.debug( 'CALLBACK %s' % (msg,) )

    # wb_git_tree_model
    def _debugTreeModel( self, msg ):
        if _debug_tree_model:
            self.log.debug( 'TREE-MODEL %s' % (msg,) )
