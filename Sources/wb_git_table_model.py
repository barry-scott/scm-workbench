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

class WbGitTableModel(QtCore.QAbstractTableModel):
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

    def data( self, index, role ):
        if role == QtCore.Qt.DisplayRole:
            entry = self.all_files[ index.row() ]

            col = index.column()

            if col == 0:
                if entry.is_dir():
                    return entry.name + os.sep

                else:
                    return entry.name

            elif col == 1:
                return time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( entry.stat().st_mtime ) )

            elif col == 2:
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
