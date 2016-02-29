'''
 ====================================================================
 Copyright (c) 2003-2015 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_app.py

    Based on code from git WorkBench

'''
import sys
import os
import stat
import types
import logging
import tempfile
import threading
import inspect
import gettext
import queue

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_git_main_window
import wb_git_platform_specific
import wb_shell_commands
import wb_git_preferences
import wb_git_exceptions
import wb_git_debug

qt_event_type_names = {}
for name in dir(QtCore.QEvent):
    value = getattr( QtCore.QEvent, name )
    if isinstance( value, int ):
        qt_event_type_names[ int(value) ] = name

class WbGit_App(QtWidgets.QApplication, wb_git_debug.WbGitDebugMixin):
    def __init__( self, args ):
        self.main_window = None
        QtWidgets.QApplication.__init__( self, [sys.argv[0]] )

        wb_git_debug.WbGitDebugMixin.__init__( self )

        self.may_quit = False

        self.args = args

        self.startup_dir = os.getcwd()

        self.all_temp_files = []
        self.all_processes = []

        wb_git_platform_specific.setupPlatform()
        #wb_shell_commands.setupCommands()

        # on the Mac the app's cwd is the resource folder
        if sys.platform == 'darwin':
            if 'PWD' in os.environ:
                os.chdir( os.environ['PWD'] )
            else:
                os.chdir( os.environ['HOME'] )

        self.__debug_noredirect = False
        self.__debug = True
        self.__log_stdout = False

        self.__callback_queue = queue.Queue()

        while len(args) > 1:
            arg = args[ 1 ]
            if arg.startswith( '-psn_' ):
                del args[ 1 ]

            elif arg.startswith( '--name=' ):
                self.opt_name = arg[len('--name='):]
                del args[ 1 ]

            elif arg == '--noredirect':
                self.__debug_noredirect = True
                del args[ 1 ]

            elif arg == '--log-stdout':
                self.__log_stdout = True
                del args[ 1 ]

            elif arg == '--debug' and len(args) > 2:
                self.__debug = True
                wb_git_debug.setDebug( args[2] )
                del args[ 1 ]
                del args[ 1 ]

            elif arg == '--start-dir' and len(args) > 2:
                os.chdir( args[2]  )
                del args[1]
                del args[1]

            elif arg == '--':
                break

            else:
                break

        self.args = args
        self.app_name = os.path.basename( args[0] )
        self.app_dir = os.path.dirname( args[0] )
        if self.app_dir == '':
            self.app_dir = self.startup_dir

        self.__call_gui_result = None
        self.__call_gui_result_event = threading.Event()

        self.main_thread = threading.currentThread()

        locale_path = wb_git_platform_specific.getLocalePath( self )
        self.translation = gettext.translation(
                'bemacs',
                str(locale_path),
                # language defaults
                fallback=True )

        import builtins
        # T_( 'non plural' )
        builtins.__dict__['T_'] = self.translation.gettext
        # S_( 'singular', 'plural', n )
        builtins.__dict__['S_'] = self.translation.ngettext
        # U_( 'static string' )
        builtins.__dict__['U_'] = lambda s: s

        # Debug settings
        self.__last_client_error = []

        self.setupLogging()

        self.log.info( 'startup_dir %s' % (self.startup_dir,) )
        self.log.info( 'locale_path %s' % (locale_path,) )
        self.log.info( 'find %r' % (gettext.find( 'wb_git', str(locale_path) ),) )
        self.log.info( 'info %r' % (self.translation.info(),) )
        self.log.info( T_("GIT Workbench") )

        self.prefs = wb_git_preferences.Preferences(
                self,
                wb_git_platform_specific.getPreferencesFilename() )

        self.main_window = wb_git_main_window.WbGitMainWindow( self )

        self.applicationStateChanged.connect( self.applicationStateChangedHandler )

    def event( self, event ):
        self._debugApp( 'WbGit_App.event() type() %r  %s' %
            (event.type(), qt_event_type_names.get( event.type(), '-unknown-' )) )

        return QtWidgets.QApplication.event( self, event )

    def applicationStateChangedHandler( self, state ):
        if state == QtCore.Qt.ApplicationActive:
            self.main_window.appActiveHandler()

    def isMainThread( self ):
        # return true if the caller is running on the main thread
        return self.main_thread is threading.currentThread()

    def setupLogging( self ):
        self.log = logging.getLogger( 'bemacs' )

        if self.__debug:
            self.log.setLevel( logging.DEBUG )
        else:
            self.log.setLevel( logging.INFO )

        if self.__log_stdout:
            handler = StdoutLogHandler()
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.log.addHandler( handler )

        else:
            log_filename = wb_git_platform_specific.getLogFilename()
            # keep 10 logs of 100K each
            handler = RotatingFileHandler( log_filename, 'a', 100*1024, 10 )
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.log.addHandler( handler )

        self.log.info( T_("Barry's Emacs starting") )

        self.log.debug( 'debug enabled' )

    def log_client_error( self, e, title='Error' ):
        self.__last_client_error = []
        for message, _ in e.args[1]:
            self.__last_client_error.append( message )
            self.log.error( message )

        message = '\n'.join( self.__last_client_error )
        QtWidgets.QMessageBox.critical( self, title, message ).exec_()

    def log_error( self, e, title='Error' ):
        message = str( e )
        self.log.error( message )

        QtWidgets.QMessageBox.critical( self, title, message ).exec_()

    def writePreferences( self ):
        self.prefs.writePreferences()

    def debugShowCallers( self, depth ):
        if not self.__debug:
            return

        stack = inspect.stack()
        for index in range( 1, depth+1 ):
            if index >= len(stack):
                break

            caller = stack[ index ]
            filename = os.path.basename( caller[1] )
            self._debugApp( 'File: %s:%d, Function: %s' % (filename, caller[2], caller[3]) )
            del caller

        del stack

    def guiReportException( self, body, title ):
        QtWidgets.QMessageBox.critical( self.main_window, title, body )

    def quit( self ):
        self._debugApp( 'quit()' )
        self.may_quit = True
        self.main_window.close()


