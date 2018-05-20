'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_factory.py

'''
import wb_p4_ui_components
import wb_p4_ui_actions
import wb_p4_log_history_view
import wb_p4_preferences

import wb_scm_project_dialogs
import wb_scm_factory_abc

class WbP4Factory(wb_scm_factory_abc.WbScmFactoryABC):
    def __init__( self ):
        super().__init__()

    def scmName( self ):
        return 'p4'

    def scmPresentationShortName( self ):
        return 'P4'

    def scmPresentationLongName( self ):
        return 'Perforce (P4)'

    def optionParse( self, args ):
        return False

    def extraLoggers( self ):
        return []

    def extraDebugEnabled( self ):
        return False

    def setupAppDebug( self ):
        pass

    def uiComponents( self ):
        return wb_p4_ui_components.P4MainWindowComponents( self )

    def uiActions( self ):
        return wb_p4_ui_actions.P4MainWindowActions( self )

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return P4ProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogExistingPages( self, wizard ):
        return [PageAddProjectP4Existing( wizard )]

    def projectDialogClonePages( self, wizard ):
        return []

    def projectDialogInitPages( self, wizard ):
        return []

    def folderDetection( self ):
        return []

    def logHistoryView( self, app, title ):
        return wb_p4_log_history_view.WbP4LogHistoryView( app, title )

    def setupPreferences( self, scheme_nodes ):
        return wb_p4_preferences.setupPreferences( scheme_nodes )

    def getAllPreferenceTabs( self, app ):
        return wb_p4_preferences.getAllPreferenceTabs( app )

class P4ProjectSettingsDialog(wb_scm_project_dialogs.ProjectSettingsDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        super().__init__( app, parent, prefs_project, scm_project )

    def scmSpecificAddRows( self ):
        pass

class PageAddProjectP4Init(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__( wizard )

        self.setTitle( T_('Add P4 Project') )
        self.setSubTitle( T_('Use P4 repository') )

    def getScmType( self ):
        return 'p4'

    def radioButtonLabel( self ):
        return T_('Use an existing Perforce (P4) workspace')

    def initializePage( self ):
        client_root = p4ClientRoot()
        self.project_folder.setText( client_root )

class PageAddProjectP4Existing(wb_scm_project_dialogs.PageAddProjectScmExistingBase):
    def __init__( self, wizard ):
        super().__init__( wizard )

        self.setTitle( T_('Add P4 Project') )
        self.setSubTitle( T_('Existing P4 client') )

        self.client_root = p4ClientRoot()
        self.grid_layout.addRow( T_('P4 Client workspace'), self.client_root )

    def radioButtonLabel( self ):
        return T_('Add existing Perforce (P4) workspace')

    def getScmType( self ):
        return 'p4'

    def validatePageScmSpecific( self ):
        w = self.wizard_state
        w.setScmUrl( self.client_root )
        w.setProjectFolder( self.client_root )

def p4ClientRoot():
    import P4
    p4 = P4.P4()
    p4.connect()
    all_clients = p4.run_client('-o')
    client_root = all_clients[0]['Root']

    return client_root
