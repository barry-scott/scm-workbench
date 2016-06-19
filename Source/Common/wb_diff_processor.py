'''
 ====================================================================
 Copyright (c) 2003-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_processor.py

'''
from PyQt5 import QtCore

class DiffOneSideProcessor:
    def __init__( self, name, text_body ):
        self.name = name
        self.text_body = text_body
        self.diff_line_numbers = text_body.diff_line_numbers

        self.line_number = 0
        self.last_line_number = -1
        self.changed_lines = []
        self.current_changed_block = -1
        self.current_change_marker = -1

    def _markChangeCurrentLine( self ):
        line_number = self.text_body.getLineCount() - 1

        if( self.last_line_number != line_number
        and self.last_line_number != (line_number - 1) ):
            self.changed_lines.append( line_number )

        self.last_line_number = line_number

    def moveNextChange( self ):
        self.current_changed_block += 1
        self._moveToChange()

    def movePrevChange( self ):
        self.current_changed_block -= 1
        self._moveToChange()

    def _moveToChange( self ):
        if len(self.changed_lines) == 0:
            return

        if self.current_changed_block >= len(self.changed_lines):
            self.current_changed_block = 0

        elif self.current_changed_block < 0:
            self.current_changed_block = len(self.changed_lines) - 1

        line_number = self.changed_lines[self.current_changed_block]

        top_line = line_number - 3
        if top_line < 0:
            top_line = 0

        self.text_body.setFirstVisibleLine( top_line )
        self.text_body.gotoLine( line_number )

    def getCurrentChangeLine( self ):
        return self.changed_lines[ self.current_changed_block ]
        
    def updateCurrentChangeMarker( self, line ):
        if self.current_change_marker != -1:
            self.diff_line_numbers.changeLineStyle( self.current_change_marker, self.diff_line_numbers.style_line_numbers )

        self.current_change_marker = line
        self.diff_line_numbers.changeLineStyle( self.current_change_marker, self.diff_line_numbers.style_line_numbers_for_diff )

    #--------------------------------------------------------------------------------
    def _addLineNumber( self ):
        self.line_number = self.line_number + 1

        self.diff_line_numbers.insertStyledText( '%5d\n' % (self.line_number,),
                        self.diff_line_numbers.style_line_numbers )

    def _addBlankLineNumber( self, isChange=1 ):
        self.diff_line_numbers.insertStyledText( '%5s\n' % '',
                        self.diff_line_numbers.style_line_numbers )

    def addNormalLine( self, line ):
        line_number = self.text_body.lineFromPosition( self.text_body.getLength() )
        self.text_body.setFoldLine( line_number, True )
        self._addLineNumber()
        self.text_body.insertStyledText( line+'\n', self.text_body.style_line_normal )

    def addGapLine( self ):
        self._markChangeCurrentLine()
        self._markChangeCurrentLine()
        self._addBlankLineNumber()

        line_number = self.text_body.lineFromPosition( self.text_body.getLength() )
        self.text_body.setFoldLine( line_number, False )
        self.text_body.insertStyledText( '\n', self.text_body.style_line_normal )

    def addInsertedLine( self, line ):
        self._markChangeCurrentLine()
        self._addLineNumber()
        line_number = self.text_body.lineFromPosition( self.text_body.getLength() )
        self.text_body.setFoldLine(line_number, False)
        self.text_body.insertStyledText( line+'\n', self.text_body.style_line_insert )

    def addDeletedLine( self, line ):
        self._markChangeCurrentLine()
        self._addLineNumber()
        line_number = self.text_body.lineFromPosition( self.text_body.getLength() )
        self.text_body.setFoldLine(line_number, False)
        self.text_body.insertStyledText( line+'\n', self.text_body.style_line_delete )

    def addChangedLineBegin( self ):
        self._markChangeCurrentLine()
        self._addLineNumber()
        line_number = self.text_body.lineFromPosition( self.text_body.getLength() )
        self.text_body.setFoldLine( line_number, False )

    def addChangedLineReplace( self, text ):
        self.text_body.insertStyledText( text, self.text_body.style_replace_changed )

    def addChangedLineDelete( self, old ):
        self.text_body.insertStyledText( old, self.text_body.style_replace_delete )

    def addChangedLineInsert( self, new ):
        self.text_body.insertStyledText( new, self.text_body.style_replace_insert )

    def addChangedLineEqual( self, text ):
        self.text_body.insertStyledText( text, self.text_body.style_replace_equal )

    def addChangedLineEnd( self ):
        self.text_body.insertStyledText( '\n', self.text_body.style_line_normal )

    #--------------------------------------------------------------------------------
    def addEnd( self ):
        self.text_body.setReadOnly( 1 )

#--------------------------------------------------------------------------------

class DiffProcessor:
    'DiffProcessor'
    def __init__( self, text_body_left, text_body_right ):
        self.processor_left = DiffOneSideProcessor( 'Diff Left',  text_body_left )
        self.processor_right = DiffOneSideProcessor( 'Diff Right',  text_body_right )

    def addNormalLine( self, line ):
        self.processor_left.addNormalLine(  line )
        self.processor_right.addNormalLine(  line )

    def addInsertedLine( self, line ):
        self.processor_left.addGapLine()
        self.processor_right.addInsertedLine( line )

    def addDeletedLine( self, line ):
        self.processor_left.addDeletedLine( line )
        self.processor_right.addGapLine()

    def addChangedLineBegin( self ):
        self.processor_left.addChangedLineBegin()
        self.processor_right.addChangedLineBegin()

    def addChangedLineReplace( self, old, new ):
        self.processor_left.addChangedLineReplace( old )
        self.processor_right.addChangedLineReplace( new )

    def addChangedLineDelete( self, old ):
        self.processor_left.addChangedLineDelete( old )

    def addChangedLineInsert( self, new ):
        self.processor_right.addChangedLineInsert( new )

    def addChangedLineEqual( self, text ):
        self.processor_left.addChangedLineEqual( text )
        self.processor_right.addChangedLineEqual( text )

    def addChangedLineEnd( self ):
        self.processor_left.addChangedLineEnd()
        self.processor_right.addChangedLineEnd()

    def addEnd( self ):
        self.processor_left.addEnd()
        self.processor_right.addEnd()
        self.processor_left.text_body.setFocus( QtCore.Qt.OtherFocusReason)

    def moveNextChange( self ):
        for proc in (self.processor_left, self.processor_right):
            proc.moveNextChange()
            line = proc.getCurrentChangeLine()
            proc.updateCurrentChangeMarker( line )

    def movePrevChange( self ):
        for proc in (self.processor_left, self.processor_right):
            proc.movePrevChange()
            line = proc.getCurrentChangeLine()
            proc.updateCurrentChangeMarker( line )

    def getChangeCount( self ):
        return len( self.processor_left.changed_lines )

    def getCurrentChange( self ):
        return self.processor_left.current_changed_block + 1
