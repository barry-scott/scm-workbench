'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_background_thread.py

'''
import threading
import queue
import types

from PyQt6 import QtCore

#
#   Decorator used to set the requires_thread_switcher property on a function
#
_requires_thread_switcher_attr = 'requires_thread_switcher'
def thread_switcher( fn ):
    setattr( fn, _requires_thread_switcher_attr, True )
    return fn

# predicate to detect function that requires a ThreadSwitchScheduler
def requiresThreadSwitcher( fn ):
    #print( 'qqq requiresThreadSwitcher( %r ) -> %r' % (fn, getattr( fn, _requires_thread_switcher_attr, False )) )
    return getattr( fn, _requires_thread_switcher_attr, False )

#------------------------------------------------------------
class MarshalledCall:
    def __init__( self, function, args ):
        self.function = function
        self.args = args

    def __call__( self ):
        self.function( *self.args )

    def __repr__( self ):
        return '<MarshalledCall: fn=%s nargs=%d>' % (self.function.__name__, len(self.args))

class BackgroundThread(threading.Thread):
    def __init__( self, app ):
        super().__init__()

        self.app = app

        self.setDaemon( 1 )
        self.running = 1

        self.work_queue = queue.Queue( maxsize=0 )

    def run( self ):
        while self.running:
            function = self.work_queue.get( block=True, timeout=None )
            self.app.debug_options.debugLogThreading( 'BackgroundThread.run dispatching %r' % (function,) )

            try:
                function()

            except:
                self.app.log.exception( 'function failed on background thread' )

    def addWork( self, function, args ):
        self.app.debug_options.debugLogThreading( 'BackgroundThread.addWork( %r, %r )' % (function, args) )
        assert self.running
        self.work_queue.put( MarshalledCall( function, args ), block=False, timeout=None )

    def shutdown( self ):
        self.addWork( self.__shutdown )

    def __shutdown( self ):
        self.running = 0

#
#   BackgroundWorkMixin
#
#   Add features that allow processing to switch
#   easily from foreground to background threads
#
#   runInBackground - call function on the background thread
#   runInForeground - call function on the foreground thread
#
#   deferRunInForeground
#       - used to move a callback made in the background
#         into the foreground with the args provided in the
#         background call back.
#
#   threadSwitcher - call function that is allowed to yield to move between threads.
#       - function starts in the foreground
#       - switch to the background by yield switchToBackground
#       - switch to the foreground by yield switchToForeground
#

# assumes that self is app
class BackgroundWork(QtCore.QObject):
    foregroundProcessSignal = QtCore.pyqtSignal( [MarshalledCall] )

    def __init__( self, app ):
        super().__init__()

        self.app = app

        self.foreground_thread = threading.currentThread()
        self.background_thread = BackgroundThread( self.app )

    def startBackgroundThread( self ):
        self.foregroundProcessSignal.connect( self.__runInForeground, type=QtCore.Qt.ConnectionType.QueuedConnection )
        self.background_thread.start()

    def isForegroundThread( self ):
        # return true if the caller is running on the main thread
        return self.foreground_thread is threading.currentThread()

    def deferRunInForeground( self, function ):
        return DeferRunInForeground( self.app, function )

    def runInBackground( self, function, args ):
        self.app.debug_options.debugLogThreading( 'runInBackground( %r, %r )' % (function, args) )
        self.background_thread.addWork( function, args )

    def runInForeground( self, function, args ):
        # cannot call logging from here as this will cause the log call to be marshelled
        self.foregroundProcessSignal.emit( MarshalledCall( function, args ) )

    def wrapWithThreadSwitcher( self, function, reason='' ):
        if requiresThreadSwitcher( function ):
            return ThreadSwitchScheduler( self.app, function, reason )

        else:
            return function

    # alias that are better names when used from the threadSwitcher function
    switchToForeground = runInForeground
    switchToBackground = runInBackground

    def __runInForeground( self, function ):
        self.app.debug_options.debugLogThreading( '__runInForeground( %r )' % (function,) )

        try:
            function()

        except:
            self.app.log.exception( 'foregroundProcess function failed' )

class DeferRunInForeground:
    def __init__( self, app, function ):
        self.app = app
        self.function = function

    def __call__( self, *args ):
        self.app.runInForeground( self.function, args )

class ThreadSwitchScheduler:
    next_instance_id = 0
    def __init__( self, app, function, reason ):
        self.app = app
        self.function = function
        self.reason = reason
        self.debugLogThreading = self.app.debug_options.debugLogThreading
        ThreadSwitchScheduler.next_instance_id += 1
        self.instance_id = self.next_instance_id

    def __call__( self, *args, **kwds ):
        self.debugLogThreading( 'ThreadSwitchScheduler(%d:%s): start %r( %r, %r )' % (self.instance_id, self.reason, self.function, args, kwds) )

        #pylint disable=bare-except
        try:
            # call the function
            result = self.function( *args, **kwds )

            # did the function run or make a generator?
            if type(result) != types.GeneratorType:
                self.debugLogThreading( 'ThreadSwitchScheduler(%d:%s): done (not GeneratorType)' % (self.instance_id, self.reason) )
                # it ran - we are all done
                return

            # step the generator
            self.queueNextSwitch( result )

        except:
            self.app.log.exception( 'ThreadSwitchScheduler(%d:%s)' % (self.instance_id, self.reason) )

    def queueNextSwitch( self, generator ):
        self.debugLogThreading( 'ThreadSwitchScheduler(%d:%s): generator %r' % (self.instance_id, self.reason, generator) )
        # result tells where to schedule the generator to next
        try:
            where_to_go_next = next( generator )

        except StopIteration:
            # no problem all done
            self.debugLogThreading( 'ThreadSwitchScheduler(%d:%s): done (StopIteration)' % (self.instance_id, self.reason) )
            return

        # will be one of app.runInForeground or app.runInForeground
        self.debugLogThreading( 'ThreadSwitchScheduler(%d:%s): next %r' % (self.instance_id, self.reason, where_to_go_next) )
        where_to_go_next( self.queueNextSwitch, (generator,) )

#------------------------------------------------------------
#
#    Used to allow a call to function on the background thread
#    to block until the result return on the main thread is available
#
#------------------------------------------------------------
class GetReturnFromCallingFunctionOnMainThread:
    def __init__( self, app, function ):
        self.app = app
        self.function = function

        self.cv = threading.Condition()
        self.result = None

    def __call__( self, *args ):
        self.app.log.debug( 'CallFunctionOnMainThread.__call__ calling %r' % self.function )
        self.cv.acquire()

        self.app.runInForeground( self.__onMainThread, args )

        self.cv.wait()
        self.cv.release()

        self.app.log.debug( 'CallFunctionOnMainThread.__call__ returning %r' % self.function )
        return self.result

    def __onMainThread( self, *args ):
        self.app.log.debug( 'CallFunctionOnMainThread._onMainThread calling %r' % self.function )
        try:
            self.result = self.function( *args )

        finally:
            pass

        self.cv.acquire()
        self.cv.notify()
        self.cv.release()

        self.app.log.debug( 'CallFunctionOnMainThread._onMainThread returning %r' % self.function )
