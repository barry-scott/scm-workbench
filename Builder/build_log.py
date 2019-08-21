import sys

class BuildLog:
    def __init__( self ):
        self._debug = False
        self.info_colour = ''
        self.error_colour = ''
        self.debug_colour = ''
        self.no_colour = ''

        if sys.platform == 'win32':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # turn on the console ANSI colour handling
            kernel32.SetConsoleMode( kernel32.GetStdHandle( -11 ), 7 )

    def setDebug( self, debug ):
        self._debug = debug

    def setColour( self, colour ):
        if colour:
            self.info_colour = '\033[32m'
            self.error_colour = '\033[31;1m'
            self.debug_colour = '\033[33;1m'
            self.no_colour = '\033[m'
        else:
            self.info_colour = ''
            self.error_colour = ''
            self.debug_colour = ''
            self.no_colour = ''

    def info( self, msg ):
        print( '%sInfo:%s %s' % (self.info_colour, self.no_colour, msg) )
        sys.stdout.flush()

    def error( self, msg ):
        print( '%sError: %s%s' % (self.error_colour, msg, self.no_colour) )
        sys.stdout.flush()

    def debug( self, msg ):
        if self._debug:
            sys.stderr.write( '%sDebug: %s%s\n' % (self.debug_colour, msg, self.no_colour) )
