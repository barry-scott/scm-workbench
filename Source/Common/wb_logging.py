'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_logging.py

    based on code from PySVN Workbench

'''
import sys
import os
import time
import logging
import traceback

import wb_platform_specific

from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6 import QtCore

INFOHEADER = logging.INFO + 1

class AppLogging:
    def __init__( self, parent ):
        self.parent = parent
        self.log = None
        self.trace = None

        self.all_extra_logger_names = []
        self.all_extra_log = []

    def setupLogging( self, extra_logger_names=None ):
        if extra_logger_names is not None:
            self.all_extra_logger_names = extra_logger_names

        logging.addLevelName( INFOHEADER, 'INFOHEADER' )
        name = ''.join( self.parent.app_name_parts )
        self.log = ThreadSafeLogFacade( self.parent, logging.getLogger( name ) )
        self.trace = ThreadSafeLogFacade( self.parent, logging.getLogger( '%s.Trace' % (name,) ) )

        for name in self.all_extra_logger_names:
            log = logging.getLogger( name )
            self.all_extra_log.append( log )

            if self.parent.extraDebugEnabled():
                log.setLevel( logging.DEBUG )

            else:
                log.setLevel( logging.INFO )

        if self.parent.debugEnabled():
            self.log.setLevel( logging.DEBUG )
        else:
            self.log.setLevel( logging.INFO )

        if self.parent.traceEnabled():
            self.trace.setLevel( logging.INFO )
        else:
            self.trace.setLevel( logging.CRITICAL )

        log_filename = wb_platform_specific.getLogFilename()

        # keep 10 logs of 100K each
        handler = RotatingFileHandler( str( log_filename ), 'a', 100*1024, 10 )
        formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
        handler.setFormatter( formatter )
        self.log.addHandler( handler )

        for log in self.all_extra_log:
            log.addHandler( handler )

        if self.parent.logToStdOut():
            handler = StdoutLogHandler()
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.log.addHandler( handler )

            handler = StdoutLogHandler()
            formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
            handler.setFormatter( formatter )
            self.trace.addHandler( handler )

            for log in self.all_extra_log:
                handler = StdoutLogHandler()
                formatter = logging.Formatter( '%(asctime)s %(levelname)s %(message)s' )
                handler.setFormatter( formatter )
                log.addHandler( handler )

        self.log.debug( 'Debug is enabled' )
        self.trace.info( 'Trace enabled' )

#--------------------------------------------------------------------------------
# move all calls from a background thread to the foreground GUI thread
class ThreadSafeLogFacade:
    def __init__( self, app, thread_unsafe_log ):
        self.__app = app
        self.__log = thread_unsafe_log

    def infoheader( self, msg ):
        self.__dispatch( self.__log.log, (INFOHEADER, msg,) )

    def info( self, msg ):
        self.__dispatch( self.__log.info, (msg,) )

    def warning( self, msg ):
        self.__dispatch( self.__log.warning, (msg,) )

    def error( self, msg ):
        self.__dispatch( self.__log.error, (msg,) )

    def critical( self, msg ):
        self.__dispatch( self.__log.critical, (msg,) )

    def debug( self, msg ):
        self.__dispatch( self.__log.debug, (msg,) )

    def exception( self, msg ):
        tb_list = traceback.format_exception( *sys.exc_info() )

        if self.__app.isForegroundThread():
            self.__printStackList( self.error, msg, tb_list )

        else:
            self.__dispatch( self.__printStackList, (self.error, msg, tb_list) )

    def stack( self, msg ):
        # take the stack and lose the 2 calls in our logging code
        tb_list = traceback.format_stack()[:-1]

        if self.__app.isForegroundThread():
            self.__printStackList( self.info, msg, tb_list )

        else:
            self.__dispatch( self.__printStackList, (self.info, msg, tb_list) )

    def __printStackList( self, log_fn, msg, tb_list ):
        log_fn( msg )
        for compound_line in tb_list:
            if compound_line.endswith( '\n' ):
                compound_line = compound_line[:-1]
            for line in compound_line.split('\n'):
                log_fn( line )

    def __dispatch( self, func, args ):
        if self.__app.isForegroundThread():
            func( *args )

        else:
            self.__app.runInForeground( func, args )

    def setLevel( self, level ):
        assert self.__app.isForegroundThread()
        self.__log.setLevel( level )

    def addHandler( self, handler ):
        assert self.__app.isForegroundThread()
        self.__log.addHandler( handler )

    def removeHandler( self, handler ):
        # have to risk calling off if main thread
        # to give excepthook a chance of working
        self.__log.removeHandler( handler )


#--------------------------------------------------------------------------------
class StdoutLogHandler(logging.Handler):
    def __init__( self ):
        super().__init__()

    def emit( self, record ):
        try:
            msg = self.format( record ) + '\n'

            sys.__stdout__.write( msg )

        except:
            self.handleError( record )

#--------------------------------------------------------------------------------
class WbLog:
    def __init__( self, app ):
        self.app = app
        self.__log_widget = WbLogTextWidget( self.app )

        self.__line = ''

        # Redirect the console IO to this panel
        sys.stdin = wb_platform_specific.getNullDevice().open( 'r' )
        if self.app.stdIoRedirected():
            sys.stdout = self
            sys.stderr = self
            sys.excepthook = self.excepthook

        # Redirect log to the Log panel
        self.widget_log_handler = WidgetLogHandler( self.app, self.__log_widget )
        self.app.log.addHandler( self.widget_log_handler )

        self.__session_log = open( str(wb_platform_specific.getLogFilename()) + '.session.log', 'w', buffering=1 )

    def initStyles( self ):
        self.__log_widget.initStyles()

    def excepthook( self, type_, value, tb ):
        # emergency write
        self.__session_log.write( 'excepthook called\n' )
        self.__session_log.flush()

        all_exception_lines = traceback.format_exception( type_, value, tb )
        for line in all_exception_lines:
            self.__session_log.write( line )
        self.__session_log.flush()

        # cannot use the GUI window now app is not sane
        self.app.log.removeHandler( self.widget_log_handler )

        self.app.log.error( 'excepthook called' )
        for line in all_exception_lines:
            self.app.log.error( line.replace( '\n', '' ) )

        self.app.runInForeground( self.app.log.addHandler, (self.widget_log_handler,) )
        self.app.runInForeground( self.app.log.error, ('Check log for traceback details',) )

    def logWidget( self ):
        return self.__log_widget

    def clearLog( self ):
        self.__log_widget.clear()

    #---------- look like a file object -------------------------
    def write( self, msg ):
        self.__session_log.write( '%s: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S') ,msg) )
        self.__session_log.flush()

        # only allowed to use GUI objects on the foreground thread
        if not self.app.isForegroundThread():
            self.app.runInForeground( self.write, (msg,) )
            return

        self.__line = self.__line + msg
        while '\n' in self.__line:
            msg, self.__line = self.__line.split( '\n', 1 )
            self.app.log.error( msg )

    def close( self ):
        if self.__line != '':
            sys.stdout.write( '\n' )

#--------------------------------------------------------------------------------
class WidgetLogHandler(logging.Handler):
    def __init__( self, app, log_widget ):
        self.app = app
        self.log_widget = log_widget
        logging.Handler.__init__( self )

    def emit( self, record ):
        msg = self.format( record ) + '\n'
        level = record.levelno

        if level >= logging.CRITICAL:
            self.log_widget.writeCritical( msg )

        elif level >= logging.ERROR:
            self.log_widget.writeError( msg )

        elif level >= logging.WARNING:
            self.log_widget.writeWarning( msg )

        elif level >= INFOHEADER:
            self.log_widget.writeInfoHeader( msg )

        elif level >= logging.INFO:
            self.log_widget.writeInfo( msg )

        elif level >= logging.DEBUG:
            self.log_widget.writeDebug( msg )

        else:
            self.log_widget.writeError( msg )

#--------------------------------------------------------------------------------
class WbLogTextWidget(QtWidgets.QTextEdit):
    style_normal = 0
    style_error = 1
    style_info = 2
    style_warning = 3
    style_critical = 4
    style_debug = 5
    style_divider = 6
    style_infoheader = 7

    all_style_colours_light_mode = (
        (style_normal,      '', ''),
        (style_error,       '#DC143C', ''),  # Crimson
        (style_warning,     '#008000', ''),  # Green
        (style_critical,    '#BA55D3', ''),  # Medium Orchid
        (style_debug,       '#191970', '#cccccc'),
        (style_divider,     '#cccccc', ''),  # Grey
        (style_infoheader,  '#191970', ''),  # Midnight Blue
        (style_info,        '#803080', ''),  # light purple
        )

    all_style_colours_dark_mode = (
        (style_normal,      '', ''),
        (style_error,       '#DC143C', ''),  # Crimson
        (style_warning,     '#00d000', ''),  # Green
        (style_critical,    '#BA55D3', ''),  # Medium Orchid
        (style_debug,       '#4040fo', '#cccccc'),
        (style_divider,     '#cccccc', ''),  # Grey
        (style_infoheader,  '#8080ff', ''),  # Midnight Blue
        (style_info,        '#f060f0', ''),  # light purple
        )

    divider_text = '\u2500'*60 + '\n'

    def __init__( self, app ):
        self.app = app

        self.initStyles()

        super().__init__()
        self.setReadOnly( True )
        self.setTextInteractionFlags( QtCore.Qt.TextInteractionFlag.TextSelectableByMouse|QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard )

    def initStyles( self ):
        if self.app.isDarkMode():
            all_style_colours = self.all_style_colours_dark_mode

        else:
            all_style_colours = self.all_style_colours_light_mode

        self.all_text_formats = {}
        for style, fg_colour, bg_colour in all_style_colours:
            fmt = QtGui.QTextCharFormat()
            fmt.setForeground( self.app.makeFgBrush( fg_colour ) )
            fmt.setBackground( self.app.makeBgBrush( bg_colour ) )
            self.all_text_formats[ style ] = fmt

    def __writeStyledText( self, text, style ):
        self.moveCursor( QtGui.QTextCursor.MoveOperation.End )

        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setCharFormat( self.all_text_formats[ style ] )
        cursor.insertText( text )
        cursor.endEditBlock()

        self.ensureCursorVisible()

    def writeNormal( self, text ):
        self.__writeStyledText( text, self.style_normal )

    def writeError( self, text ):
        self.__writeStyledText( text, self.style_error )

    def writeInfoHeader( self, text ):
        self.__writeStyledText( self.divider_text, self.style_divider )
        self.__writeStyledText( text, self.style_infoheader )

    def writeInfo( self, text ):
        self.__writeStyledText( text, self.style_info )

    def writeWarning( self, text ):
        self.__writeStyledText( text, self.style_warning )

    def writeCritical( self, text ):
        self.__writeStyledText( text, self.style_critical )

    def writeDebug( self, text ):
        self.__writeStyledText( text, self.style_debug )

    def clearText( self ):
        self.clear()

#--------------------------------------------------------------------------------
#
#    RotatingFileHandler - based on python lib class
#
#--------------------------------------------------------------------------------
class RotatingFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", maxBytes=0, backupCount=0):
        """

        Open the specified file and use it as the stream for logging.

        By default, the file grows indefinitely.  You can specify
        particular values of maxBytes and backupCount to allow the file
        to rollover at a predetermined size.

        Rollover occurs whenever the current log file is nearly
        maxBytes in length.  If backupCount is >= 1, the system will
        successively create new files with the same pathname as the
        base file, but add in ".1", ".2" etc.

        The file being written to is always "app.log" - when it gets
        filled up, it is closed and renamed to "app.1.log", and if
        files "app.1.log", "app.2.log" etc.  exist, then they are
        renamed to "app.2.log", "app.3.log" etc.  respectively.

        For example, with a backupCount of 5 and a base file name of
        "app.log", you would get "app.log", "app.1.log", "app.2.log",
        ...  through to "app.5.log".

        If maxBytes is zero, rollover never occurs.
        """
        super().__init__(filename, mode, encoding='utf-8')
        self.maxBytes = maxBytes
        self.backupCount = backupCount

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
                    #print "%s -> %s" % (sfn, dfn)
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = "%s.%d%s" % (prefix, 1, suffix)
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)

        self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)

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
