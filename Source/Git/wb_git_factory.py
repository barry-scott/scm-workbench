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

from PyQt5 import QtWidgets

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
        return GitProjectSettingsDialog( app, main_window, prefs_project, scm_project )

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

class GitProjectSettingsDialog(wb_scm_project_dialogs.ProjectSettingsDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        super().__init__( app, parent, prefs_project, scm_project )

    def scmSpecificAddRows( self ):
        self.config_local = self.scm_project.configReader( 'repository' )

        self.config_local_user_name = self.scmSpecificLineEdit( self.config_local.get_value( 'user', 'name', '' ) )
        self.config_local_user_email = self.scmSpecificLineEdit( self.config_local.get_value( 'user', 'email', '' ) )

        if self.config_local.has_option( 'pull', 'rebase' ):
            rebase = self.config_local.get_value( 'pull', 'rebase' )
        else:
            rebase = False

        self.config_local_pull_rebase = self.scmSpecificCheckBox( T_('git pull --rebase'), rebase )

        self.addNamedDivider( T_('Repository local config') )
        self.addRow( T_('user.name'), self.config_local_user_name )
        self.addRow( T_('user.email'), self.config_local_user_email )
        self.addRow( T_('pull.rebase'), self.config_local_pull_rebase )

        self.config_global = self.scm_project.configReader( 'global' )

        self.config_global_user_name = self.scmSpecificLineEdit( self.config_global.get_value( 'user', 'name', '' ) )
        self.config_global_user_email = self.scmSpecificLineEdit( self.config_global.get_value( 'user', 'email', '' ) )

        self.addNamedDivider( T_('Git Global config') )
        self.addRow( T_('user.name'), self.config_global_user_name )
        self.addRow( T_('user.email'), self.config_global_user_email )

    def scmSpecificEnableOkButton( self ):
        if( self.config_local_user_name.hasChanged()
        or  self.config_local_user_email.hasChanged()
        or  self.config_local_pull_rebase.hasChanged()
        or  self.config_global_user_name.hasChanged()
        or  self.config_global_user_email.hasChanged() ):
            return True

        return False

    def scmSpecificUpdateProject( self ):
        if( self.config_local_user_name.hasChanged()
        or  self.config_local_user_email.hasChanged()
        or  self.config_local_pull_rebase.hasChanged() ):
            # update local config
            config = self.scm_project.configWriter( 'repository' )

            if self.config_local_pull_rebase.hasChanged():
                value = 'true' if self.config_local_pull_rebase.isChecked() else 'false'
                config.set_value( 'pull', 'rebase', value )

            if self.config_local_user_name.hasChanged():
                value = self.config_local_user_name.text().strip()
                if value == '':
                    config.remove_option( 'user', 'name' )
                else:
                    config.set_value( 'user', 'name', value )

            if self.config_local_user_email.hasChanged():
                value = self.config_local_user_email.text().strip()
                if value == '':
                    config.remove_option( 'user', 'email' )
                else:
                    config.set_value( 'user', 'email', value )

            config.release()


        if( self.config_global_user_name.hasChanged()
        or  self.config_global_user_email.hasChanged() ):
            # update global config
            config = self.scm_project.configWriter( 'global' )

            if self.config_global_user_name.hasChanged():
                value = self.config_global_user_name.text().strip()
                if value == '':
                    config.remove_option( 'user', 'name' )
                else:
                    config.set_value( 'user', 'name', value )

            if self.config_global_user_email.hasChanged():
                value = self.config_global_user_email.text().strip()
                if value == '':
                    config.remove_option( 'user', 'email' )
                else:
                    config.set_value( 'user', 'email', value )

            config.release()

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
