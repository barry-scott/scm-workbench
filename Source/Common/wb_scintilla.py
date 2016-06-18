'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scintilla.py

    proveide a nice python3 friendly wrapper arouns the raw Scintilla control

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

    def setProperty( self, prop, value ):
        self.SendScintilla( self.SCI_SETPROPERTY, prop.encode( 'utf-8' ), value.encode( 'utf-8' ) )

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

    def setMarginWidth( self, margin, width ):
        self.SendScintilla( self.SCI_SETMARGINWIDTHN, margin, width )

    def setScrollWidth( self, width ):
        self.SendScintilla( self.SCI_SETSCROLLWIDTH, width )

    def emptyUndoBuffer( self ):
        self.SendScintilla( self.SCI_EMPTYUNDOBUFFER )

    def getLength( self ):
        return self.SendScintilla( self.SCI_GETLENGTH )

    def insertText( self, pos, text ):
        self.SendScintilla( self.SCI_INSERTTEXT, pos, text.encode( 'utf-8' ) )

    def startStyling( self, pos ):
        self.SendScintilla( self.SCI_STARTSTYLING, pos )

    def setStyling( self, length, style_number ):
        self.SendScintilla( self.SCI_SETSTYLING, length, style_number )

    def positionFromLine( self, line ):
        return self.SendScintilla( self.SCI_POSITIONFROMLINE, line )

    def getLineEndPosition( self, line ):
        return self.SendScintilla( self.SCI_GETLINEENDPOSITION, line )

    def setSelectionStart( self, start ):
        self.SendScintilla( self.SCI_SETSELECTIONSTART, start )

    def setSelectionEnd( self, end ):
        self.SendScintilla( self.SCI_SETSELECTIONEND, end )

    def replaceSel( self, text ):
        self.SendScintilla( self.SCI_REPLACESEL, text.encode( 'utf-8' ) )

    def indicSetStyle( self, style_number, style ):
        self.SendScintilla( self.SCI_INDICSETSTYLE, style_number, style )

    def indicSetFore( self, style_number, color ):
        self.SendScintilla( self.SCI_INDICSETFORE, style_number, parseColourToRgbInt( color ) )
        
    def setHScrollBar( self, visible ):
        self.SendScintilla( self.SCI_SETHSCROLLBAR, visible )

    def setVScrollBar( self, visible ):
        self.SendScintilla( self.SCI_SETVSCROLLBAR, visible )

    def setMarginMask( self, margin, mask ):
        self.SendScintilla( self.SCI_SETMARGINMASKN, margin, mask )

    def setMarginSensitive( self, margin, sensitive ):
        self.SendScintilla( self.SCI_SETMARGINSENSITIVEN, margin, sensitive )

    def markerDefine( self, marker_number, marker_symbol ):
        self.SendScintilla( self.SCI_MARKERDEFINE, marker_number, marker_symbol )

    def markerSetFore( self, marker_number, colour ):
        self.SendScintilla( self.SCI_MARKERSETFORE, parseColourToRgbInt( colour ) )

    def markerSetBack( self, marker_number, colour ):
        self.SendScintilla( self.SCI_MARKERSETBACK, parseColourToRgbInt( colour ) )

    def lineFromPosition( self, pos ):
        return self.SendScintilla( self.SCI_LINEFROMPOSITION, pos )

    def setReadOnly( self, readonly ):
        self.SendScintilla( self.SCI_SETREADONLY, readonly )

    def getLength( self ):
        return self.SendScintilla( self.SCI_GETLENGTH )

    def setFoldLevel( self, line, level ):
        self.SendScintilla( self.SCI_SETFOLDLEVEL, line, level )

    def getFoldLevel( self, line ):
        return self.SendScintilla( self.SCI_GETFOLDLEVEL, line )

    def setFoldExpanded( self, line, expand ):
        self.SendScintilla( self.SCI_SETFOLDEXPANDED, line, expand )

    def getFoldExpanded( self, line ):
        return self.SendScintilla( self.SCI_GETFOLDEXPANDED, line )

    def setZoom( self, zoom_in_points ):
        self.SendScintilla( self.SCI_SETZOOM, zoom_in_points )

    def showLines( self, line_start, line_end ):
        self.SendScintilla( self.SCI_SHOWLINES, line_start, line_end ) 

    def hideLines( self, line_start, line_end ):
        self.SendScintilla( self.SCI_HIDELINES, line_start, line_end )

    def getLineCount( self ):
        return self.SendScintilla( self.SCI_GETLINECOUNT )

    def setFirstVisibleLine( self, line ):
        self.SendScintilla( self.SCI_SETFIRSTVISIBLELINE, line )

    def getFirstVisibleLine( self ):
        return self.SendScintilla( self.SCI_GETFIRSTVISIBLELINE )

    def gotoLine( self, line ):
        self.SendScintilla( self.SCI_GOTOLINE, line )

    def setViewWhiteSpace( self, visible ):
        if visible:
            self.setViewWs( self.SCWS_VISIBLEALWAYS )
        else:
            self.setViewWs( self.SCWS_INVISIBLE )

    def setViewWs( self, mode ):
        self.SendScintilla( self.SCI_SETVIEWWS, mode )

    #--- high level API -------------------------------------------------------------
    def insertStyledText( self, text, style ):
        pos = self.getLength()
        self.insertText( pos, text )
        self.startStyling( pos )
        self.setStyling( len(text), style )

    def changeLineStyle( self, line, style ):
        pos_start = self.positionFromLine( line )
        pos_end = self.getLineEndPosition( line )
        self.startStyling( pos_start )
        self.setStyling( pos_end - pos_start, style )
