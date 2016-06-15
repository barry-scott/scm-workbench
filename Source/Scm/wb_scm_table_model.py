'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_table_model.py

'''
from PyQt5 import QtGui
from PyQt5 import QtCore

import os
import time

class WbScmTableSortFilter(QtCore.QSortFilterProxyModel):
    def __init__( self, app, parent=None ):
        self.app = app
        super().__init__( parent )

        self.filter_text = ''

        self.show_controlled = True
        self.show_uncontrolled = True
        self.show_ignored = False
        self.show_only_changed = False

    def setFilterText( self, text ):
        self.filter_text = text
        self.invalidateFilter()

    def setShowControllerFiles( self, state ):
        self.show_controlled = state
        self.invalidateFilter()

    def setShowUncontrolledFiles( self, state ):
        self.show_uncontrolled = state
        self.invalidateFilter()

    def setShowIgnoredFiles( self, state ):
        self.show_ignored = state
        self.invalidateFilter()

    def setShowOnlyChangedFiles( self, state ):
        self.show_only_changed = state
        self.invalidateFilter()

    def filterAcceptsRow( self, source_row, source_parent ):
        model = self.sourceModel()
        index = model.createIndex( source_row, WbScmTableModel.col_name )

        entry = model.data( index, QtCore.Qt.UserRole )

        if entry.controlledFile() and not self.show_controlled:
            return False

        if entry.uncontrolledFile() and not self.show_uncontrolled:
            return False

        if entry.ignoreFile() and not self.show_ignored:
            return False

        if (entry.stagedAsString() != '' or entry.statusAsString() !=0) and not self.show_only_changed:
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

        if column in (model.col_staged, model.col_status):
            # cached first
            left = left_ent.stagedAsString()
            right = right_ent.stagedAsString()
            if left != right:
                return left > right

            # then working changes
            left = left_ent.statusAsString()
            right = right_ent.statusAsString()
            if left != right:
                return left > right

            left = left_ent.isWorkingNew()
            right = right_ent.isWorkingNew()
            if left != right:
                return left < right

            left = left_ent.ignoreFile()
            right = right_ent.ignoreFile()
            if left != right:
                return left < right

            # finally in name order
            return left_ent.name < right_ent.name

        if column == model.col_status:
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

class WbScmTableModel(QtCore.QAbstractTableModel):
    col_staged = 0
    col_status = 1
    col_name = 2
    col_date = 3
    col_type = 4

    column_titles = [U_('Staged'), U_('Status'), U_('Name'), U_('Date'), U_('Type')]

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debugTableModel

        super().__init__()

        self.scm_project_tree_node = None

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

            if col == self.col_staged:
                return entry.stagedAsString()

            elif col == self.col_status:
                return entry.statusAsString()

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
            cached = entry.stagedAsString()
            working = entry.statusAsString()

            if cached != '':
                return self.__brush_is_cached

            if working != '':
                return self.__brush_is_working_changed

            if entry.isWorkingNew():
                return self.__brush_working_new

            return None

        #if role == QtCore.Qt.BackgroundRole:

        return None

    def setScmProjectTreeNode( self, scm_project_tree_node ):
        self.refreshTable( scm_project_tree_node )

    def refreshTable( self, scm_project_tree_node=None ):
        self._debug( 'WbScmTableModel.refreshTable( %r ) start' % (scm_project_tree_node,) )
        self._debug( 'WbScmTableModel.refreshTable() self.scm_project_tree_node %r' % (self.scm_project_tree_node,) )

        if scm_project_tree_node is None:
            scm_project_tree_node = self.scm_project_tree_node

        # find all the files know to the SCM and the folder
        all_files = {}
        for dirent in os_scandir( str( scm_project_tree_node.absolutePath() ) ):
            entry = WbScmTableEntry( dirent.name )
            entry.updateFromDirEnt( dirent )
            
            all_files[ entry.name ] = entry

        for name in scm_project_tree_node.getAllFileNames():
            if name not in all_files:
                entry = WbScmTableEntry( name )

            else:
                entry = all_files[ name ]

            entry.updateFromScm( scm_project_tree_node.getStatusEntry( name ) )

            all_files[ entry.name ] = entry

        if( self.scm_project_tree_node is None
        or self.scm_project_tree_node.isNotEqual( scm_project_tree_node ) ):
            self._debug( 'WbScmTableModel.refreshTable() resetModel' )
            self.beginResetModel()
            self.all_files = sorted( all_files.values() )
            self.endResetModel()

        else:
            parent = QtCore.QModelIndex()
            self._debug( 'WbScmTableModel.refreshTable() insert/remove' )

            all_new_files = sorted( all_files.values() )

            all_old_names = [entry.name for entry in self.all_files]
            all_new_names = [entry.name for entry in all_new_files]

            for offset in range( len(self.all_files) ):
                self._debug( 'old %2d %s' % (offset, all_old_names[ offset ]) )

            for offset in range( len(all_new_files) ):
                self._debug( 'new %2d %s' % (offset, all_new_names[ offset ]) )

            offset = 0
            while offset < len(all_new_files) and offset < len(self.all_files):
                self._debug( 'WbScmTableModel.refreshTable() while offset %d %s old %s' %
                        (offset, all_new_files[ offset ].name, self.all_files[ offset ].name) )
                if all_new_files[ offset ].name == self.all_files[ offset ].name:
                    if all_new_files[ offset ].isNotEqual( self.all_files[ offset ] ):
                        self._debug( 'WbScmTableModel.refreshTable() emit dataChanged row=%d' % (offset,) )
                        self.dataChanged.emit(
                            self.createIndex( offset, self.col_staged ),
                            self.createIndex( offset, self.col_type ) )
                    offset += 1

                elif all_new_files[ offset ].name < self.all_files[ offset ].name:
                    self._debug( 'WbScmTableModel.refreshTable() insertRows row=%d %r' % (offset, all_new_names[offset]) )
                    self.beginInsertRows( parent, offset, offset )
                    self.all_files.insert( offset, all_new_files[ offset ] )
                    self.endInsertRows()
                    offset += 1

                else:
                    self._debug( 'WbScmTableModel.refreshTable() deleteRows row=%d %r' % (offset, all_old_names[ offset ]) )
                    # delete the old
                    self.beginRemoveRows( parent, offset, offset )
                    del self.all_files[ offset ]
                    del all_old_names[ offset ]
                    self.endRemoveRows()

            if offset < len(self.all_files):
                self._debug( 'WbScmTableModel.refreshTable() removeRows at end of old row=%d %r' % (offset, all_old_names[ offset: ]) )

                self.beginRemoveRows( parent, offset, len(self.all_files)-1 )
                del self.all_files[ offset: ]
                self.endRemoveRows()

            if offset < len(all_new_files):
                self._debug( 'WbScmTableModel.refreshTable() insertRows at end of new row=%d %r, old row %s' % (offset, all_new_names[offset:], offset) )

                to_insert = len(all_new_files) - offset - 1
                self.beginInsertRows( parent, offset, offset + to_insert )
                self.all_files.extend( all_new_files[offset:] )
                self.endInsertRows()

            self.all_files = sorted( all_files.values() )

        self.scm_project_tree_node = scm_project_tree_node
        self._debug( 'WbScmTableModel.refreshTable() done self.scm_project_tree_node %r' % (self.scm_project_tree_node,) )

class WbScmTableEntry:
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

    def updateFromScm( self, status ):
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

    def controlledFile( self ):
        if self.status is not None and not self.status.isIgnored():
            return True

        return False

    def uncontrolledFile( self ):
        if self.status is None:
            return True

    def ignoreFile( self ):
        if self.status is None:
            return True

        if self.status.isIgnored():
            return True

        return False

    def stagedAsString( self ):
        if self.status is None:
            return ''

        return self.status.getStagedAbbreviatedStatus()

    def statusAsString( self ):
        if self.status is None:
            return ''

        return self.status.getUnstagedAbbreviatedStatus()

    def isWorkingNew( self ):
        if self.status is None:
            return False

        return self.status.isUntracked()

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
