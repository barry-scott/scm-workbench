'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_tree_model.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import os

import wb_git_project

class WbGitTreeModel(QtGui.QStandardItemModel):
    def __init__( self, app, table_model ):
        self.app = app
        self._debug = self.app._debugTreeModel
        self.table_model = table_model

        super().__init__()

        self.all_git_projects = {}

        self.selected_node = None

        for project in self.app.prefs.getProjects().getProjectList():
            self.addProject( project )

    def addProject( self, project ):
        git_project = wb_git_project.GitProject( self.app, project )
        git_project.updateState()

        tree_node = ProjectTreeNode( self, git_project.tree )
        self.all_git_projects[ git_project.tree.name ] = (git_project, tree_node)
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

    def refreshTree( self ):
        self._debug( 'WbGitTreeModel.refreshTree()' )
        if self.selected_node is None:
            return

        # update the project data and reset the table model
        project = self.selected_node.git_project_tree_node.project
        project.updateState()

        # add new nodes
        git_project, tree_node = self.all_git_projects[ project.tree.name ]

        tree_node.update( git_project.tree )

        self.table_model.setGitProjectTreeNode( self.selected_node.git_project_tree_node )

    def getFirstProjectIndex( self ):
        if self.invisibleRootItem().rowCount() == 0:
            return None

        item = self.invisibleRootItem().child( 0 )
        return self.indexFromItem( item )

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

    def indexFromBookmark( self, bookmark ):
        item = self.invisibleRootItem()

        for name in [bookmark.project] + list( bookmark.path.parts ):

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
        return None

    def flags( self, index ):
        # turn off edit as that stops double click to expand
        return super().flags( index ) & ~QtCore.Qt.ItemIsEditable

    def appActiveHandler( self ):
        self.refreshTree()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'selectChanged()' )
        all_selected = selected.indexes()
        if len( all_selected ) == 0:
            self.selected_node = None
            return

        index = selected.indexes()[0]
        selected_node = self.itemFromIndex( index )

        if selected_node is None:
            return

        need_to_refresh = False
        if self.selected_node is not None:
            old_project = self.selected_node.git_project_tree_node.project
            new_project = selected_node.git_project_tree_node.project
            if old_project != new_project:
                need_to_refresh = True

        self.selected_node = selected_node

        if need_to_refresh:
            self.refreshTree()

        else:
            self.table_model.setGitProjectTreeNode( self.selected_node.git_project_tree_node )

    def selectedGitProjectTreeNode( self ):
        if self.selected_node is None:
            return None

        return self.selected_node.git_project_tree_node

class ProjectTreeNode(QtGui.QStandardItem):
    def __init__( self, model, git_project_tree_node ):
        self.model = model
        self._debug = self.model._debug

        self.git_project_tree_node = git_project_tree_node

        super().__init__( self.git_project_tree_node.name )

        for tree in sorted( self.git_project_tree_node.all_folders.values() ):
            self.appendRow( ProjectTreeNode( self.model, tree ) )

    def update( self, git_project_tree_node, indent=0 ):
        # replace the old git_project_tree_node with the new one from updateStatus()
        self.git_project_tree_node = git_project_tree_node

        self._debug( '%*sProjectTreeNode.update name %s' % (indent, '', self.text()) )

        self._debug( '%*sProjectTreeNode.update all_folders %r' % (indent, '', list( git_project_tree_node.all_folders.keys() )) )

        # do the deletes first
        all_row_names = set()
        row = 0
        while row < self.rowCount():
            item = self.child( row )
            self._debug( '%*sProjectTreeNode.update row %d child %s' % (indent, '', row, item.text()) )
            if item.text() not in git_project_tree_node.all_folders:
                self._debug( '%*sProjectTreeNode.update remove row %d child %s' % (indent, '', row, item.text()) )
                self.removeRow( row )

            else:
                # recursive update of the whole tree
                item.update( git_project_tree_node.all_folders[ item.text() ], indent+4 )

                all_row_names.add( item.text() )
                row += 1

        # do the inserts now
        all_new_row_names = set( git_project_tree_node.all_folders )

        all_to_add = all_new_row_names - all_row_names
        for name in all_to_add:
            self._debug( '%*sProjectTreeNode.update add name %s' % (indent, '', name,) )
            self.appendRow( ProjectTreeNode( self.model, self.git_project_tree_node.all_folders[ name ] ) )
