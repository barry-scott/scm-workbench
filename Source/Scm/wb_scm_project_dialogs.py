'''
 ====================================================================
 Copyright (c) 2003-2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_project_dialogs.py

'''
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtCore

import wb_dialog_bases
import wb_platform_specific
import wb_pick_path_dialogs

#------------------------------------------------------------
class WbScmAddProjectWizard(QtWidgets.QWizard):
    action_clone = 1
    action_init = 2
    action_add_existing = 3

    def __init__( self, app ):
        self.app = app
        self.all_factories = app.all_factories
        super().__init__()

        self.setWizardStyle(self.ClassicStyle)

        self.setWindowTitle( T_('Add Project Wizard - %s') % (' '.join( app.app_name_parts ),) )

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 60*em )

        #------------------------------------------------------------
        self.all_existing_project_names = set()
        self.all_existing_project_paths = set()

        if self.app is not None:
            prefs = self.app.prefs

            for project in prefs.getAllProjects():
                self.all_existing_project_names.add( project.name.lower() )
                self.all_existing_project_paths.add( project.path )

        if self.app.prefs.projects_defaults.new_projects_folder is not None:
            self.project_default_parent_folder = pathlib.Path( self.app.prefs.projects_defaults.new_projects_folder )
        else:
            self.project_default_parent_folder = wb_platform_specific.getHomeFolder()

        self.scm_type = None
        self.action = None
        self.__project_folder = None
        self.scm_url = None
        self.scm_specific_state = None
        self.__name = None

        # ------------------------------------------------------------
        self.page_id_start = 1
        self.page_id_folder = 2
        self.page_id_name = 3

        next_id = 4

        self.all_existing_pages = {}
        self.all_clone_pages = {}
        self.all_init_pages = {}

        # first the special "existing" pages
        for page in (PageAddProjectScanForExisting( self )
                    ,PageAddProjectBrowseExisting( self )):
            self.all_existing_pages[ next_id ] = page
            next_id += 1

        for scm_name in sorted( self.all_factories ):
            f = self.all_factories[ scm_name ]
            for page in f.projectDialogExistingPages( self ):
                self.all_existing_pages[ next_id ] = page
                next_id += 1

            for page in f.projectDialogClonePages( self ):
                self.all_clone_pages[ next_id ] = page
                next_id += 1

            for page in f.projectDialogInitPages( self ):
                self.all_init_pages[ next_id ] = page
                next_id += 1

        # needs all_clone_pages and all_init_pages
        self.page_start = PageAddProjectStart( self )

        self.page_folder = PageAddProjectFolder( self )
        self.page_name = PageAddProjectName( self )

        self.setPage( self.page_id_start, self.page_start )

        self.setPage( self.page_id_folder, self.page_folder )
        self.setPage( self.page_id_name, self.page_name )

        for id_, page in sorted( self.all_existing_pages.items() ):
            self.setPage( id_, page )

        for id_, page in sorted( self.all_clone_pages.items() ):
            self.setPage( id_, page )

        for id_, page in sorted( self.all_init_pages.items() ):
            self.setPage( id_, page )

    def closeEvent( self, event ):
        # tell pages with resources to cleanup
        for page in self.all_existing_pages.values():
            page.freeResources()

        for page in self.all_clone_pages.values():
            page.freeResources()

        for page in self.all_init_pages.values():
            page.freeResources()

        super().closeEvent( event )

    #------------------------------------------------------------
    def setScmUrl( self, scm_url ):
        self.scm_url = scm_url

    def getScmUrl( self ):
        return self.scm_url

    def setScmType( self, scm_type ):
        self.scm_type = scm_type

    def getScmType( self ):
        return self.scm_type

    def getScmFactory( self ):
        return self.all_factories[ self.scm_type ]

    def setAction( self, action ):
        self.action = action

    def getAction( self ):
        return self.action

    def setProjectFolder( self, project_folder ):
        if isinstance( project_folder, pathlib.Path ):
            self.__project_folder = project_folder

        else:
            self.__project_folder = pathlib.Path( project_folder )

    def getProjectFolder( self ):
        if self.__project_folder is None:
            self.setProjectFolder( self.project_default_parent_folder )

        return self.__project_folder

    def setProjectName( self, name ):
        self.__name = name

    def getProjectName( self ):
        return self.__name

    def setScmSpecificState( self, state ):
        self.scm_specific_state = state

    def getScmSpecificState( self ):
        return self.scm_specific_state

    #------------------------------------------------------------
    def pickProjectFolder( self, parent ):
        path = wb_pick_path_dialogs.pickFolder( self, self.getProjectFolder() )
        if path is not None:
            self.setProjectFolder( path )
            return True

        return False

    def detectScmTypeForFolder( self, folder ):
        scm_folder_detection = []
        for factory in self.all_factories.values():
            scm_folder_detection.extend( factory.folderDetection() )

        for special_folder, scm in scm_folder_detection:
            scm_folder = folder / special_folder
            try:
                if scm_folder.is_dir():
                    return scm

            except PermissionError:
                # ignore folders that cannot be accessed
                pass

        return None


