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

    all_style_colours = (
        (style_header,  '#00cc00', '#ffffff'),
        (style_normal,  '#000000', '#ffffff'),
        (style_add,     '#DC143C', '#ffffff'),
        (style_delete,  '#1919c0', '#ffffff'),
        )

    def __init__( self, app, title, icon ):
        self.app = app

        super().__init__()

        self.setWindowTitle( title )
        if icon is not None:
            self.setWindowIcon( icon )

class WbDiffViewText(WbDiffViewBase):
    def __init__( self, app, title, icon ):
        super().__init__( app, title, icon )

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

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.text_edit )

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

class WbDiffViewVisual(WbDiffViewBase):
    def __init__( self, app, title, icon ):
        super().__init__( app, title, icon )

        self.model = WbDiffVisualModel()

        self.tree = QtWidgets.QTreeView()
        self.tree.setModel( self.model )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.tree )
        self.setLayout( self.layout )

        #self.resize( 1100, 700 )
        self.resize( 600, 200 )

    def setDiffSources( self, old_lines, new_lines ):
        self.model.addSection( 'D', 1, ['old 1', 'old 2'], 1, [] )
        #self.model.addSection( 'A', 2, [], 1, [' new 1', 'new 2', 'new 3', 'new 4'] )
        self.model.initDone()

def decodeItemFlags( value ):
    value = int(value)

    all_bits = [
        (QtCore.Qt.ItemIsSelectable, 'ItemIsSelectable'),
        (QtCore.Qt.ItemIsEditable, 'ItemIsEditable'),
        (QtCore.Qt.ItemIsDragEnabled, 'ItemIsDragEnabled'),
        (QtCore.Qt.ItemIsDropEnabled, 'ItemIsDropEnabled'),
        (QtCore.Qt.ItemIsUserCheckable, 'ItemIsUserCheckable'),
        (QtCore.Qt.ItemIsEnabled, 'ItemIsEnabled'),
        #(QtCore.Qt.ItemIsAutoTristate, 'ItemIsAutoTristate'),
        (QtCore.Qt.ItemIsTristate, 'ItemIsTristate'),
        (QtCore.Qt.ItemNeverHasChildren, 'ItemNeverHasChildren'),
        #(QtCore.Qt.ItemIsUserTristate, 'ItemIsUserTristate'),
        ]

    found_bits = 0
    all_names = []
    for bit, name in all_bits:
        if (value&bit) != 0:
            found_bits |= int(bit)
            all_names.append( name )

    if found_bits != value:
        all_names.append( '0x%x' % (value&found_bits,) )

    return ', '.join( all_names )

def _indexToString( index ):
    if not index.isValid():
        return '<Index INVALID>'

    assert isinstance( index, QtCore.QModelIndex )

    item = index.internalPointer()
    return '<index row %s col %d pointer %r>' % (index.row(), index.column(), index.internalPointer())

def printResult( func ):
    def wrapper( *args, **kwds ):
        all_fragments = ['%s(' % (func.__name__,)]
        for arg in args:
            if isinstance( arg, QtCore.QModelIndex ):
                all_fragments.append( '%s,' % (_indexToString( arg ),) )

            else:
                all_fragments.append( '%s,' % (arg,) )

        all_fragments.append( ')' )

        r = func( *args, **kwds )
        if isinstance( r, QtCore.QModelIndex ):
            all_fragments.append( '-> %s' % (_indexToString( r ),) )

        elif isinstance( r, QtCore.Qt.ItemFlags ):
            all_fragments.append( '-> <ItemFlags %s>' % (decodeItemFlags( int(r) ),) )

        else:
            all_fragments.append( '-> %r' % (r,) )

        print( ' '.join( all_fragments ) )

        return r

    return wrapper


