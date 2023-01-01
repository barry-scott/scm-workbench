from __future__ import print_function
import sys

class BuildLog:
    def __init__( self ):
        self._debug = False
        self._info_fmt = 'Info: %s'
        self._error_fmt = 'Error: %s'
        self._debug_fmt = 'Debug: %s'
        self._ct = None

    def setColour( self, colour ):
        if colour:
            try:
                import colour_text
                self._ct = colour_text.ColourText()
                self._ct.initTerminal()
                self._info_fmt = self._ct('<>info Info:<> %s')
                self._error_fmt = self._ct('<>error Error: %s<>')
                self._debug_fmt = self._ct('<>em Debug:<> %s')

            except ImportError:
                print( 'Colour output requires colour-text library: pip%d.%d install --user colour-text'
                        % (sys.version_info.major, sys.version_info.minor) )

    def colourFormat( self, colour_fmt ):
        if self._ct is not None:
            return self._ct( colour_fmt )
        else:
            # remove the colour markup
            return (colour_fmt
                    .replace( '<>info ', '' )
                    .replace( '<>error ', '' )
                    .replace( '<>em ', '' )
                    .replace( '<>', '' ))

    def setDebug( self, debug ):
        self._debug = debug

    def info( self, msg ):
        print( self._info_fmt % (msg,) )
        sys.stdout.flush()

    def error( self, msg ):
        print( self._error_fmt % (msg,) )
        sys.stdout.flush()

    def debug( self, msg ):
        if self._debug:
            sys.stderr.write( self._debug % (msg,) )
