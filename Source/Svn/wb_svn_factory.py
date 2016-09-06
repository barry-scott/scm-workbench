'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_factory.py

'''
import wb_svn_ui_components
import wb_scm_project_dialogs

class WbSvnFactory:
    def __init__( self ):
        pass

    def scmName( self ):
        return 'svn'

    def scmPresentationShortName( self ):
        return 'SVN'

    def scmPresentationLongName( self ):
        return 'Subversion (SVN)'

    def uiComponents( self ):
        return wb_svn_ui_components.SvnMainWindowComponents()

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectSvnCheckout()]

    def projectDialogInitPages( self, wizard ):
        return []

    def folderDetection( self ):
        return [('.svn', 'svn'), ('_svn', 'svn')]

class PageAddProjectSvnCheckout(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    all_supported_schemes = ('https', 'http')

    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Svn Project') )
        self.setSubTitle( T_('Checkout Svn repository') )

    def getScmType( self ):
        return 'svn'

    def allSupportedSchemes( self ):
        return self.all_supported_schemes

    def radioButtonLabel( self ):
        return T_('Checkout Subversion (svn) repository')

    def verifyScmUrl( self ):
        # if this works we have an svn repo
        # pysvn.ls( [<url>], depth=empty? )
        return False
