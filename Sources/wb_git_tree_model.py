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

class WbGitTreeModel(QtGui.QStandardItemModel):
    def __init__( self, app, table_model ):
        self.app = app
        self.table_model = table_model

        super().__init__()

        root = self.invisibleRootItem()

        for project in self.app.prefs.getProjects().getProjectList():
            root.appendRow( ProjectNode( project ) )

    def getFirstProjectIndex( self ):
        item = self.invisibleRootItem().child( 0 )
        return self.indexFromItem( item )

    def headerData( self, section, orientation, role ):
        return None

    def selectionChanged( self, selected, deselected ):
        index = selected.indexes()[0]
        node = self.itemFromIndex( index )
        if node is not None:
            self.table_model.setProjectAndPath( node.project, node.path )

class ProjectNode(QtGui.QStandardItem):
    def __init__( self, project, folder=None ):
        self.project = project

        if folder is not None:
            super().__init__( os.path.basename( folder ) )
            self.path = folder

        else:
            super().__init__( project.name )
            self.path = project.path

        if hasattr( os, 'scandir' ):
            for entry in os.scandir( self.path ):
                if entry.name == '.git':
                    continue

                if entry.is_dir():
                    self.appendRow( ProjectNode( self.project, os.path.join( self.path, entry.name ) ) )

        else:
            for folder in os.listdir( self.path ):
                if folder == '.git':
                    continue

                folder = os.path.join( self.path, folder )
                if os.path.isdir( folder ):
                    self.appendRow( ProjectNode( self.project, folder ) )