#--------------------------------------------------------------------------------
#
#    RotatingFileHandler - based on python lib class
#
#--------------------------------------------------------------------------------
class RotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0):
        """
        Open the specified file and use it as the stream for logging.

        By default, the file grows indefinitely. You can specify particular
        values of maxBytes and backupCount to allow the file to rollover at
        a predetermined size.

        Rollover occurs whenever the current log file is nearly maxBytes in
        length. If backupCount is >= 1, the system will successively create
        new files with the same pathname as the base file, but with extensions
        ".1", ".2" etc. appended to it. For example, with a backupCount of 5
        and a base file name of "app.log", you would get "app.log",
        "app.log.1", "app.log.2", ... through to "app.log.5". The file being
        written to is always "app.log" - when it gets filled up, it is closed
        and renamed to "app.log.1", and if files "app.log.1", "app.log.2" etc.
        exist, then they are renamed to "app.log.2", "app.log.3" etc.
        respectively.

        If maxBytes is zero, rollover never occurs.
        """
        logging.FileHandler.__init__(self, str(filename), mode)
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        if maxBytes > 0:
            self.mode = "a"

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """

        self.stream.close()
        if self.backupCount > 0:
            prefix, suffix = os.path.splitext( self.baseFilename )
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d%s" % (prefix, i, suffix)
                dfn = "%s.%d%s" % (prefix, i+1, suffix)
                if os.path.exists(sfn):
                    #print( "%s -> %s" % (sfn, dfn) )
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.baseFilename + ".1"
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
            #print( "%s -> %s" % (self.baseFilename, dfn) )
        self.stream = open(self.baseFilename, "w")

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in setRollover().
        """
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            try:
                self.stream.seek(0, 2)  #due to non-posix-compliant Windows feature
                if self.stream.tell() + len(msg) >= self.maxBytes:
                    self.doRollover()

            except ValueError:
                # on Windows we get "ValueError: I/O operation on closed file"
                # when a second copy of workbench is run
                self.doRollover()

        logging.FileHandler.emit(self, record)

class StdoutLogHandler(logging.Handler):
    def __init__( self ):
        logging.Handler.__init__( self )

    def emit( self, record ):
        try:
            msg = self.format( record ) + '\n'

            sys.stdout.write( msg )
            sys.stdout.flush()

        except:
            self.handleError( record )

class MarshalledCall:
    def __init__( self, function, args ):
        self.function = function
        self.args = args

    def dispatch( self ):
        self.function( *self.args )

    def __repr__( self ):
        return 'MarshalledCall: fn=%s nargs=%d' % (self.function.__name__,len(self.args))
