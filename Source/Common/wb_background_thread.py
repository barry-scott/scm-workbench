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

class BackgroundThread(threading.Thread):
    def __init__( self, app ):
        threading.Thread.__init__( self )

        self.app = app

        self.setDaemon( 1 )
        self.running = 1

        self.work_queue = queue.Queue( maxsize=0 )

    def run( self ):
        while self.running:
            function, args = self.work_queue.get( block=True, timeout=None )
            self.app._debugThreading( 'BackgroundThread.run dispatching %r, %r' % (function, args) )

            try:
                function( *args )

            except:
                self.app.log.exception( 'function failed on background thread' )

    def addWork( self, function, args ):
        self.app._debugThreading( 'BackgroundThread.addWork( %r, %r )' % (function, args) )
        assert self.running
        self.work_queue.put( (function, args), block=False, timeout=None )

    def shutdown( self ):
        self.addWork( self.__shutdown )

    def __shutdown( self ):
        self.running = 0