class PageAddProjectStart(QtWidgets.QWizardPage):
    def __init__( self, wizard_state ):
        super().__init__()

        self.wizard_state = wizard_state

        self.setTitle( T_('Add Project') )
        self.setSubTitle( T_('Where is the Project?') )

        self.grp_show = QtWidgets.QButtonGroup()

        checked = True
        self.all_existing_radio = []
        for id_, page in sorted( wizard_state.all_existing_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            radio.setChecked( checked )
            checked = False
            self.all_existing_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        self.all_clone_radio = []
        for id_, page in sorted( wizard_state.all_clone_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            radio.setChecked( False )
            self.all_clone_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        self.all_init_radio = []
        for id_, page in sorted( wizard_state.all_init_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            radio.setChecked( False )
            self.all_init_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Add an existing local project'),) ) )
        for id_, radio in self.all_existing_radio:
            layout.addWidget( radio )

        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Add an external project'),) ) )
        for id_, radio in self.all_clone_radio:
            layout.addWidget( radio )

        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Create an empty project'),) ) )
        for id_, radio in self.all_init_radio:
            layout.addWidget( radio )

        self.setLayout( layout )

    def nextId( self ):
        w = self.wizard_state

        for id_, radio in self.all_existing_radio + self.all_clone_radio + self.all_init_radio:
            if radio.isChecked():
                return id_

        assert False

#--------------------------------------------------
class WbWizardPage(QtWidgets.QWizardPage):
    def __init__( self, wizard_state ):
        super().__init__()

        self.wizard_state = wizard_state

        self.grid_layout = wb_dialog_bases.WbFeedbackGridLayout()
        self.setLayout( self.grid_layout )

    def isComplete( self ):
        return self.grid_layout.isValid()

    def _fieldsChanged( self, text ):
        self.completeChanged.emit()

    def scmSpecificCheckBoxLineEdit( self, initial_enable, initial_value, case_blind=False, strip=True, validator=None ):
        widget = wb_dialog_bases.WbCheckBoxLineEdit( initial_enable, initial_value, case_blind, strip, validator )
        widget.changedConnect( self._fieldsChanged )
        return widget

    def scmSpecificLineEdit( self, initial_value, case_blind=False, strip=True, validator=None ):
        widget = wb_dialog_bases.WbLineEdit( initial_value, case_blind, strip, validator )
        widget.textChanged.connect( self._fieldsChanged )
        return widget

    def scmSpecificCheckBox( self, title, initial_value ):
        widget = wb_dialog_bases.WbCheckBox( title, initial_value )
        widget.stateChanged.connect( self._fieldsChanged )
        return widget

    def freeResources( self ):
        pass

class PageAddProjectScmExistingBase(WbWizardPage):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

    def nextId( self ):
        return self.wizard_state.page_id_name

    def validatePage( self ):
        w = self.wizard_state
        w.setScmType( self.getScmType() )
        w.setAction( w.action_add_existing )

        return self.validatePageScmSpecific()

    def validatePageScmSpecific( self ):
        # override must call self.wizard_state.setScmUrl( url )
        raise NotImplementedError()

    def getScmType( self ):
        raise NotImplementedError()

class PageAddProjectScmCloneBase(WbWizardPage):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        v = wb_dialog_bases.WbValidateUrl( self.allSupportedSchemes(),
                    T_('Fill in a repository URL') )
        self.url = self.scmSpecificLineEdit( '', validator=v )

    def nextId( self ):
        return self.wizard_state.page_id_folder

    def validatePage( self ):
        w = self.wizard_state
        w.setScmType( self.getScmType() )
        w.setAction( w.action_clone )
        w.setScmUrl( self.url.text().strip() )

        return self.validatePageScmSpecific()

    def validatePageScmSpecific( self ):
        return True

    def getScmType( self ):
        raise NotImplementedError()

#------------------------------------------------------------
class PageAddProjectScmInitBase(WbWizardPage):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        v = wb_dialog_bases.WbValidateNewFolder(
                    T_('Pick a folder for the project') )
        self.project_folder = self.scmSpecificLineEdit( '', validator=v )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.grid_layout.addRow( T_('Project folder'), self.project_folder, self.browse_button )
        self.grid_layout.addFeedbackWidget()

    def nextId( self ):
        return self.wizard_state.page_id_name

    def initializePage( self ):
        self.project_folder.setText( str( self.wizard_state.getProjectFolder() ) )

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def validatePage( self ):
        w = self.wizard_state
        w.setScmType( self.getScmType() )
        w.setAction( w.action_init )
        w.setProjectFolder( self.project_folder.text().strip() )

        return True

    def getScmType( self ):
        raise NotImplementedError()

    def __pickDirectory( self ):
        w = self.wizard_state
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

#------------------------------------------------------------
class WbValidateExistingProjectFolder(wb_dialog_bases.WbValidateLineEditValue):
    def __init__( self, wizard_state ):
        super().__init__()

        self.wizard_state = wizard_state

    def isValid( self ):
        self.setFeedback( None )

        path =  self.line_edit_ctrl.value()
        if path == '':
            self.setFeedback( T_('Fill in the project folder') )
            return False

        path = pathlib.Path( path )

        scm_type = self.wizard_state.detectScmTypeForFolder( path )
        if scm_type is None:
            self.setFeedback( T_('%s is not a project folder') % (path,) )
            return False

        if path in self.wizard_state.all_existing_project_paths:
            self.setFeedback( T_('Project folder %s has already been added') % (path,) )
            return False

        return True

class PageAddProjectBrowseExisting(PageAddProjectScmExistingBase):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Browse for the SCM project folder') )

        v = WbValidateExistingProjectFolder( self.wizard_state )
        self.project_folder = self.scmSpecificLineEdit( '', validator=v )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.grid_layout.addRow( T_('Project folder'), self.project_folder, self.browse_button )
        self.grid_layout.addFeedbackWidget()

    def radioButtonLabel( self ):
        return T_('Browse for an existing project')

    def nextId( self ):
        return self.wizard_state.page_id_name

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def validatePage( self ):
        w = self.wizard_state
        w.setAction( w.action_add_existing )

        path = self.project_folder.value()
        w.setProjectFolder( path )

        w.setScmType( w.detectScmTypeForFolder( pathlib.Path( path ) ) )

        return True

    def __pickDirectory( self ):
        w = self.wizard_state
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

class PageAddProjectScanForExisting(PageAddProjectScmExistingBase):
    foundRepository = QtCore.pyqtSignal( [str, str] )
    scannedOneMoreFolder = QtCore.pyqtSignal()
    scanComplete = QtCore.pyqtSignal()

    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        self.setTitle( T_('Add Project') )
        self.setSubTitle( T_('Pick from the available projects') )

        self.scan_progress = QtWidgets.QLabel( T_('Scanning for projects...') )

        # QQQ maybe use a table to allow for SCM and PATH columns?
        self.wc_list = QtWidgets.QListWidget()
        self.wc_list.setSelectionMode( self.wc_list.SingleSelection )
        self.wc_list.setSortingEnabled( True )
        self.wc_list.itemSelectionChanged.connect( self.__selectionChanged )

        self.grid_layout.addRow( None, self.scan_progress )
        self.grid_layout.addRow( None, self.wc_list )

        self.thread = None

        self.foundRepository.connect( self.__foundRepository, type=QtCore.Qt.QueuedConnection )
        self.scannedOneMoreFolder.connect( self.__setFeedback, type=QtCore.Qt.QueuedConnection )
        self.scanComplete.connect( self.__scanCompleted, type=QtCore.Qt.QueuedConnection )

        self.__all_labels_to_scm_info = {}

    def radioButtonLabel( self ):
        return T_('Scan for existing projects')

    def nextId( self ):
        return self.wizard_state.page_id_name

    def freeResources( self ):
        if self.thread is None:
            return

        self.thread.stop_scan = True
        self.thread.wait()
        self.thread = None

    def initializePage( self ):
        if self.wc_list.count() != 0:
            return

        self.thread = ScanForScmRepositoriesThread( self, self.wizard_state, self.wizard_state.project_default_parent_folder )
        self.thread.start()

    def __foundRepository( self, scm_type, project_path ):
        project_path = pathlib.Path( project_path )
        if project_path not in self.wizard_state.all_existing_project_paths:
            label = '%s: %s' % (scm_type, project_path)
            self.__all_labels_to_scm_info[ label ] = (scm_type, project_path)
            QtWidgets.QListWidgetItem( label, self.wc_list )

        self.__setFeedback()

    def __setFeedback( self, complete=False ):
        if self.thread is None:
            return

        if self.thread.stop_scan:
            prefix = T_('Scan interrupted.')

        elif complete:
            prefix = T_('Scan completed.')

        else:
            prefix = T_('Scanning.')

        args = {'scanned': self.thread.num_folders_scanned
               ,'found': self.thread.num_scm_repos_found}

        fmt1 = S_( 'Found 1 project.',
                  'Found %(found)d projects.',
                 self.thread.num_scm_repos_found )

        fmt2 = S_( 'Scanned 1 folder.',
                  'Scanned %(scanned)d folders.',
                 self.thread.num_folders_scanned )

        self.scan_progress.setText( '%s %s %s' % (prefix, fmt1 % args, fmt2 % args) )

    def __selectionChanged( self ):
        self.completeChanged.emit()

    def __scanCompleted( self ):
        self.completeChanged.emit()

        self.__setFeedback( complete=True )

    def isComplete( self ):
        if self.thread is None or not self.thread.isRunning():
            self.scan_progress.setText( '' )

        all_selected_items = self.wc_list.selectedItems()
        return len(all_selected_items) == 1

    def validatePage( self ):
        all_selected_items = self.wc_list.selectedItems()

        label = all_selected_items[0].text()
        scm_type, project_path = self.__all_labels_to_scm_info[ label ]
        w = self.wizard()
        w.setScmType( scm_type )
        w.setAction( w.action_add_existing )
        w.setProjectFolder( project_path )

        self.freeResources()

        return True

class ScanForScmRepositoriesThread(QtCore.QThread):
    def __init__( self, page, wizard_state, project_default_parent_folder ):
        super().__init__()

        self.page = page
        self.wizard_state = wizard_state
        self.project_default_parent_folder = project_default_parent_folder

        self.num_folders_scanned = 0
        self.num_scm_repos_found = 0

        self.stop_scan = False

        self.folders_to_scan = [self.project_default_parent_folder]

    def run( self ):
        while len(self.folders_to_scan) > 0:
            if self.stop_scan:
                return

            self.page.scannedOneMoreFolder.emit()

            folder = self.folders_to_scan.pop( 0 )
            self.num_folders_scanned += 1

            try:
                for path in folder.iterdir():
                    if self.stop_scan:
                        return

                    if path.is_dir():
                        scm_type = self.wizard_state.detectScmTypeForFolder( path )
                        if scm_type is not None:
                            self.num_scm_repos_found += 1
                            self.page.foundRepository.emit( scm_type, str(path) )

                        else:
                            self.folders_to_scan.append( path )

            except PermissionError:
                # iterdir or is_dir can raise PermissionError
                # is the folder is inaccessable
                pass

        self.page.scanComplete.emit()

#------------------------------------------------------------
class PageAddProjectFolder(WbWizardPage):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        self.setSubTitle( T_('Project folder') )

        v = wb_dialog_bases.WbValidateNewFolder(
                    T_('Pick a folder for the new project') )
        self.project_folder = self.scmSpecificLineEdit( '', validator=v )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.grid_layout.addRow( T_('Project folder'), self.project_folder, self.browse_button )
        self.grid_layout.addFeedbackWidget()

    def nextId( self ):
        return self.wizard_state.page_id_name

    def _fieldsChanged( self, text ):
        self.completeChanged.emit()

    def initializePage( self ):
        w = self.wizard_state
        if w.getAction() == w.action_init:
            self.project_folder.setText( str( w.getProjectFolder() ) )

        else:
            name = w.getScmUrl().split('/')[-1]
            # qqq breaks OO - factory function?
            if name.endswith( '.git' ):
                name = name[:-len('.git')]
            folder = w.getProjectFolder() / name
            self.project_folder.setText( str( folder ) )

    def validatePage( self ):
        self.wizard_state.setProjectFolder( self.project_folder.text().strip() )

        return True

    def __pickDirectory( self ):
        w = self.wizard_state
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

#------------------------------------------------------------
class PageAddProjectName(WbWizardPage):
    def __init__( self, wizard_state ):
        super().__init__( wizard_state )

        self.setSubTitle( T_('Name the project') )

        v = wb_dialog_bases.WbValidateUnique( self.wizard_state.all_existing_project_names,
                    T_('Pick a name for new project that is not in use for another project') )
        self.name = self.scmSpecificLineEdit( '', validator=v )

        self.grid_layout.addRow( T_('Project name'), self.name )
        self.grid_layout.addFeedbackWidget()

    def nextId( self ):
        return -1

    def initializePage( self ):
        w = self.wizard_state

        factory = w.getScmFactory()
        self.setTitle( T_('Add %s Project') % (factory.scmPresentationShortName(),) )

        project_folder = w.getProjectFolder()

        self.name.setText( project_folder.name )

    def __nameChanged( self, text ):
        self.completeChanged.emit()

    def validatePage( self ):
        self.wizard_state.setProjectName( self.name.text().strip() )

        return True

#------------------------------------------------------------
class ProjectSettingsDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        self.app = app
        self.prefs_project = prefs_project
        self.scm_project = scm_project

        self.old_project_name = prefs_project.name

        prefs = self.app.prefs

        self.all_other_existing_project_names = set()

        for prefs_project in prefs.getAllProjects():
            if self.old_project_name != prefs_project.name:
                self.all_other_existing_project_names.add( prefs_project.name.lower() )

        super().__init__( parent )

        v = wb_dialog_bases.WbValidateUnique( self.all_other_existing_project_names,
                    T_('Enter a new project name that has not been used for another project') )
        self.name = wb_dialog_bases.WbLineEdit( self.prefs_project.name, case_blind=True, strip=True, validator=v )

        f = self.app.getScmFactory( self.prefs_project.scm_type )

        self.setWindowTitle( T_('Project settings for %s') % (self.prefs_project.name,) )

        self.addNamedDivider( T_('General') )
        self.addRow( T_('Name'), self.name )
        self.addRow( T_('SCM Type'), f.scmPresentationLongName() )
        self.addRow( T_('Path'), str(self.prefs_project.path) )
        self.scmSpecificAddRows()
        self.addFeedbackWidget()
        self.addButtons()

        self.ok_button.setEnabled( False )
        self.name.textChanged.connect( self.enableOkButton )

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 60*em )

    def scmSpecificCheckBoxLineEdit( self, initial_enable, initial_value, case_blind=False, strip=True, validator=None ):
        widget = wb_dialog_bases.WbCheckBoxLineEdit( initial_enable, initial_value, case_blind, strip, validator )
        widget.changedConnect( self.enableOkButton )
        return widget

    def scmSpecificLineEdit( self, initial_value, case_blind=False, strip=True, validator=None ):
        widget = wb_dialog_bases.WbLineEdit( initial_value, case_blind, strip, validator )
        widget.textChanged.connect( self.enableOkButton )
        return widget

    def scmSpecificCheckBox( self, title, initial_value ):
        widget = wb_dialog_bases.WbCheckBox( title, initial_value )
        widget.stateChanged.connect( self.enableOkButton )
        return widget

    def scmSpecificAddRows( self ):
        pass

    def enableOkButton( self, arg=None ):
        self.ok_button.setEnabled( self.grid_layout.isValid()
                                    and (self.name.hasChanged() or self.scmSpecificHasChanged()) )

    def scmSpecificHasChanged( self ):
        return False

    def updateProject( self ):
        prefs = self.app.prefs

        if self.name.hasChanged():
            # rename project
            prefs.renameProject( self.old_project_name, self.name.value() )

        self.scmSpecificUpdateProject()

    def scmSpecificUpdateProject( self ):
        pass

#------------------------------------------------------------


if __name__ == '__main__':
    def T_(s):
        return s

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    wiz = WbScmAddProjectWizard( None )
    if wiz.exec_():
        print( 'SCM', wiz.getScmType() )
        print( 'Action', wiz.getAction() )
        print( 'url', wiz.getScmUrl() )
        print( 'name', wiz.getProjectName() )
        print( 'path', wiz.getProjectFolder() )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del wiz
    del app
