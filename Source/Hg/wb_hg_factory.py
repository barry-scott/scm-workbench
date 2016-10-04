'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_factory.py

'''
import wb_hg_ui_components
import wb_hg_log_history

import wb_scm_project_dialogs

class WbHgFactory:
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

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return wb_scm_project_dialogs.ProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectHgClone( wizard )]

    def projectDialogInitPages( self, wizard ):
        return [PageAddProjectHgInit( wizard )]

    def folderDetection( self ):
        return [('.hg', 'hg')]

    def logHistoryView( self, app, title ):
        return wb_hg_log_history.WbHgLogHistoryView( app, title )

class PageAddProjectHgClone(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    all_supported_schemes = ('ssh', 'https', 'http')

    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Hg Project') )
        self.setSubTitle( T_('Clone Hg repository') )

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

class PageAddProjectHgInit(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Hg Project') )
        self.setSubTitle( T_('Init Hg repository') )

    def getScmType( self ):
        return 'hg'

    def radioButtonLabel( self ):
        return T_('Create an empty Murcurial (hg) repository')
