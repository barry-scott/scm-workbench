'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_view.py

'''
import sys
import os
import itertools

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_tracked_qwidget

def U_(s):
    return s

class WbDiffViewBase(wb_tracked_qwidget.WbTrackedModelessQWidget):
    style_header = 0
    style_normal = 1
    style_add = 2
    style_delete = 3

    def __init__( self, app, title ):
        self.app = app

        super().__init__()

        prefs = app.prefs.diff_window

        self.all_style_colours = (
            (self.style_header,  prefs.colour_header.fg, '#ffffff'),
            (self.style_normal,  prefs.colour_normal.fg, '#ffffff'),
            (self.style_delete,  prefs.colour_delete_line.fg, '#ffffff'),
            (self.style_add,     prefs.colour_insert_line.fg, '#ffffff'),
            )

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

class WbDiffViewText(WbDiffViewBase):
    def __init__( self, app, title ):
        super().__init__( app, title )

        self.code_font = self.app.getCodeFont()

        self.text_edit = QtWidgets.QTextEdit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.text_edit )

        self.setLayout( self.layout )

        self.all_text_formats = {}
        for style, fg_colour, bg_colour in self.all_style_colours:
            format = QtGui.QTextCharFormat()
            format.setFont( self.code_font )
            format.setForeground( QtGui.QBrush( QtGui.QColor( str(fg_colour) ) ) )
            format.setBackground( QtGui.QBrush( QtGui.QColor( str(bg_colour) ) ) )
            self.all_text_formats[ style ] = format

        self.text_edit.setReadOnly( True )

        self.resize( 1100, 700 )

    def setUnifiedDiffText( self, all_lines ):
        for line in all_lines:
            if line.startswith('-'):
                self.writeStyledText( line + '\n', self.style_delete )

            elif line.startswith('+'):
                self.writeStyledText( line + '\n', self.style_add )

            elif line.startswith(' '):
                self.writeStyledText( line + '\n', self.style_normal )

            else:
                self.writeStyledText( line + '\n', self.style_header )

        self.ensureStartVisible()

    def ensureStartVisible( self ):
        self.text_edit.moveCursor( QtGui.QTextCursor.Start )
        self.text_edit.ensureCursorVisible()

    def writeStyledText( self, text, style ):
        self.text_edit.moveCursor( QtGui.QTextCursor.End )

        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        cursor.setCharFormat( self.all_text_formats[ style ] )
        cursor.insertText( text )
        cursor.endEditBlock()
