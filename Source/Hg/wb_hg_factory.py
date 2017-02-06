'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_factory.py

'''
import wb_hg_ui_components
import wb_hg_ui_actions
import wb_hg_log_history_view
import wb_hg_preferences

import wb_scm_project_dialogs
import wb_scm_factory_abc

class WbHgFactory(wb_scm_factory_abc.WbScmFactoryABC):
    def __init__( self ):
        pass

    def scmName( self ):
        return 'hg'

    def scmPresentationShortName( self ):
        return 'Hg'

    def scmPresentationLongName( self ):
        return 'Mercurial (HG)'

    def uiComponents( self ):
        return wb_hg_ui_components.HgMainWindowComponents( self )

    def uiActions( self ):
        return wb_hg_ui_actions.HgMainWindowActions( self )

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return HgProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectHgClone( wizard )]

    def projectDialogInitPages( self, wizard ):
        return [PageAddProjectHgInit( wizard )]

    def folderDetection( self ):
        return [('.hg', 'hg')]

    def logHistoryView( self, app, title ):
        return wb_hg_log_history_view.WbHgLogHistoryView( app, title )

    def setupPreferences( self, scheme_nodes ):
        return wb_hg_preferences.setupPreferences( scheme_nodes )

    def getAllPreferenceTabs( self, app ):
        return wb_hg_preferences.getAllPreferenceTabs( app )

class HgProjectSettingsDialog(wb_scm_project_dialogs.ProjectSettingsDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        super().__init__( app, parent, prefs_project, scm_project )

    def scmSpecificAddRows( self ):
        url = self.scm_project.getRemoteUrl()
        if url is None:
            url = ''

        self.addRow( T_('URL:'), url )

class PageAddProjectHgClone(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    all_supported_schemes = ('ssh', 'https', 'http')

    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Hg Project') )
        self.setSubTitle( T_('Clone Hg repository') )

        self.grid_layout.addRow( T_('Git Repository URL'), self.url )
        self.grid_layout.addRow( '', self.feedback )

    def getScmType( self ):
        return 'hg'

    def allSupportedSchemes( self ):
        return self.all_supported_schemes

    def radioButtonLabel( self ):
        return T_('Clone Murcurial (hg) repository')

    def verifyScmUrl( self ):
        # if this works we have an hg repo
        # hg identify <URL>
        return False

    def isCompleteScmSpecific( self ):
        return True

    def validatePageScmSpecific( self ):
        pass

class PageAddProjectHgInit(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Hg Project') )
        self.setSubTitle( T_('Init Hg repository') )

    def getScmType( self ):
        return 'hg'

    def radioButtonLabel( self ):
        return T_('Create an empty Murcurial (hg) repository')
