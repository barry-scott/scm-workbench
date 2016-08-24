'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_factory.py

'''
import wb_git_ui_components
import wb_scm_project_dialogs

class WbGitFactory:
    def __init__( self ):
        pass

    def scmName( self ):
        return 'git'

    def scmPresentationShortName( self ):
        return 'Git'

    def scmPresentationLongName( self ):
        return 'Git'

    def uiComponents( self ):
        return wb_git_ui_components.GitMainWindowComponents()

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectGitClone( wizard )]

    def projectDialogInitPages( self, wizard ):
        return [PageAddProjectGitInit( wizard )]

    def folderDetection( self ):
        return [('.git', 'git')]

class PageAddProjectGitClone(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Clone Git repository') )

    def getScmType( self ):
        return 'git'

    def radioButtonLabel( self ):
        return T_('Clone Git repository')

class PageAddProjectGitInit(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Init Git repository') )

    def getScmType( self ):
        return 'git'

    def radioButtonLabel( self ):
        return T_('Create an empty Git repository')
