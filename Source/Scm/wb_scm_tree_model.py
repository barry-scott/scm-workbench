'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_tree_model.py

'''
from PyQt6 import QtGui
from PyQt6 import QtCore

import wb_scm_project_place_holder

from wb_background_thread import thread_switcher

class WbScmTreeSortFilter(QtCore.QSortFilterProxyModel):
    def __init__( self, app, main_window, parent=None ):
        self.app = app
        self.main_window = main_window

        super().__init__( parent )

    def lessThan( self, source_left, source_right ):
        if not source_left.isValid() or not source_right.isValid():
            return True

        model = self.sourceModel()

        left_ent = model.itemFromIndex( source_left )
        right_ent = model.itemFromIndex( source_right )

        return left_ent.text().lower() > right_ent.text().lower()

    def selectionChanged( self, selected, deselected ):
        self.app.wrapWithThreadSwitcher( self.main_window.treeSelectionChanged_Bg, 'sort filter SelectionChanged' )(
                self.mapSelectionToSource( selected ),
                self.mapSelectionToSource( deselected ) )

class WbScmTreeModel(QtGui.QStandardItemModel):
    def __init__( self, app, table_model ):
        assert table_model is not None
        self.app = app
        self.debugLog = self.app.debug_options.debugLogTreeModel
        self.debugLogNode = self.app.debug_options.debugLogTreeModelNode

        self.table_model = table_model

        super().__init__()

        self.all_scm_projects = {}

        self.debugLog( 'WbScmTreeModel.__init__ self.selected_node = None' )
        self.selected_node = None

    def addProject( self, project ):
        scm_project = self.app.top_window.createProject( project )
        if scm_project is None:
            scm_project = wb_scm_project_place_holder.ScmProjectPlaceholder( self.app, project )

        tree_node = ProjectTreeNode( self, scm_project.tree )
        self.all_scm_projects[ scm_project.tree.name ] = (scm_project, tree_node)
        self.appendRow( tree_node )

    def delProject( self, project_name ):
        item = self.invisibleRootItem()

        row = 0
        while True:
            child = item.child( row )

            if child is None:
                # not found
                return

            if child.text() == project_name:
                break

            row += 1

        self.removeRow( row, QtCore.QModelIndex() )

    @thread_switcher
    def refreshTree_Bg( self, folder=None ):
        self.debugLog( 'refreshTree_Bg( %r ) selected_node %r' % (folder, self.selected_node) )
        if self.selected_node is None:
            return

        scm_project = self.selected_node.scm_project_tree_node.project
        self.app.top_window.setStatusAction( T_('Update status of %s') % (scm_project.projectName(),) )
        yield self.app.switchToBackground

        # update the project data
        if folder is None:
            folder = self.selected_node.scm_project_tree_node.relativePath()

        scm_project.updateState( folder )

        yield self.app.switchToForeground

        self.app.top_window.setStatusAction()

        # add new nodes
        scm_project, tree_node = self.all_scm_projects[ scm_project.tree.name ]

        # reset the table model
        tree_node.update( scm_project.tree )

        # can arrive here and self.selected_node is None
        if self.selected_node is not None:
            self.table_model.setScmProjectTreeNode( self.selected_node.scm_project_tree_node )
        self.debugLog( 'refreshTree_Bg() Done' )

    def getFirstProjectIndex( self ):
        if self.invisibleRootItem().rowCount() == 0:
            return None

        item = self.invisibleRootItem().child( 0 )
        return self.indexFromItem( item )

    def getFirstProjectName( self ):
        if self.invisibleRootItem().rowCount() == 0:
            return None

        item = self.invisibleRootItem().child( 0 )
        return item.text()

    def indexFromProject( self, project ):
        item = self.invisibleRootItem()

        row = 0
        while True:
            child = item.child( row )

            if child is None:
                return None

            if child.text() == project.name:
                item = child
                break

            row += 1

        return self.indexFromItem( item )

    def indexFromFavorite( self, favorite ):
        item = self.invisibleRootItem()

        project = self.app.prefs.getProjectByPath( favorite.project_path )

        for name in [project.name] + list( favorite.path.parts ):
            row = 0
            while True:
                child = item.child( row )

                if child is None:
                    return None

                if child.text() == name:
                    item = child
                    break

                row += 1

        return self.indexFromItem( item )

    def headerData( self, section, orientation, role ):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return T_('Project')

            if orientation == QtCore.Qt.Orientation.Vertical:
                return ''

        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole and orientation == QtCore.Qt.Orientation.Horizontal:
            return QtCore.Qt.AlignmentFlag.AlignCenter

        return None

    def flags( self, index ):
        # turn off edit as that stops double click to expand
        return super().flags( index ) & ~QtCore.Qt.ItemFlag.ItemIsEditable

    def selectionChanged( self, selected, deselected ):
        self.debugLog( 'selectionChanged:   selected %r' % ([(index.row(), index.column()) for index in selected.indexes()],) )
        self.debugLog( 'selectionChanged: deselected %r' % ([(index.row(), index.column()) for index in deselected.indexes()],) )
        super().selectionChanged( selected, deselected )
        self.debugLog( 'selectionChanged calling selectionChanged_Bg' )
        self.app.wrapWithThreadSwitcher( self.selectionChanged_Bg, 'treeModel selectionChanged' )( selected, deselected )

    @thread_switcher
    def selectionChanged_Bg( self, selected, deselected ):
        self.debugLog( 'selectionChanged_Bg()' )
        all_selected = selected.indexes()
        self.debugLog( 'selectionChanged_Bg() all_selected %r' % ([(index.row(), index.column()) for index in all_selected],) )
        if len( all_selected ) == 0:
            self.selected_node = None
            self.debugLog( 'selectionChanged_Bg() nothing selected self.selected_node = None' )
            return

        index = selected.indexes()[0]
        self.debugLog( 'selectionChanged() index row %r col %r' % (index.row(), index.column()) )
        selected_node = self.itemFromIndex( index )

        if selected_node is None:
            self.debugLog( 'selectionChanged() cannot get item' )
            return

        self.debugLog( 'selectionChanged() selected_node %r' % (selected_node,) )

        need_to_refresh = False
        if self.selected_node is not None:
            old_project = self.selected_node.scm_project_tree_node.project
            new_project = selected_node.scm_project_tree_node.project
            if old_project != new_project:
                need_to_refresh = True

        self.debugLog( 'selectionChanged() self.selected_node = %r' % (selected_node,) )
        self.selected_node = selected_node

        if need_to_refresh:
            self.debugLog( 'selectionChanged() calling refreshTree_Bg' )
            yield from self.refreshTree_Bg()

            self.app.top_window.setStatusAction()

        else:
            yield self.app.switchToBackground
            self.selected_node.scm_project_tree_node.updateTreeNode()

            yield self.app.switchToForeground
            self.table_model.setScmProjectTreeNode( self.selected_node.scm_project_tree_node )

            # add new nodes
            scm_project, tree_node = self.all_scm_projects[ selected_node.scm_project_tree_node.project.tree.name ]

            # reset the table model
            tree_node.update( scm_project.tree )

    def selectedScmProjectTreeNode( self ):
        if self.selected_node is None:
            return None

        return self.selected_node.scm_project_tree_node

class ProjectTreeNode(QtGui.QStandardItem):
    def __init__( self, model, scm_project_tree_node ):
        self.model = model
        self.debugLog = self.model.debugLogNode

        self.scm_project_tree_node = scm_project_tree_node

        super().__init__( self.scm_project_tree_node.name )

        for tree in sorted( self.scm_project_tree_node.getAllFolderNodes() ):
            self.appendRow( ProjectTreeNode( self.model, tree ) )

    def __repr__( self ):
        return '<ProjectTreeNode: %s>' % (self.text(),)

    def update( self, scm_project_tree_node, indent=0 ):
        # replace the old scm_project_tree_node with the new one from updateStatus()
        self.scm_project_tree_node = scm_project_tree_node

        self.debugLog( '%*sProjectTreeNode.update name %s' % (indent, '', self.text()) )

        self.debugLog( '%*sProjectTreeNode.update all_folders %r' % (indent, '', list( scm_project_tree_node.getAllFolderNames() )) )

        # do the deletes first
        all_row_names = set()
        row = 0
        while row < self.rowCount():
            item = self.child( row )
            self.debugLog( '%*sProjectTreeNode.update row %d child %s' % (indent, '', row, item.text()) )
            if not scm_project_tree_node.hasFolder( item.text() ):
                self.debugLog( '%*sProjectTreeNode.update remove row %d child %s' % (indent, '', row, item.text()) )
                self.removeRow( row )

            else:
                # recursive update of the whole tree
                item.update( scm_project_tree_node.getFolder( item.text() ), indent+4 )

                all_row_names.add( item.text() )
                row += 1

        # do the inserts now
        all_new_row_names = set( scm_project_tree_node.getAllFolderNames() )

        all_to_add = all_new_row_names - all_row_names
        # sort to make sure order is not swapped
        for name in sorted( all_to_add ):
            self.debugLog( '%*sProjectTreeNode.update add name %s' % (indent, '', name,) )
            self.appendRow( ProjectTreeNode( self.model, self.scm_project_tree_node.getFolder( name ) ) )
