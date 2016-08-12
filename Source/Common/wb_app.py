'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_app.py

    Based on code from svn WorkBench

'''
import sys
import os
import inspect
import gettext
import queue
import xml_preferences

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_platform_specific
import wb_logging
import wb_shell_commands
import wb_background_thread

qt_event_type_names = {}
for name in dir(QtCore.QEvent):
    value = getattr( QtCore.QEvent, name )
    if isinstance( value, int ):
        qt_event_type_names[ int(value) ] = name

class WbApp(QtWidgets.QApplication,
             wb_logging.AppLoggingMixin,
             wb_background_thread.BackgroundWorkMixin):

    def __init__( self, app_name_parts, args, extra_loggers=None ):
        self.top_window = None
        self.main_window = None
        # used to set the names of files and windows for this app
        self.app_name_parts = app_name_parts

        # setup the platform specific support
        wb_platform_specific.setupPlatform( self.app_name_parts, sys.argv[0] )

        # plugins folder exists when win_app_packager creates an .EXE
        qt_plugin_dir = wb_platform_specific.getAppDir() / 'plugins'
        if qt_plugin_dir.exists():
            QtWidgets.QApplication.setLibraryPaths( [str(qt_plugin_dir)] )

        QtWidgets.QApplication.__init__( self, [sys.argv[0]] )

        if extra_loggers is None:
            extra_loggers = []

        wb_logging.AppLoggingMixin.__init__( self, extra_loggers )
        wb_background_thread.BackgroundWorkMixin.__init__( self )

        self.may_quit = False

        self.args = args

        self.startup_dir = os.getcwd()

        self.all_temp_files = []
        self.all_processes = []

        # on the Mac the app's cwd is the resource folder
        if wb_platform_specific.isMacOs():
            if 'PWD' in os.environ:
                os.chdir( os.environ['PWD'] )
            else:
                os.chdir( os.environ['HOME'] )

        self.__debug_noredirect = False
        self.__debug = False
        self.__trace = False
        self.__git_debug = False
        self.__log_stdout = False

        self.all_positional_args = []

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
                self.setDebug( args[2] )
                del args[ 1 ]
                del args[ 1 ]

            elif arg == '--start-dir' and len(args) > 2:
                os.chdir( args[2]  )
                del args[1]
                del args[1]

            elif arg == '--':
                break

            elif self.optionParse( args ):
                pass

            elif arg.startswith( '--' ):
                print( 'Error: unknown option %s' % (arg,) )
                break

            else:
                self.all_positional_args.append( arg )
                del args[1]

        self.args = args
        self.app_name = os.path.basename( args[0] )
        self.app_dir = os.path.dirname( args[0] )
        if self.app_dir == '':
            self.app_dir = self.startup_dir

        self.background_thread.start()

        locale_path = wb_platform_specific.getLocalePath()
        self.translation = gettext.translation(
                '-'.join( [part.lower() for part in self.app_name_parts] ),
                str(locale_path),
                # language defaults
                fallback=True )

        import builtins
        # T_( 'non plural' )
        builtins.__dict__['T_'] = self.translation.gettext
        # S_( 'singular', 'plural', n )
        builtins.__dict__['S_'] = self.translation.ngettext
        # U_( 'static string' )
        # already setup in wb_main

        # Debug settings
        self.__last_client_error = []

        # part 1 of settings up logging

        self.setupScmDebug()

        # and logging
        self.setupLogging()

        # these messages just go into the log file not the log widget
        self.log.info( 'startup_dir %s' % (self.startup_dir,) )
        self.log.info( 'locale_path %s' % (locale_path,) )
        # qqq: what should the arg to find be? wb wb-git, wb-hg?
        self.log.info( 'find %r' % (gettext.find( 'wb', str(locale_path) ),) )
        self.log.info( 'info %r' % (self.translation.info(),) )

        # and capture logs into the log widget
        self.__wb_log = wb_logging.WbLog( self )

        self.prefs_manager = self.createPreferencesManager()
        try:
            self.log.info( 'Reading preferences' )
            self.prefs_manager.readPreferences()

        except xml_preferences.ParseError as e:
            # the preferences are defaulted on a failure to load
            self.log.error( str(e) )

        self.prefs = self.prefs_manager.getPreferences()

        # part 2 of settings up logging is done in main window code
        self.main_window = self.createMainWindow()

        self.applicationStateChanged.connect( self.applicationStateChangedHandler )

    def logWidget( self ):
        return self.__wb_log.logWidget()

    # called to parse option supported by the derived class
    def optionParse( self, args ):
        return False

    # called to setup debug for the SCM supported by the derived class
    def setupScmDebug( self ):
        return

    def debugEnabled( self ):
        return self.__debug

    def extraDebugEnabled( self ):
        return False

    def traceEnabled( self ):
        return self.__trace

    def stdIoRedirected( self ):
        return not self.__debug_noredirect

    def logToStdOut( self ):
        return self.__log_stdout

    def event( self, event ):
        self._debugApp( 'Wb_App.event() type() %r  %s' %
            (event.type(), qt_event_type_names.get( event.type(), '-unknown-' )) )

        return QtWidgets.QApplication.event( self, event )

    def applicationStateChangedHandler( self, state ):
        if state == QtCore.Qt.ApplicationActive:
            self.main_window.appActiveHandler()

    def writePreferences( self ):
        self.log.info( 'Writing preferences' )
        self.prefs_manager.writePreferences()

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
