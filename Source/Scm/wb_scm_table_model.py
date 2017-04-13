'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_table_model.py

'''
import os

from PyQt5 import QtGui
from PyQt5 import QtCore

def U_( s: str ) -> str:
    return s

class WbScmTableSortFilter(QtCore.QSortFilterProxyModel):
    def __init__( self, app, parent=None ):
        self.app = app
        super().__init__( parent )

        self.filter_text = ''

        self.show_controlled_and_changed = True
        self.show_controlled_and_not_changed = True
        self.show_uncontrolled = True
        self.show_ignored = False

    # ------------------------------------------------------------
    def setFilterText( self, text ):
        self.filter_text = text
        # invalidateFilter is documented to update the view with the
        # filter conditions are changed but it does not work
        # when filter puts more items into the result
        self.invalidate()

    # ------------------------------------------------------------
    def filterAcceptsRow( self, source_row, source_parent ):
        model = self.sourceModel()
        index = model.createIndex( source_row, WbScmTableModel.col_name )

        entry = model.data( index, QtCore.Qt.UserRole )

        changed = entry.stagedAsString() != '' or entry.statusAsString() != ''
        not_changed = entry.stagedAsString() == '' and entry.statusAsString() == ''

        if entry.is_dir():
            return False

        if entry.isControlled() and changed and not self.show_controlled_and_changed:
            return False

        if entry.isControlled() and not_changed and not self.show_controlled_and_not_changed:
            return False

        if entry.isUncontrolled() and not self.show_uncontrolled:
            return False

        if entry.isIgnore() and not self.show_ignored:
            return False

        if self.filter_text != '':
            return self.filter_text.lower() in str(entry.name).lower()

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

            left = left_ent.isControlled()
            right = right_ent.isControlled()
            if left != right:
                return left > right

            left = left_ent.isIgnore()
            right = right_ent.isIgnore()
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
    col_include = 0
    col_staged = 1
    col_status = 2
    col_name = 3
    col_date = 4
    col_type = 5
    col_num_columns = 6

    column_titles = (U_('Commit'), U_('Staged'), U_('Status'), U_('Name'), U_('Date'), U_('Type'))

    def __init__( self, app ):
        self.app = app

        self._debug = self.app._debug_options._debugTableModel

        super().__init__()

        self.scm_project_tree_node = None

        self.all_files = []
        self.all_included_files = None

        self.__brush_is_cached = QtGui.QBrush( QtGui.QColor( 255, 0, 255 ) )
        self.__brush_is_changed = QtGui.QBrush( QtGui.QColor( 0, 0, 255 ) )
        self.__brush_is_uncontrolled = QtGui.QBrush( QtGui.QColor( 0, 128, 0 ) )

    def isByPath( self ):
        return self.scm_project_tree_node is not None and self.scm_project_tree_node.isByPath()

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

            if col == self.col_include:
                return 'X' if entry.name in self.all_included_files else ''

            elif col == self.col_staged:
                return entry.stagedAsString()

            elif col == self.col_status:
                return entry.statusAsString()

            elif col == self.col_name:
                # entry.name maybe a pathlib.Path object
                name = str(entry.name)

                if entry.is_dir():
                    return name + os.sep

                elif entry.is_symlink():
                    return name + '@'

                else:
                    # name can be a
                    return name

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
                return self.__brush_is_changed

            if not entry.isControlled():
                return self.__brush_is_uncontrolled

        #if role == QtCore.Qt.BackgroundRole:

        return None

    def setIncludedFilesSet( self, all_included_files ):
        self.all_included_files = all_included_files

    def setScmProjectTreeNode( self, scm_project_tree_node ):
        self.refreshTable( scm_project_tree_node )

    def refreshTable( self, scm_project_tree_node=None ):
        self._debug( 'WbScmTableModel.refreshTable( %r ) start' % (scm_project_tree_node,) )
        self._debug( 'WbScmTableModel.refreshTable() self.scm_project_tree_node %r' % (self.scm_project_tree_node,) )

        if scm_project_tree_node is None:
            scm_project_tree_node = self.scm_project_tree_node

        # find all the files know to the SCM and the folder
        all_files = {}
        if scm_project_tree_node.absolutePath().exists():
            if not scm_project_tree_node.isByPath():
                # skip scanning the file system for now
                folder = scm_project_tree_node.absolutePath()
                for dirent in os_scandir( str( folder ) ):
                    entry = WbScmTableEntry( self.app, dirent.name )
                    entry.updateFromDirEnt( dirent )

                    all_files[ entry.name ] = entry

        for name in scm_project_tree_node.getAllFileNames():
            if name not in all_files:
                entry = WbScmTableEntry( self.app, name )

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

            # see if self.all_included_files needs setting up
            if self.all_included_files is not None:
                for entry in self.all_files:
                    if entry.canCommit():
                        self.all_included_files.add( entry.name )

            else:
                self.all_included_files = set()

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
                    self._debug( 'WbScmTableModel.refreshTable() deleteRows row=%d' % (offset,) )
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

    def selectedScmProjectTreeNode( self ):
        return self.scm_project_tree_node

    def absoluteNodePath( self ):
        if self.scm_project_tree_node is None:
            return None

        return self.scm_project_tree_node.absolutePath()

    def relativeNodePath( self ):
        if self.scm_project_tree_node is None:
            return None

        return self.scm_project_tree_node.relativePath()

class WbScmTableEntry:
    def __init__( self, app, name ):
        self.app = app
        self.name = name
        self.dirent = None
        self.status = None

    def __repr__( self ):
        return '<WbScmTableEntry: n: %r s: %r>' % (self.name, self.status)

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

    def is_symlink( self ):
        return self.dirent is not None and self.dirent.is_symlink()

    def fileDate( self ):
        if self.dirent is None:
            return '-'

        else:
            try:
                return self.app.formatDatetime( self.dirent.stat( follow_symlinks=not self.dirent.is_symlink() ).st_mtime )

            except FileNotFoundError:
                return '-'

    # ------------------------------------------------------------
    def isControlled( self ):
        return self.status is not None and self.status.isControlled()

    def isUncontrolled( self ):
        return self.status is not None and self.status.isUncontrolled()

    def isIgnore( self ):
        return self.status is not None and self.status.isIgnored()

    def canCommit( self ):
        return self.status is not None and self.status.canCommit()

    # ------------------------------------------------------------
    def stagedAsString( self ):
        if self.status is None:
            return ''

        return self.status.getStagedAbbreviatedStatus()

    def statusAsString( self ):
        if self.status is None:
            return ''

        return self.status.getUnstagedAbbreviatedStatus()

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
