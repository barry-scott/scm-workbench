'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_project_place_holder.py

'''
import pathlib

#
#   ScmProjectPlaceholder is used when the project cannot be loaded
#
class ScmProjectPlaceholder:
    def __init__( self, app, prefs_project ):
        self.app = app
        self.prefs_project = prefs_project

        self.tree = ScmProjectPlaceholderTreeNode( self, prefs_project.name, pathlib.Path( '.' ) )

    def scmType( self ):
        return self.prefs_project.scm_type

    def isNotEqual( self, other ):
        return self.projectName() != other.projectName()

    def getBranchName( self ):
        return T_('-unknown-')

    def getAllBranchNames( self ):
        return [self.getBranchName()]

    def projectName( self ):
        return self.prefs_project.name

    def projectPath( self ):
        return pathlib.Path( self.prefs_project.path )

    def updateState( self, tree_leaf ):
        pass

class ScmProjectPlaceholderTreeNode:
    def __init__( self, project, name, path ):
        self.project = project
        self.name = name
        self.__path = path

    def __repr__( self ):
        return '<ScmProjectPlaceholderTreeNode: project %r, path %s>' % (self.project, self.__path)

    def isNotEqual( self, other ):
        return (self.relativePath() != other.relativePath()
            or self.project.isNotEqual( other.project ))

    def __lt__( self, other ):
        return self.name < other.name

    def relativePath( self ):
        return self.__path

    def absolutePath( self ):
        return self.project.projectPath() / self.__path

    def getAllFolderNodes( self ):
        return []

    def getAllFolderNames( self ):
        return []

    def getAllFileNames( self ):
        return []

    def isByPath( self ):
        return False
