'''
 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

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

import wb_dialog_bases

from PyQt6 import QtWidgets

all_supported_schemes = ('ssh', 'git', 'https', 'http')


class WbGitFactory(wb_scm_factory_abc.WbScmFactoryABC):
    def __init__( self ):
        super().__init__()
        self.__git_debug = False

    def scmName( self ):
        return 'git'

    def scmPresentationShortName( self ):
        return 'Git'

    def scmPresentationLongName( self ):
        return 'Git'

    def extraLoggers( self ):
        return ['git.cmd']

    def optionParse( self, args ):
        if args[1] == '--git-debug':
            self.__git_debug = True
            del args[ 1 ]
            return True

        return False

    def extraDebugEnabled( self ):
        return self.__git_debug

    def setupAppDebug( self ):
        # turn on GitPython debug as required
        import git
        import logging

        if self.__git_debug:
            git.Git.GIT_PYTHON_TRACE = 'full'
            git_log = logging.getLogger( 'git.cmd' )
            git_log.setLevel( logging.DEBUG )

        else:
            git.Git.GIT_PYTHON_TRACE = False

    def uiComponents( self ):
        return wb_git_ui_components.GitMainWindowComponents( self )

    def uiActions( self ):
        return wb_git_ui_actions.GitMainWindowActions( self )

    def projectSettingsDialog( self, app, main_window, prefs_project, scm_project ):
        return GitProjectSettingsDialog( app, main_window, prefs_project, scm_project )

    def projectDialogExistingPages( self, wizard ):
        return []

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
        remote_origin = self.scm_project.getRemote( 'origin' )
        remote_upstream = self.scm_project.getRemote( 'upstream' )
        master_branch_name = self.scm_project.getMasterBranchName()

        v = wb_dialog_bases.WbValidateUrl( all_supported_schemes,
                    T_('Fill in the origin URL') )
        self.url_origin = self.scmSpecificLineEdit( '' if remote_origin is None else remote_origin.url, validator=v )

        v = wb_dialog_bases.WbValidateUrl( all_supported_schemes,
                    T_('Fill in the upstream URL') )
        self.url_upstream = self.scmSpecificLineEdit( '' if remote_upstream is None else remote_upstream.url, validator=v )

        self.setup_upstream = self.scmSpecificCheckBox(
                T_('git remote upstream. Usually required when using a forked repository'),
                remote_upstream is not None )
        self.setup_upstream.stateChanged.connect( self.url_upstream.setEnabled )
        self.url_upstream.setEnabled( remote_upstream is not None )

        self.master_branch_check = self.scmSpecificCheckBox( T_('alternate master branch name'), master_branch_name != 'master' )
        self.master_branch_name = self.scmSpecificLineEdit( master_branch_name )
        self.master_branch_check.stateChanged.connect( self.master_branch_name.setEnabled )
        self.master_branch_name.setEnabled( master_branch_name != 'master' )

        self.addNamedDivider( 'git remote origin' )
        self.addRow( 'origin URL', self.url_origin )
        self.addRow( 'master branch', self.master_branch_check )
        self.addRow( 'branch name', self.master_branch_name )

        self.addNamedDivider( 'git remote upstream' )
        self.addRow( 'remote upstream', self.setup_upstream )
        self.addRow( 'upstream URL', self.url_upstream )

        #------------------------------------------------------------
        self.config_local = self.scm_project.configReader( 'repository' )

        value = self.config_local.get_value( 'user', 'name', '' )
        v = wb_dialog_bases.WbValidateUserName(
                        T_('Fill in the user.name') )
        self.config_local_user_name = self.scmSpecificCheckBoxLineEdit( value != '', value, validator=v )

        value = self.config_local.get_value( 'user', 'email', '' )
        v = wb_dialog_bases.WbValidateUserEmail(
                        T_('Fill in the user.email with a valid email address: user@domain') )
        self.config_local_user_email = self.scmSpecificCheckBoxLineEdit( value != '', value, validator=v )

        if self.config_local.has_option( 'pull', 'rebase' ):
            rebase = self.config_local.get_value( 'pull', 'rebase' )
        else:
            rebase = False

        self.config_local_pull_rebase = self.scmSpecificCheckBox( T_('git pull --rebase'), rebase )

        self.addNamedDivider( T_('Repository local config') )
        self.addRow( T_('user.name'), self.config_local_user_name )
        self.addRow( T_('user.email'), self.config_local_user_email )
        self.addRow( T_('pull.rebase'), self.config_local_pull_rebase )

        #------------------------------------------------------------
        self.config_global = self.scm_project.configReader( 'global' )

        self.config_global_user_name = self.scmSpecificLineEdit( self.config_global.get_value( 'user', 'name', '' ) )
        self.config_global_user_email = self.scmSpecificLineEdit( self.config_global.get_value( 'user', 'email', '' ) )

        self.addNamedDivider( T_('Git Global config') )
        self.addRow( T_('user.name'), self.config_global_user_name )
        self.addRow( T_('user.email'), self.config_global_user_email )

    def scmSpecificHasChanged( self ):
        return (self.config_local_user_name.hasChanged()
             or self.config_local_user_email.hasChanged()
             or self.config_local_pull_rebase.hasChanged()
             or self.config_global_user_name.hasChanged()
             or self.config_global_user_email.hasChanged()
             or self.url_origin.hasChanged()
             or self.setup_upstream.hasChanged()
             or self.url_upstream.hasChanged()
             or self.master_branch_check.hasChanged()
             or self.master_branch_name.hasChanged())

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
                if self.config_local_user_name.isChecked():
                    value = self.config_local_user_name.value()
                    config.set_value( 'user', 'name', value )
                else:
                    config.remove_option( 'user', 'name' )

            if self.config_local_user_email.hasChanged():
                if self.config_local_user_email.isChecked():
                    value = self.config_local_user_email.value()
                    config.set_value( 'user', 'email', value )
                else:
                    config.remove_option( 'user', 'email' )

            config.release()

        if self.url_origin.hasChanged():
            # update remote origin
            self.scm_project.cmdUpdateRemote( 'origin', self.url_origin.value() )

        if( self.config_global_user_name.hasChanged()
        or  self.config_global_user_email.hasChanged() ):
            # update global config
            config = self.scm_project.configWriter( 'global' )

            if self.config_global_user_name.hasChanged():
                value = self.config_global_user_name.value()
                if value == '':
                    config.remove_option( 'user', 'name' )
                else:
                    config.set_value( 'user', 'name', value )

            if self.config_global_user_email.hasChanged():
                value = self.config_global_user_email.value()
                if value == '':
                    config.remove_option( 'user', 'email' )
                else:
                    config.set_value( 'user', 'email', value )

            config.release()

        if self.master_branch_check.hasChanged() or self.master_branch_name.hasChanged():
            if self.master_branch_check.isChecked():
                self.scm_project.setMasterBranchName( self.master_branch_name.value() )
            else:
                self.scm_project.setMasterBranchName( 'master' )

        if self.setup_upstream.hasChanged():
            if self.setup_upstream.isChecked():
                # add remote upstream
                self.scm_project.cmdAddRemote( 'upstream', self.url_upstream.value() )

                import git
                remote = git.Remote( self.scm_project.repo(), 'upstream' )
                remote.add_url( self.url_upstream.value() )

            else:
                # delete remote upstream
                self.scm_project.cmdDeleteRemote( 'upstream' )

        elif( self.setup_upstream.isChecked()
        and self.url_upstream.hasChanged() ):
            # update remote upstream
            self.scm_project.cmdUpdateRemote( 'upstream', self.url_upstream.value() )



class PageAddProjectGitClone(wb_scm_project_dialogs.PageAddProjectScmCloneBase):
    def __init__( self, wizard ):
        super().__init__( wizard )

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Clone Git repository') )

        #------------------------------------------------------------
        v = wb_dialog_bases.WbValidateUrl( all_supported_schemes,
                    T_('Fill in the upstream URL') )
        self.url_upstream = wb_dialog_bases.WbLineEdit( '', validator=v )

        self.setup_upstream = wb_dialog_bases.WbCheckBox(
                T_('git remote upstream. Usually required when using a forked repository'),
                False )

        self.setup_upstream.stateChanged.connect( self.url_upstream.setEnabled )
        self.url_upstream.setEnabled( False )

        self.setup_upstream.stateChanged.connect( self._fieldsChanged )
        self.url_upstream.textChanged.connect( self._fieldsChanged )

        #------------------------------------------------------------
        self.pull_rebase = QtWidgets.QCheckBox( T_('git pull --rebase') )
        self.pull_rebase.setChecked( True )

        #------------------------------------------------------------
        self.grid_layout.addNamedDivider( T_('git remote origin') )
        self.grid_layout.addRow( T_('Repository URL'), self.url )

        self.grid_layout.addNamedDivider( T_('git remote upstream') )
        self.grid_layout.addRow( T_('remote upstream'), self.setup_upstream )
        self.grid_layout.addRow( T_('upstream URL'),  self.url_upstream )

        self.grid_layout.addNamedDivider( T_('git config --local') )
        self.grid_layout.addRow( T_('pull.rebase'), self.pull_rebase )

        self.grid_layout.addFeedbackWidget()

    def getScmType( self ):
        return 'git'

    def allSupportedSchemes( self ):
        return all_supported_schemes

    def radioButtonLabel( self ):
        return T_('Clone Git repository')

    def verifyScmUrl( self ):
        # if this works we have a git repo
        # git ls-remote --heads <URL>
        return False

    def validatePageScmSpecific( self ):
        if self.setup_upstream.isChecked():
            url_upstream = self.url_upstream.value()
        else:
            url_upstream = None

        pull_rebase = self.pull_rebase.isChecked()

        self.wizard().setScmSpecificState( WbGitScmSpecificState( url_upstream, pull_rebase ) )

        return True

class WbGitScmSpecificState:
    def __init__( self, upstream_url, pull_rebase ):
        self.upstream_url = upstream_url
        self.pull_rebase = pull_rebase


class PageAddProjectGitInit(wb_scm_project_dialogs.PageAddProjectScmInitBase):
    def __init__( self, wizard ):
        super().__init__( wizard )

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Init Git repository') )

    def getScmType( self ):
        return 'git'

    def radioButtonLabel( self ):
        return T_('Create an empty Git repository')
