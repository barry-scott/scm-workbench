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

from PyQt5 import QtCore

#
#   Decorator used to set the requires_thread_switcher property on a function
#
_requires_thread_switcher_attr = 'requires_thread_switcher'
def thread_switcher( fn ):
    setattr( fn, _requires_thread_switcher_attr, True )
    return fn

# predicate to detect function that requires a ThreadSwitchScheduler
def requiresThreadSwitcher( fn ):
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
        threading.Thread.__init__( self )

        self.app = app

        self.setDaemon( 1 )
        self.running = 1

        self.work_queue = queue.Queue( maxsize=0 )

    def run( self ):
        while self.running:
            function = self.work_queue.get( block=True, timeout=None )
            self.app._debug_options._debugThreading( 'BackgroundThread.run dispatching %r' % (function,) )

            try:
                function()

            except:
                self.app.log.exception( 'function failed on background thread' )

    def addWork( self, function, args ):
        self.app._debug_options._debugThreading( 'BackgroundThread.addWork( %r, %r )' % (function, args) )
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
class BackgroundWorkMixin:
    foregroundProcessSignal = QtCore.pyqtSignal( [MarshalledCall] )

    def __init__( self ):
        self.foreground_thread = threading.currentThread()
        self.background_thread = BackgroundThread( self )

        self.foregroundProcessSignal.connect( self.__runInForeground, type=QtCore.Qt.QueuedConnection )

    def isForegroundThread( self ):
        # return true if the caller is running on the main thread
        return self.foreground_thread is threading.currentThread()

    def deferRunInForeground( self, function ):
        return DeferRunInForeground( self, function )

    def runInBackground( self, function, args ):
        self._debug_options._debugThreading( 'runInBackground( %r, %r )' % (function, args) )
        self.background_thread.addWork( function, args )

    def runInForeground( self, function, args ):
        # cannot call logging from here as this will cause the log call to be marshelled
        self.foregroundProcessSignal.emit( MarshalledCall( function, args ) )

    def wrapWithThreadSwitcher( self, function ):
        if requiresThreadSwitcher( function ):
            return ThreadSwitchScheduler( self, function )

        else:
            return function

    # alias that are better names when used from the threadSwitcher function
    switchToForeground = runInForeground
    switchToBackground = runInBackground

    def __runInForeground( self, function ):
        self._debug_options._debugThreading( '__runInForeground( %r )' % (function,) )

        try:
            function()

        except:
            self.log.exception( 'foregroundProcess function failed' )

class DeferRunInForeground:
    def __init__( self, app, function ):
        self.app = app
        self.function = function

    def __call__( self, *args ):
        self.app.runInForeground( self.function, args )

class ThreadSwitchScheduler:
    def __init__( self, app, function ):
        self.app = app
        self.function = function
        self._debugThreading = self.app._debug_options._debugThreading

    def __call__( self, *args, **kwds ):
        self._debugThreading( 'ThreadSwitchScheduler: __call__( %r, %r )' % (args, kwds) )

        try:
            # call the function
            result = self.function( *args, **kwds )

            # did the function run or make a generator?
            if type(result) != types.GeneratorType:
                # it ran - we are all done
                return

            # step the generator
            self.queueNextSwitch( result )

        except:
            self.app.log.exception( 'ThreadSwitchScheduler' )

    def queueNextSwitch( self, generator ):
        self._debugThreading( 'queueNextSwitch<%r>()' % (generator,) )

        # result tells where to schedule the generator to next
        try:
            where_to_go_next = next( generator )
            self._debugThreading( 'queueNextSwitch<%r>() next=>%r' % (generator, where_to_go_next) )

        except StopIteration:
            # no problem all done
            return

        # will be one of app.runInForeground or app.runInForeground
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
