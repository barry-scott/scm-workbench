'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_app.py

    Based on code from git WorkBench

'''
import sys
import os
import threading
import inspect
import gettext
import queue

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_platform_specific
import wb_logging
import wb_shell_commands
import wb_background_thread

import wb_git_main_window
import wb_git_preferences
import wb_git_exceptions
import wb_git_debug

qt_event_type_names = {}
for name in dir(QtCore.QEvent):
    value = getattr( QtCore.QEvent, name )
    if isinstance( value, int ):
        qt_event_type_names[ int(value) ] = name

class MarshalledCall:
    def __init__( self, function, args ):
        self.function = function
        self.args = args

    def dispatch( self ):
        self.function( *self.args )

    def __repr__( self ):
        return 'MarshalledCall: fn=%s nargs=%d' % (self.function.__name__,len(self.args))

class WbGit_App(QtWidgets.QApplication,
                wb_logging.AppLoggingMixin,
                wb_git_debug.WbGitDebugMixin):

    foregroundProcessSignal = QtCore.pyqtSignal( [MarshalledCall] )

    def __init__( self, args ):
        self.main_window = None
        # used to set the names of files and windows for this app
        self.app_name_parts = ('Git', 'Workbench')

        QtWidgets.QApplication.__init__( self, [sys.argv[0]] )

        wb_logging.AppLoggingMixin.__init__( self, ['git.cmd'] )
        wb_git_debug.WbGitDebugMixin.__init__( self )

        self.may_quit = False

        self.args = args

        self.startup_dir = os.getcwd()

        self.all_temp_files = []
        self.all_processes = []

        wb_platform_specific.setupPlatform( self.app_name_parts )
        #wb_shell_commands.setupCommands()

        # on the Mac the app's cwd is the resource folder
        if sys.platform == 'darwin':
            if 'PWD' in os.environ:
                os.chdir( os.environ['PWD'] )
            else:
                os.chdir( os.environ['HOME'] )

        self.__debug_noredirect = False
        self.__debug = False
        self.__trace = False
        self.__git_debug = False
        self.__log_stdout = False

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

            elif arg == '--git-debug':
                self.__git_debug = True
                del args[ 1 ]

            elif arg == '--start-dir' and len(args) > 2:
                os.chdir( args[2]  )
                del args[1]
                del args[1]

            elif arg == '--':
                break

            elif arg.startswith( '--' ):
                print( 'Error: unknown option %s' % (arg,) )
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

        self.background_thread = wb_background_thread.BackgroundThread( self )
        self.background_thread.start()

        self.foregroundProcessSignal.connect( self.__foregroundProcessHandler, type=QtCore.Qt.QueuedConnection )

        locale_path = wb_platform_specific.getLocalePath()
        self.translation = gettext.translation(
                'git-workbench',
                str(locale_path),
                # language defaults
                fallback=True )

        import builtins
        # T_( 'non plural' )
        builtins.__dict__['T_'] = self.translation.gettext
        # S_( 'singular', 'plural', n )
        builtins.__dict__['S_'] = self.translation.ngettext
        # U_( 'static string' )
        # already setup in wb_git_main

        # Debug settings
        self.__last_client_error = []

        # part 1 of settings up logging

        # turn on GitPython debug is required
        import git
        if self.__git_debug:
            git.Git.GIT_PYTHON_TRACE = 'full'
        else:
            git.Git.GIT_PYTHON_TRACE = False

        # and logging
        self.setupLogging()

        self.log.info( 'startup_dir %s' % (self.startup_dir,) )
        self.log.info( 'locale_path %s' % (locale_path,) )
        self.log.info( 'find %r' % (gettext.find( 'wb_git', str(locale_path) ),) )
        self.log.info( 'info %r' % (self.translation.info(),) )

        self.prefs = wb_git_preferences.Preferences(
                self,
                wb_platform_specific.getPreferencesFilename() )


        # part 2 of settings up logging is done in main window code
        self.main_window = wb_git_main_window.WbGitMainWindow( self )

        self.applicationStateChanged.connect( self.applicationStateChangedHandler )

    def debugEnabled( self ):
        return self.__debug

    def extraDebugEnabled( self ):
        # tells wb_logging to turn on debug for git.cmd
        return self.__git_debug

    def traceEnabled( self ):
        return self.__trace

    def stdIoRedirected( self ):
        return not self.__debug_noredirect

    def logToStdOut( self ):
        return self.__log_stdout

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

    def backgroundProcess( self, function, args ):
        self._debugThreading( 'backgroundProcess( %r, %r )' % (function, args) )
        self.background_thread.addWork( function, args )

    def foregroundProcess( self, function, args ):
        # cannot call logging from here as this will cause the log call to be marshelled
        self.foregroundProcessSignal.emit( MarshalledCall( function, args ) )

    def __foregroundProcessHandler( self, function_args ):
        self._debugThreading( '__foregroundProcessHandler( %r )' % (function_args,) )

        try:
            function_args.dispatch()

        except:
            self.log.exception( 'foregroundProcess failed' )

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
