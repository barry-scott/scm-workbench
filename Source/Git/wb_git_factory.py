'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_factory.py

'''
import wb_git_log_history_view
import wb_git_ui_components
import wb_git_ui_actions
import wb_git_preferences

import wb_scm_project_dialogs
import wb_scm_factory_abc

class WbGitFactory(wb_scm_factory_abc.WbScmFactoryABC):
    def __init__( self ):
        pass

    def scmName( self ):
        return 'git'

    def scmPresentationShortName( self ):
        return 'Git'

    def scmPresentationLongName( self ):
        return 'Git'

    def uiComponents( self ):
        return wb_git_ui_components.GitMainWindowComponents( self )

    def uiActions( self ):
        return wb_git_ui_actions.GitMainWindowActions( self )

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return wb_scm_project_dialogs.ProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogClonePages( self, wizard ):
        return [PageAddProjectGitClone( wizard )]

    def projectDialogInitPages( self, wizard ):
        return [PageAddProjectGitInit( wizard )]

    def folderDetection( self ):
        return [('.git', 'git')]

    def logHistoryView( self, app, title ):
        return wb_git_log_history_view.WbGitLogHistoryView( app, title )

    def setupPreferences( self, scheme_nodes ):
        return wb_git_preferences.setupPreferences( scheme_nodes )

    def getAllPreferenceTabs( self, app ):
        return wb_git_preferences.getAllPreferenceTabs( app )

class PageAddProjectGitClone(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    all_supported_schemes = ('ssh', 'git', 'https', 'http', 'ftps', 'ftp')

    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Clone Git repository') )

    def getScmType( self ):
        return 'git'

    def allSupportedSchemes( self ):
        return self.all_supported_schemes

    def radioButtonLabel( self ):
        return T_('Clone Git repository')

    def verifyScmUrl( self ):
        # if this works we have a git repo
        # git ls-remote --heads <URL>
        return False


class PageAddProjectGitInit(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Init Git repository') )

    def getScmType( self ):
        return 'git'

    def radioButtonLabel( self ):
        return T_('Create an empty Git repository')
