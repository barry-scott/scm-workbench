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
        self.table_model = table_model

        super().__init__()

        root = self.invisibleRootItem()

        self.all_git_projects = []

        self.selected_node = None

        for project in self.app.prefs.getProjects().getProjectList():
            git_project = wb_git_project.GitProject( project )
            git_project.update()

            self.all_git_projects.append( git_project )
            self.appendRow( ProjectTreeNode( git_project.tree ) )


    def getFirstProjectIndex( self ):
        item = self.invisibleRootItem().child( 0 )
        return self.indexFromItem( item )

    def headerData( self, section, orientation, role ):
        return None

    def selectionChanged( self, selected, deselected ):
        index = selected.indexes()[0]
        self.selected_node = self.itemFromIndex( index )
        if self.selected_node is not None:
            self.table_model.setGitProjectTreeNode( self.selected_node.git_project_tree_node )

    def selectedGitProjectTreeNode( self ):
        if self.selected_node is None:
            return None

        return self.selected_node.git_project_tree_node

class ProjectTreeNode(QtGui.QStandardItem):
    def __init__( self, git_project_tree_node ):
        self.git_project_tree_node = git_project_tree_node

        super().__init__( self.git_project_tree_node.name )

        for tree in sorted( self.git_project_tree_node.all_folders.values() ):
            self.appendRow( ProjectTreeNode( tree ) )
