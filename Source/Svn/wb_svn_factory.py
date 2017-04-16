'''
 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_factory.py

'''
import pathlib

import wb_svn_log_history_view
import wb_svn_ui_components
import wb_svn_ui_actions

import wb_scm_project_dialogs
import wb_scm_factory_abc
import wb_svn_preferences

from PyQt5 import QtWidgets
from PyQt5 import QtCore

class WbSvnFactory(wb_scm_factory_abc.WbScmFactoryABC):
    def __init__( self ):
        super().__init__()

    def scmName( self ):
        return 'svn'

    def scmPresentationShortName( self ):
        return 'SVN'

    def scmPresentationLongName( self ):
        return 'Subversion (SVN)'

    def extraLoggers( self ):
        return []

    def optionParse( self, args ):
        return False

    def extraDebugEnabled( self ):
        return False

    def setupAppDebug( self ):
        pass

    def uiComponents( self ):
        return wb_svn_ui_components.SvnMainWindowComponents( self )

    def uiActions( self ):
        return wb_svn_ui_actions.SvnMainWindowActions( self )

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return SvnProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectSvnCheckout( wizard )]

    def projectDialogInitPages( self, wizard ):
        return []

    def folderDetection( self ):
        return [('.svn', 'svn'), ('_svn', 'svn')]

    def logHistoryView( self, app, title ):
        return wb_svn_log_history_view.WbSvnLogHistoryView( app, title )

    def setupPreferences( self, scheme_nodes ):
        return wb_svn_preferences.setupPreferences( scheme_nodes )

    def getAllPreferenceTabs( self, app ):
        return wb_svn_preferences.getAllPreferenceTabs( app )

class SvnProjectSettingsDialog(wb_scm_project_dialogs.ProjectSettingsDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        self.tags_url = QtWidgets.QLineEdit()

        super().__init__( app, parent, prefs_project, scm_project )

    def scmSpecificAddRows( self ):
        info = self.scm_project.cmdInfo( pathlib.Path('.') )

        self.addRow( T_('URL:'), info['URL'] )
        self.addRow( T_('Repos root:'), info[ 'repos_root_URL' ] )

        tags_url = self.prefs_project.tags_url
        tags_url_present = tags_url is not None

        if tags_url is None:
            url_parts = info['URL'].split( '/' )

            # look for the conventional 'trunk' or 'branches' folder
            try:
                index = url_parts.index( 'trunk' )

            except ValueError:
                try:
                    index = url_parts.index( 'branches' )

                except ValueError:
                    index = -1

            if index > 0:
                url_parts[index] = 'tags'
                tags_url = '/'.join( url_parts )

            else:
                tags_url = '%s/tags' % (info[ 'repos_root_URL' ],)

        self.tags_url.setText( tags_url )
        self.tags_url.setEnabled( tags_url_present )

        self.check_tag_url = QtWidgets.QCheckBox( T_('Tag URL:') )
        self.check_tag_url.setCheckState( QtCore.Qt.Checked if tags_url_present else QtCore.Qt.Unchecked )
        self.check_tag_url.stateChanged.connect( self.tags_url.setEnabled )
        self.check_tag_url.stateChanged.connect( self.enableOkButton )

        self.addRow( self.check_tag_url, self.tags_url )

        self.tags_url.textChanged.connect( self.enableOkButton )
        self.enableOkButton()

    def scmSpecificUpdateProject( self ):
        self.prefs_project.tags_url = self.getTagsUrl()

    def getTagsUrl( self ):
        if self.check_tag_url.isChecked():
            return self.tags_url.text()
        else:
            return None

    def scmSpecificHasChanged( self ):
        return ((self.prefs_project.tags_url is not None) != self.check_tag_url.isChecked()
               or self.prefs_project.tags_url != self.getTagsUrl())

class PageAddProjectSvnCheckout(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    all_supported_schemes = ('https', 'http')

    def __init__( self, wizard ):
        super().__init__( wizard )

        self.setTitle( T_('Add Svn Project') )
        self.setSubTitle( T_('Checkout Svn repository') )

        self.grid_layout.addRow( T_('Svn Repository URL'), self.url )
        self.grid_layout.addFeedbackWidget()

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

    def validatePageScmSpecific( self ):
        pass
