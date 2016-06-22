'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scintilla.py

    provide a nice python3 friendly wrapper arouns the raw Scintilla control

'''
from PyQt5 import Qsci

#------------------------------------------------------------------------------------------
_colour_names = {
    'white':    '#ffffff',
    'black':    '#000000',
    'grey':     '#cccccc',    
    }

def parseColourToRgbInt( colour ):
    if colour.startswith( '#' ) and len(colour) == 7:
        return int( colour[1:], 16 )

    elif colour in _colour_names:
        return int( _colour_names[ colour ][1:], 16 )

    else:
        assert False, 'colour %r not supported' % (colour,)

class WbScintilla(Qsci.QsciScintilla):
    def __init__( self, parent ):
        super().__init__( parent )

        self.SendScintilla( self.SCI_SETCODEPAGE, self.SC_CP_UTF8 )

    # The following fucntion are organised in to section
    # taken from the scintilla documentation.
    # --- section-name ---

    # --- Text retrieval and modification ---
    def insertText( self, pos, text ):
        self.SendScintilla( self.SCI_INSERTTEXT, pos, text.encode( 'utf-8' ) )

    def replaceSel( self, text ):
        self.SendScintilla( self.SCI_REPLACESEL, text.encode( 'utf-8' ) )

    def setReadOnly( self, readonly ):
        self.SendScintilla( self.SCI_SETREADONLY, readonly )

    # --- Searching ---
    # --- Overtype ---
    # --- Cut, copy and paste ---
    # --- Error handling ---
    # --- Undo and Redo ---
    def emptyUndoBuffer( self ):
        self.SendScintilla( self.SCI_EMPTYUNDOBUFFER )

    # --- Selection and information ---
    def getLength( self ):
        return self.SendScintilla( self.SCI_GETLENGTH )

    def getLineCount( self ):
        return self.SendScintilla( self.SCI_GETLINECOUNT )

    def positionFromLine( self, line ):
        return self.SendScintilla( self.SCI_POSITIONFROMLINE, line )

    def getLineEndPosition( self, line ):
        return self.SendScintilla( self.SCI_GETLINEENDPOSITION, line )

    def setSelectionStart( self, start ):
        self.SendScintilla( self.SCI_SETSELECTIONSTART, start )

    def setSelectionEnd( self, end ):
        self.SendScintilla( self.SCI_SETSELECTIONEND, end )

    def lineFromPosition( self, pos ):
        return self.SendScintilla( self.SCI_LINEFROMPOSITION, pos )

    # --- Multiple Selection and Virtual Space ---
    # --- Scrolling and automatic scrolling ---
    def setFirstVisibleLine( self, line ):
        self.SendScintilla( self.SCI_SETFIRSTVISIBLELINE, line )

    def getFirstVisibleLine( self ):
        return self.SendScintilla( self.SCI_GETFIRSTVISIBLELINE )

    def gotoLine( self, line ):
        self.SendScintilla( self.SCI_GOTOLINE, line )

    def setScrollWidth( self, width ):
        self.SendScintilla( self.SCI_SETSCROLLWIDTH, width )

    def setHScrollBar( self, visible ):
        self.SendScintilla( self.SCI_SETHSCROLLBAR, visible )

    def setVScrollBar( self, visible ):
        self.SendScintilla( self.SCI_SETVSCROLLBAR, visible )

    # --- White space ---
    def setViewWhiteSpace( self, visible ):
        if visible:
            self.setViewWs( self.SCWS_VISIBLEALWAYS )
        else:
            self.setViewWs( self.SCWS_INVISIBLE )

    def setViewWs( self, mode ):
        self.SendScintilla( self.SCI_SETVIEWWS, mode )

    # --- Cursor ---
    # --- Mouse capture ---
    # --- Line endings ---
    # --- Styling ---
    def startStyling( self, pos ):
        self.SendScintilla( self.SCI_STARTSTYLING, pos )

    def setStyling( self, length, style_number ):
        self.SendScintilla( self.SCI_SETSTYLING, length, style_number )

    # --- Style definition ---
    def styleSetFromSpec( self, style_number, css ):
        # simple css-like style
        # name:value,name:value
        # white space is not removed
        for name_value in css.split( ',' ):
            name, value = name_value.split( ':' )
            if name == 'size':
                self.SendScintilla( self.SCI_STYLESETSIZE, style_number, int(value) )

            elif name == 'face':
                self.SendScintilla( self.SCI_STYLESETFONT, style_number, value.encode( 'utf-8' ) )

            elif name == 'fore':
                self.SendScintilla( self.SCI_STYLESETFORE, style_number, parseColourToRgbInt( value ) ) 

            elif name == 'back':
                self.SendScintilla( self.SCI_STYLESETBACK, style_number, parseColourToRgbInt( value ) ) 

            else:
                assert False, 'Unknown name %r in css %r' % (name, css)

    # --- Caret, selection, and hotspot styles ---
    # --- Character representations ---
    # --- Margins ---
    def setMarginWidth( self, margin, width ):
        self.SendScintilla( self.SCI_SETMARGINWIDTHN, margin, width )

    def setMarginMask( self, margin, mask ):
        self.SendScintilla( self.SCI_SETMARGINMASKN, margin, mask )

    def setMarginSensitive( self, margin, sensitive ):
        self.SendScintilla( self.SCI_SETMARGINSENSITIVEN, margin, sensitive )



    # --- Annotations ---
    # --- Other settings ---
    # --- Brace highlighting ---
    # --- Tabs and Indentation Guides ---
    # --- Markers ---
    def markerDefine( self, marker_number, marker_symbol ):
        self.SendScintilla( self.SCI_MARKERDEFINE, marker_number, marker_symbol )

    def markerSetFore( self, marker_number, colour ):
        self.SendScintilla( self.SCI_MARKERSETFORE, parseColourToRgbInt( colour ) )

    def markerSetBack( self, marker_number, colour ):
        self.SendScintilla( self.SCI_MARKERSETBACK, parseColourToRgbInt( colour ) )

    # --- Indicators ---
    def indicSetStyle( self, indic_number, style ):
        self.SendScintilla( self.SCI_INDICSETSTYLE, indic_number, style )

    def indicGetStyle( self, indic_number ):
        return self.SendScintilla( self.SCI_INDICGETSTYLE, indic_number )

    def indicSetFore( self, indic_number, color ):
        self.SendScintilla( self.SCI_INDICSETFORE, indic_number, parseColourToRgbInt( color ) )

    def indicGetFore( self, indic_number ):
        return self.SendScintilla( self.SCI_INDICGETFORE, indic_number )

    def setIndicatorValue( self, value ):
        self.SendScintilla( self.SCI_SETINDICATORVALUE, value )

    def getIndicatorValue( self ):
        return self.SendScintilla( self.SCI_GETINDICATORVALUE )

    def setIndicatorCurrent( self, indic_number ):
        self.SendScintilla( self.SCI_SETINDICATORCURRENT, indic_number )

    def getIndicatorCurrent( self ):
        return self.SendScintilla( self.SCI_GETINDICATORCURRENT )

    # use setIndicatorCurrent to set the indic_number to fill with
    # note: setIndicatorValue does not work (docs are wrong)
    def indicatorFillRange( self, position, fill_length ):
        self.SendScintilla( self.SCI_INDICATORFILLRANGE, position, fill_length )

    def indicatorClearRange( self, position, clear_length ):
        self.SendScintilla( self.SCI_INDICATORCLEARRANGE, position, clear_length )

    # --- OS X Find Indicator ---
    # --- Autocompletion ---
    # --- User lists ---
    # --- Call tips ---
    # --- Keyboard commands ---
    # --- Key bindings ---
    # --- Popup edit menu ---
    # --- Macro recording ---
    # --- Printing ---
    # --- Direct access ---
    # --- Multiple views ---
    # --- Background loading and saving ---
    # --- Folding ---
    def setFoldLevel( self, line, level ):
        self.SendScintilla( self.SCI_SETFOLDLEVEL, line, level )

    def getFoldLevel( self, line ):
        return self.SendScintilla( self.SCI_GETFOLDLEVEL, line )

    def setFoldExpanded( self, line, expand ):
        self.SendScintilla( self.SCI_SETFOLDEXPANDED, line, expand )

    def getFoldExpanded( self, line ):
        return self.SendScintilla( self.SCI_GETFOLDEXPANDED, line )

    def showLines( self, line_start, line_end ):
        self.SendScintilla( self.SCI_SHOWLINES, line_start, line_end ) 

    def hideLines( self, line_start, line_end ):
        self.SendScintilla( self.SCI_HIDELINES, line_start, line_end )

    # --- Line wrapping ---

    # --- Zooming ---
    def setZoom( self, zoom_in_points ):
        self.SendScintilla( self.SCI_SETZOOM, zoom_in_points )


    # --- Long lines ---

    # --- Lexer ---
    def setProperty( self, prop, value ):
        self.SendScintilla( self.SCI_SETPROPERTY, prop.encode( 'utf-8' ), value.encode( 'utf-8' ) )

    # ------------------------------------------------------------

    #--- high level API -------------------------------------------------------------
    def insertStyledText( self, text, style_number, indic_number=None ):
        # insert text and rember where
        pos = self.getLength()
        self.insertText( pos, text )

        # apply a style to the text
        self.startStyling( pos )
        self.setStyling( len(text), style_number )

        if indic_number is not None:
            # apply an indic_number to the text
            self.setIndicatorCurrent( indic_number )
            self.indicatorFillRange( pos, len(text) )

    def changeLineStyle( self, line, style ):
        pos_start = self.positionFromLine( line )
        pos_end = self.getLineEndPosition( line )
        self.startStyling( pos_start )
        self.setStyling( pos_end - pos_start, style )
