'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_diff_view.py

'''
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtGui

class WbDiffView(QtWidgets.QDialog):
    style_header = 0
    style_normal = 1
    style_add = 2
    style_delete = 3

    all_style_colours = (
        (style_header,  '#00cc00', '#ffffff'),
        (style_normal,  '#000000', '#ffffff'),
        (style_add,     '#DC143C', '#ffffff'),
        (style_delete,  '#1919c0', '#ffffff'),
        )

    def __init__( self, app, parent, title, icon ):
        self.app = app

        super().__init__( parent )

        self.setWindowTitle( title )
        self.setWindowIcon( icon )

        self.point_size = 14
        # point size and face need to choosen for platform
        if sys.platform.startswith( 'win' ):
            self.face = 'Courier New'

        elif sys.platform == 'darwin':
            self.face = 'Monaco'

        else:
            # Assuming linux/xxxBSD
            self.face = 'Liberation Mono'
            self.point_size = 11

        self.font = QtGui.QFont( self.face, self.point_size )

        self.text_edit = QtWidgets.QTextEdit()

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )

        self.buttons.accepted.connect( self.accept )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.text_edit )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        self.all_text_formats = {}
        for style, fg_colour, bg_colour in self.all_style_colours:
            format = QtGui.QTextCharFormat()
            format.setFont( self.font )
            format.setForeground( QtGui.QBrush( QtGui.QColor( fg_colour ) ) )
            format.setBackground( QtGui.QBrush( QtGui.QColor( bg_colour ) ) )
            self.all_text_formats[ style ] = format

        self.text_edit.setReadOnly( True )

        self.resize( 1100, 700 )

    def setUnifiedDiffText( self, all_lines ):
        for line in all_lines:
            if line[0] == '-':
                self.writeStyledText( line + '\n', self.style_delete )

            elif line[0] == '+':
                self.writeStyledText( line + '\n', self.style_add )

            elif line[0] == ' ':
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