class WbDiffVisualModel(QtCore.QAbstractTableModel):
    col_diff_type = 0
    col_old_line_num = 1
    col_new_line = 2
    col_new_line_num = 3
    col_new_line = 4

    column_titles = [U_('Diff'), U_('Line'), U_('Old Line'), U_('Line'), U_('New Line')]

    def __init__( self ):
        super().__init__()

        self.all_sections = []

    def __repr__( self ):
        return '<WbDiffVisualModel>'

    @printResult
    def index( self, row, column, parent=QtCore.QModelIndex() ):
        if( row < 0
        or column < 0 or column >= len(self.column_titles)
        or (parent.isValid() and parent.column() != 0) ):
            print( '  index invalid checks' )
            return QtCore.QModelIndex()

        # return a section index
        if not parent.isValid():
            if row < len( self.all_sections ):
                return self.createIndex( row, column, self.all_sections[ row ] )

            else:
                return QtCore.QModelIndex()

        # return a line index
        print( 'zzz its a line' )
        section = parent.internalPointer()
        if row < section.rowCount():
            return self.createIndex( row, column, section.all_lines[ row ] )

        else:
            return QtCore.QModelIndex()

    @printResult
    def parent( self, index ):
        if not index.isValid():
            return QtCore.QModelIndex()

        item = index.internalPointer()
        if isinstance( item, DiffSection ):
            return QtCore.QModelIndex()

        if isinstance( item, DiffLine ):
            return self.createIndex( item.section.row, 0, item.section )

        return QtCore.QModelIndex()

    @printResult
    def flags( self, index ):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        # QQQ: is it always ItemIsSelectable?
        item = index.internalPointer()
        if isinstance( item, DiffSection ):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        if isinstance( item, DiffLine ):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        assert False

    @printResult
    def columnCount( self, parent ):
        return 2
        return len( self.column_titles )

    @printResult
    def rowCount( self, parent ):
        # is it the root?
        if not parent.isValid():
            return len( self.all_sections )

        item = parent.internalPointer()
        if isinstance( item, DiffSection ):
            return len( item.all_lines )

        if isinstance( item, DiffLine ):
            return 0

        assert False

    def headerData( self, section, orientation, role ):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return T_( self.column_titles[section] )

            elif role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignLeft

        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                if orientation == QtCore.Qt.Vertical:
                    return ''

        return None

    def data( self, index, role ):
        row = index.row()
        col = index.column()

        item = index.internalPointer()
        if isinstance( item, DiffSection ):
            if role == QtCore.Qt.DisplayRole:
                if col == self.col_diff_type:
                    return self.all_sections[ row ].diffType()

                return 'section %d/%d' % (row,col)

        if isinstance( item, DiffLine ):
            if role == QtCore.Qt.DisplayRole:
                if col == self.col_diff_type:
                    return 'qqq1'

                elif col == self.col_old_line_num:
                    return item[ row ].old_line_num

                elif col == self.col_old_line:
                    return item[ row ].old_line

                elif col == self.col_new_line_num:
                    return item[ row ].new_line_num

                elif col == self.col_new_line:
                    return item[ row ].new_line

                else:
                    return 'qqq2'

        return None

    def addSection( self, diff_type, old_line_num, all_old_lines, new_line_num, all_new_lines ):
        section = DiffSection( diff_type, len( self.all_sections ) )

        for old_line, new_line in itertools.zip_longest( all_old_lines, all_new_lines ):
            DiffLine( section, old_line_num, old_line, new_line_num, new_line )

        self.all_sections.append( section )

    def initDone( self ):
        self.beginResetModel()
        self.endResetModel()

class ModelItem:
    def __init__( self ):
        pass

class DiffSection(ModelItem):
    def __init__( self, diff_type, row ):
        super().__init__()

        self.diff_type = diff_type
        self.all_lines = []
        self.row = row

    def __repr__( self ):
        return '<DiffSection: row %d lines %d>' % (self.row, self.rowCount())

    def rowCount( self ):
        return len( self.all_lines )

    def diffType( self ):
        return self.diff_type

    def addLine( self, line ):
        line.row = len( self.all_lines )
        self.all_lines.append( line )

class DiffLine(ModelItem):
    def __init__( self, section, old_line_num, old_line, new_line_num, new_line ):
        self.section = section
        self.row = None

        super().__init__()

        if old_line is None:
            self.old_line_num = ''
            self.old_line = ''
        else:
            self.old_line_num = old_line_num
            self.old_line = old_line

        if new_line is None:
            self.new_line_num = ''
            self.new_line = ''
        else:
            self.new_line_num = new_line_num
            self.new_line = old_line

        self.section.addLine( self )

    def __repr__( self ):
        return '<DiffLine: row %d section %r>' % (self.row, self.section)

if __name__ == '__main__':
    import sys

    def T_(s):
        return s

    old_lines = open( sys.argv[1], 'r' ).readlines()
    new_lines = open( sys.argv[2], 'r' ).readlines()

    app = QtWidgets.QApplication( ['foo'] )

    view = WbDiffViewVisual( None, 'testing', None )
    view.setDiffSources( old_lines, new_lines )

    view.show()

    app.exec_()

