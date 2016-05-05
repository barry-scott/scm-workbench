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

        self.filter_text = ''

    def setFilterText( self, text ):
        self.filter_text = text
        self.invalidateFilter()

    def filterAcceptsRow( self, source_row, source_parent ):
        model = self.sourceModel()
        index = model.createIndex( source_row, WbGitTableModel.col_name )

        entry = model.data( index, QtCore.Qt.UserRole )
        if entry.ignoreFile():
            return False

        if self.filter_text != '':
            return self.filter_text.lower() in entry.name.lower()

        return True

    def lessThan( self, source_left, source_right ):
        model = self.sourceModel()
        left_ent = model.entry( source_left )
        right_ent = model.entry( source_right )

        column = source_left.column()

        if column == model.col_name:
            return left_ent.name < right_ent.name

        if column in (model.col_cache, model.col_working):
            # cached first
            left = left_ent.cacheAsString()
            right = right_ent.cacheAsString()
            if left != right:
                return left > right

            # then working changesabrt-CCpp.conf
            left = left_ent.workingAsString()
            right = right_ent.workingAsString()
            if left != right:
                return left > right

            left = left_ent.isWorkingNew()
            right = right_ent.isWorkingNew()
            if left != right:
                return left < right

            # finally in name order
            return left_ent.name < right_ent.name

        if column == model.col_working:
            if left == right:
                return left_ent.name < right_ent.name

            return left > right

        if column == model.col_date:
            left = (left_ent.stat().st_mtime, left_ent.name)
            right = (right_ent.stat().st_mtime, right_ent.name)

            return left < right

        if column == model.col_type:
            left = (left_ent.is_dir(), left_ent.name)
            right = (right_ent.is_dir(), right_ent.name)

            return left < right

        assert False, 'Unknown column %r' % (source_left,)

    def indexListFromNameList( self, all_names ):
        if len(all_names) == 0:
            return []

        model = self.sourceModel()

        all_indices = []
        for row in range( self.rowCount( QtCore.QModelIndex() ) ):
            index = self.createIndex( row, 0 )
            entry = model.data( index, QtCore.Qt.UserRole )
            if entry.name in all_names:
                all_indices.append( index )

        return all_indices

