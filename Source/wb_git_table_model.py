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

import pygit2

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

        if column == model.col_cache:
            return left_ent.name < right_ent.name

        if column == model.col_working:
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
    col_cache = 0
    col_working = 1
    col_name = 2
    col_date = 3
    col_type = 4

    column_titles = ['Cache', 'Working', 'Name', 'Date', 'Type']

    def __init__( self, app ):
        self.app = app
        super().__init__()

        self.project = None
        self.path = None

        self.all_files = []

    def rowCount( self, parent ):
        return len( self.all_files )

    def columnCount( self, parent ):
        return len( self.column_titles )

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
        if role == QtCore.Qt.UserRole:
            return self.all_files[ index.row() ]

        if role == QtCore.Qt.DisplayRole:
            entry = self.all_files[ index.row() ]

            col = index.column()

            if col == self.col_cache:
                return entry.cacheAsString()

            elif col == self.col_working:
                return entry.workingAsString()

            elif col == self.col_name:
                if entry.is_dir():
                    return entry.name + os.sep

                else:
                    return entry.name

            elif col == self.col_date:
                return entry.fileDate()

            elif col == self.col_type:
                return entry.is_dir() and 'dir' or 'file'

        return None

    def setGitProjectTreeNode( self, git_project_tree_node ):
        self.git_project_tree_node = git_project_tree_node

        self.beginResetModel()

        all_files = {}
        for dirent in os_scandir( str( git_project_tree_node.path() ) ):
            entry = WbGitTableEntry( dirent.name )
            entry.updateFromDirEnt( dirent )
            
            all_files[ entry.name ] = entry

        for name in self.git_project_tree_node.all_files.keys():
            if name not in all_files:
                entry = WbGitTableEntry( name )

            else:
                entry = all_files[ name ]

            entry.updateFromGit( self.git_project_tree_node.state( name ) )

            all_files[ entry.name ] = entry

        self.all_files = sorted( all_files.values() )

        self.endResetModel()

class WbGitTableEntry:
    def __init__( self, name ):
        self.name = name
        self.dirent = None
        self.status = None

    def updateFromDirEnt( self, dirent ):
        self.dirent = dirent

    def updateFromGit( self, status ):
        self.status = status

    def stat( self ):
        return self.dirent.stat()

    def __lt__( self, other ):
        return self.name < other.name

    def is_dir( self ):
        return self.dirent is not None and self.dirent.is_dir()

    def fileDate( self ):
        if self.dirent is None:
            return '-'

        else:
            return time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime( self.dirent.stat().st_mtime ) )



    def cacheAsString( self ):
        '''
GIT_STATUS_CONFLICTED: 0x8000
GIT_STATUS_CURRENT: 0x0
GIT_STATUS_IGNORED: 0x4000
GIT_STATUS_INDEX_DELETED: 0x4
GIT_STATUS_INDEX_MODIFIED: 0x2
GIT_STATUS_INDEX_NEW: 0x1
GIT_STATUS_WT_DELETED: 0x200
GIT_STATUS_WT_MODIFIED: 0x100
GIT_STATUS_WT_NEW: 0x80
'''
        if self.status is None:
            return ''

        status = self.status[1]
        state = []

        if status&pygit2.GIT_STATUS_INDEX_NEW:
            state.append( 'A' )

        elif status&pygit2.GIT_STATUS_INDEX_MODIFIED:
            state.append( 'M' )

        elif status&pygit2.GIT_STATUS_INDEX_DELETED:
            state.append( 'D' )

        return ''.join( state )

    def workingAsString( self ):
        if self.status is None:
            return ''

        status = self.status[1]
        state = []

        if status&pygit2.GIT_STATUS_CONFLICTED:
            state.append( 'C' )

        if status&pygit2.GIT_STATUS_WT_MODIFIED:
            state.append( 'M' )

        elif status&pygit2.GIT_STATUS_WT_DELETED:
            state.append( 'D' )

        return ''.join( state )

def os_scandir( path ):
    if hasattr( os, 'scandir' ):
        return os.scandir( path )

    return [DirEntPre35( filename, path ) for filename in os.listdir( path )]

class DirEntPre35:
    def __init__( self, name, parent ):
        self.name = name
        self.__full_path = os.path.join( parent, name )
        self.__stat = os.stat( self.__full_path )

    def stat( self ):
        return self.__stat

    def is_dir( self ):
        import stat
        return stat.S_ISDIR( self.__stat.st_mode )
