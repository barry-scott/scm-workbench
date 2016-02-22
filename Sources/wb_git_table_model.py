'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_table_model.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import os
import time

class WbGitTableSortFilter(QtCore.QSortFilterProxyModel):
    def __init__( self, app, parent=None ):
        self.app = app
        super().__init__( parent )

    def filterAcceptsRow( self, source_row, source_parent ):
        # simple filter to lose editor backup~ files

        model = self.sourceModel()
        index = model.createIndex( source_row, WbGitTableModel.col_name )

        name = model.data( index, QtCore.Qt.DisplayRole )
        if name.endswith( '~' ):
            return False

        return True

    def lessThan( self, source_left, source_right ):
        model = self.sourceModel()
        left_ent = model.entry( source_left )
        right_ent = model.entry( source_right )

        column = source_left.column()

        if column == model.col_name:
            return left_ent.name < right_ent.name

        if column == model.col_date:
            left = (left_ent.stat().st_mtime, left_ent.name)
            right = (right_ent.stat().st_mtime, right_ent.name)

            return left < right

        if column == model.col_type:
            left = (left_ent.is_dir(), left_ent.name)
            right = (right_ent.is_dir(), right_ent.name)

            return left < right

        assert False, 'Unknown column %r' % (source_left,)

class WbGitTableModel(QtCore.QAbstractTableModel):
    col_name = 0
    col_date = 1
    col_type = 2

    column_titles = ['Name', 'Date', 'Type']

    def __init__( self, app ):
        self.app = app
        super().__init__()

        self.project = None
        self.path = None

        self.all_files = []

    def rowCount( self, parent ):
        return len( self.all_files )

    def columnCount( self, parent ):
        return len(self.column_titles)

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.column_titles[section]

            if orientation == QtCore.Qt.Vertical:
                return ''

        elif role == QtCore.Qt.TextAlignmentRole and orientation == QtCore.Qt.Horizontal:
            return QtCore.Qt.AlignLeft

        return None

    def entry( self, index ):
        return self.all_files[ index.row() ]

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            entry = self.all_files[ index.row() ]

            col = index.column()

            if col == self.col_name:
                if entry.is_dir():
                    return entry.name + os.sep

                else:
                    return entry.name

            elif col == self.col_date:
                return time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( entry.stat().st_mtime ) )

            elif col == self.col_type:
                return entry.is_dir() and 'dir' or 'file'

        return None

    def setProjectAndPath( self, project, path ):
        self.project = project
        self.path = path

        self.beginResetModel()

        if hasattr( os, 'scandir' ):
            self.all_files = sorted( os.scandir( path ) )

        else:
            self.all_files = [DirEntPre35( filename, path ) for filename in sorted( os.listdir( path ) )]

        #self.dataChanged.emit( self.createIndex( 0, 0 ), self.createIndex( len(self.all_files), len(self.column_titles) ) )
        self.endResetModel()

class DirEntPre35:
    def __init__( self, filename, parent ):
        self.name = filename
        self.__full_path = os.path.join( parent, filename )
        self.__stat = os.stat( self.__full_path )

    def stat( self ):
        return self.__stat

    def is_dir( self ):
        import stat
        return stat.S_ISDIR( self.__stat.st_mode )
