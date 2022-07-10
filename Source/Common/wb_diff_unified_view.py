'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_view.py

'''
from PyQt6 import QtWidgets
from PyQt6 import QtGui

import wb_tracked_qwidget
import wb_config

class WbDiffViewBase(wb_tracked_qwidget.WbTrackedModelessQWidget):
    style_header = 0
    style_normal = 1
    style_add = 2
    style_delete = 3

    def __init__( self, app, title ):
        self.app = app

        super().__init__()

        prefs = app.prefs.diff_window

        if app.isDarkMode():
            self.all_style_colours = (
                (self.style_header,  wb_config.diff_dark_colour_header, ''),
                (self.style_normal,  '', ''),
                (self.style_delete,  wb_config.diff_dark_colour_delete_line, ''),
                (self.style_add,     wb_config.diff_dark_colour_insert_line, ''),
                )
        else:
            self.all_style_colours = (
                (self.style_header,  wb_config.diff_light_colour_header, ''),
                (self.style_normal,  '', ''),
                (self.style_delete,  wb_config.diff_light_colour_delete_line, ''),
                (self.style_add,     wb_config.diff_light_colour_insert_line, ''),
                )

        self.setWindowTitle( title )
        self.setWindowIcon( self.app.getAppQIcon() )

class WbDiffViewText(WbDiffViewBase):
    def __init__( self, app, title ):
        super().__init__( app, title )

        self.code_font = self.app.codeFont()

        self.text_edit = QtWidgets.QTextEdit()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.text_edit )

        self.setLayout( self.layout )

        self.all_text_formats = {}
        for style, fg_colour, bg_colour in self.all_style_colours:
            char_format = QtGui.QTextCharFormat()
            char_format.setFont( self.code_font )
            char_format.setForeground( app.makeFgBrush( fg_colour ) )
            char_format.setBackground( app.makeBgBrush( bg_colour ) )
            self.all_text_formats[ style ] = char_format

        self.text_edit.setReadOnly( True )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 130*em, 45*ex )

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
        self.text_edit.moveCursor( QtGui.QTextCursor.MoveOperation.Start )
        self.text_edit.ensureCursorVisible()

    def writeStyledText( self, text, style ):
        self.text_edit.moveCursor( QtGui.QTextCursor.MoveOperation.End )

        cursor = self.text_edit.textCursor()
        cursor.beginEditBlock()
        cursor.setCharFormat( self.all_text_formats[ style ] )
        cursor.insertText( text )
        cursor.endEditBlock()
