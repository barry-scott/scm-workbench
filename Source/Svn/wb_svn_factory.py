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
import wb_scm_project_dialogs

import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

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

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return SvnProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectSvnCheckout()]

    def projectDialogInitPages( self, wizard ):
        return []

    def folderDetection( self ):
        return [('.svn', 'svn'), ('_svn', 'svn')]

class SvnProjectSettingsDialog(wb_scm_project_dialogs.ProjectSettingsDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        self.tags_url = QtWidgets.QLineEdit()

        super().__init__( app, parent, prefs_project, scm_project )


    def scmSpecificAddRows( self ):
        info = self.scm_project.cmdInfo( pathlib.Path('.') )

        self.addRow( T_('URL:'), info['URL'] )
        self.addRow( T_('Repos root:'), info[ 'repos_root_URL' ] )

        tags_url = self.prefs_project.tags_url
        if tags_url is None:
            url_parts = info['URL'].split( '/' )
            index = url_parts.index( 'trunk' )
            if index > 0:
                url_parts[index] = 'tags'
                tags_url = '/'.join( url_parts )

            else:
                tags_url = '%s/tags' % (info[ 'repos_root_URL' ],)

        self.tags_url.setText( tags_url )

        self.addRow( T_('Tag URL:'), self.tags_url )

        self.tags_url.textChanged.connect( self.enableOkButton )
        self.enableOkButton()

    def scmSpecificUpdateProject( self ):
        self.prefs_project.tags_url = self.tags_url.text()

    def scmSpecificEnableOkButton( self ):
        return self.prefs_project.tags_url != self.tags_url.text()

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