class WbGitTableModel(QtCore.QAbstractTableModel):
    col_cache = 0
    col_working = 1
    col_name = 2
    col_date = 3
    col_type = 4

    column_titles = [U_('Cache'), U_('Working'), U_('Name'), U_('Date'), U_('Type')]

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugTableModel

        super().__init__()

        self.git_project_tree_node = None

        self.all_files = []

        self.__brush_working_new = QtGui.QBrush( QtGui.QColor( 0, 128, 0 ) )
        self.__brush_is_cached = QtGui.QBrush( QtGui.QColor( 255, 0, 255 ) )
        self.__brush_is_working_changed = QtGui.QBrush( QtGui.QColor( 0, 0, 255 ) )

    def rowCount( self, parent ):
        return len( self.all_files )

    def columnCount( self, parent ):
        return len( self.column_titles )

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return T_( self.column_titles[section] )

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
                return entry.is_dir() and 'Dir' or 'File'

            assert False

        elif role == QtCore.Qt.ForegroundRole:
            entry = self.all_files[ index.row() ]
            cached = entry.cacheAsString()
            working = entry.workingAsString()

            if cached != '':
                return self.__brush_is_cached

            if working != '':
                return self.__brush_is_working_changed

            if entry.isWorkingNew():
                return self.__brush_working_new

            return None

        #if role == QtCore.Qt.BackgroundRole:

        return None

    def setGitProjectTreeNode( self, git_project_tree_node ):
        self.refreshTable( git_project_tree_node )

    def refreshTable( self, git_project_tree_node=None ):
        self._debug( 'WbGitTableModel.refreshTable( %r ) start' % (git_project_tree_node,) )
        self._debug( 'WbGitTableModel.refreshTable() self.git_project_tree_node %r' % (self.git_project_tree_node,) )

        if git_project_tree_node is None:
            git_project_tree_node = self.git_project_tree_node

        all_files = {}
        for dirent in os_scandir( str( git_project_tree_node.absolutePath() ) ):
            entry = WbGitTableEntry( dirent.name )
            entry.updateFromDirEnt( dirent )
            
            all_files[ entry.name ] = entry

        for name in git_project_tree_node.all_files.keys():
            if name not in all_files:
                entry = WbGitTableEntry( name )

            else:
                entry = all_files[ name ]

            entry.updateFromGit( git_project_tree_node.state( name ) )

            all_files[ entry.name ] = entry

        if( self.git_project_tree_node is None
        or self.git_project_tree_node.isNotEqual( git_project_tree_node ) ):
            self._debug( 'WbGitTableModel.refreshTable() resetModel' )
            self.beginResetModel()
            self.all_files = sorted( all_files.values() )
            self.endResetModel()

        else:
            parent = QtCore.QModelIndex()
            self._debug( 'WbGitTableModel.refreshTable() insert/remove' )

            all_new_files = sorted( all_files.values() )

            all_old_names = [entry.name for entry in self.all_files]
            all_new_names = [entry.name for entry in all_new_files]

            for offset in range( len(self.all_files) ):
                self._debug( 'old %2d %s' % (offset, all_old_names[ offset ]) )

            for offset in range( len(all_new_files) ):
                self._debug( 'new %2d %s' % (offset, all_new_names[ offset ]) )

            offset = 0
            while offset < len(all_new_files) and offset < len(self.all_files):
                self._debug( 'WbGitTableModel.refreshTable() while offset %d %s old %s' %
                        (offset, all_new_files[ offset ].name, self.all_files[ offset ].name) )
                if all_new_files[ offset ].name == self.all_files[ offset ].name:
                    if all_new_files[ offset ].isNotEqual( self.all_files[ offset ] ):
                        self._debug( 'WbGitTableModel.refreshTable() emit dataChanged row=%d' % (offset,) )
                        self.dataChanged.emit(
                            self.createIndex( offset, self.col_cache ),
                            self.createIndex( offset, self.col_type ) )
                    offset += 1

                elif all_new_files[ offset ].name < self.all_files[ offset ].name:
                    self._debug( 'WbGitTableModel.refreshTable() insertRows row=%d %r' % (offset, all_new_names[offset]) )
                    self.beginInsertRows( parent, offset, offset )
                    self.all_files.insert( offset, all_new_files[ offset ] )
                    self.endInsertRows()
                    offset += 1

                else:
                    self._debug( 'WbGitTableModel.refreshTable() deleteRows row=%d %r' % (offset, all_old_names[ offset ]) )
                    # delete the old
                    self.beginRemoveRows( parent, offset, offset )
                    del self.all_files[ offset ]
                    del all_old_names[ offset ]
                    self.endRemoveRows()

            if offset < len(self.all_files):
                self._debug( 'WbGitTableModel.refreshTable() removeRows at end of old row=%d %r' % (offset, all_old_names[ offset: ]) )

                self.beginRemoveRows( parent, offset, len(self.all_files)-1 )
                del self.all_files[ offset: ]
                self.endRemoveRows()

            if offset < len(all_new_files):
                self._debug( 'WbGitTableModel.refreshTable() insertRows at end of new row=%d %r, old row %s' % (offset, all_new_names[offset:], offset) )

                to_insert = len(all_new_files) - offset - 1
                self.beginInsertRows( parent, offset, offset + to_insert )
                self.all_files.extend( all_new_files[offset:] )
                self.endInsertRows()

            self.all_files = sorted( all_files.values() )

        self.git_project_tree_node = git_project_tree_node
        self._debug( 'WbGitTableModel.refreshTable() done self.git_project_tree_node %r' % (self.git_project_tree_node,) )

class WbGitTableEntry:
    def __init__( self, name ):
        self.name = name
        self.dirent = None
        self.status = None

    def isNotEqual( self, other ):
        return (self.name != other.name
            or self.status != other.status
            or self.dirent != self.dirent)

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

    def ignoreFile( self ):
        if self.status is None:
            return True

        return (self.status[1]&pygit2.GIT_STATUS_IGNORED) != 0

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

        if status&pygit2.GIT_STATUS_INDEX_NEW:
            return 'A'

        elif status&pygit2.GIT_STATUS_INDEX_MODIFIED:
            return 'M'

        elif status&pygit2.GIT_STATUS_INDEX_DELETED:
            return 'D'

        else:
            return ''

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

    def isWorkingNew( self ):
        if self.status is None:
            return False

        if self.status[1]&pygit2.GIT_STATUS_WT_NEW:
            return True

        return False

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
