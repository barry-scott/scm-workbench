'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_project_dialogs.py

'''
import sys
import os
import pathlib
import urllib.parse

from PyQt5 import QtWidgets
from PyQt5 import QtGui
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

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 50*em )

        # ------------------------------------------------------------
        self.page_id_start = 1
        self.page_id_browse_existing = 2
        self.page_id_scan_for_existing = 3

        self.page_id_folder = 4
        self.page_id_name = 5

        next_id = 6

        self.all_clone_pages = {}
        self.all_init_pages = {}

        for scm_name in sorted( self.all_factories ):
            f = self.all_factories[ scm_name ]
            for page in f.projectDialogClonePages( self ):
                self.all_clone_pages[ next_id ] = page
                next_id += 1

            for page in f.projectDialogInitPages( self ):
                self.all_init_pages[ next_id ] = page
                next_id += 1

        # needs all_clone_pages and all_init_pages
        self.page_start = PageAddProjectStart( self )

        self.page_browse_existing = PageAddProjectBrowseExisting()
        self.page_scan_for_existing = PageAddProjectScanForExisting()

        self.page_folder = PageAddProjectFolder()
        self.page_name = PageAddProjectName()

        self.setPage( self.page_id_start, self.page_start )

        self.setPage( self.page_id_scan_for_existing, self.page_scan_for_existing )
        self.setPage( self.page_id_browse_existing, self.page_browse_existing )

        self.setPage( self.page_id_folder, self.page_folder )
        self.setPage( self.page_id_name, self.page_name )

        for id_, page in sorted( self.all_clone_pages.items() ):
            self.setPage( id_, page )

        for id_, page in sorted( self.all_init_pages.items() ):
            self.setPage( id_, page )

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

    def closeEvent( self, event ):
        # tell pages with resources to cleanup
        self.page_scan_for_existing.freeResources()

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
    def __init__( self, wizard ):
        super().__init__()

        self.setTitle( T_('Add Project') )
        self.setSubTitle( T_('Where is the Project?') )

        self.radio_browse_existing = QtWidgets.QRadioButton( T_('Browse for an existing project') )
        self.radio_scan_for_existing = QtWidgets.QRadioButton( T_('Scan for existing projects') )

        self.radio_scan_for_existing.setChecked( True )
        self.radio_browse_existing.setChecked( False )

        self.grp_show = QtWidgets.QButtonGroup()
        self.grp_show.addButton( self.radio_scan_for_existing )
        self.grp_show.addButton( self.radio_browse_existing )

        self.all_clone_radio = []
        for id_, page in sorted( wizard.all_clone_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            self.all_clone_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        self.all_init_radio = []
        for id_, page in sorted( wizard.all_init_pages.items() ):
            radio = QtWidgets.QRadioButton( page.radioButtonLabel() )
            self.all_init_radio.append( (id_, radio) )
            self.grp_show.addButton( radio )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Add an existing local project'),) ) )
        layout.addWidget( self.radio_scan_for_existing )
        layout.addWidget( self.radio_browse_existing )

        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Add an external project'),) ) )
        for id_, radio in self.all_clone_radio:
            layout.addWidget( radio )

        layout.addWidget( QtWidgets.QLabel( '<b>%s</b>' % (T_('Create an empty project'),) ) )
        for id_, radio in self.all_init_radio:
            layout.addWidget( radio )

        self.setLayout( layout )

    def nextId( self ):
        w = self.wizard()

        if self.radio_browse_existing.isChecked():
            return w.page_id_browse_existing

        if self.radio_scan_for_existing.isChecked():
            return w.page_id_scan_for_existing

        for id_, radio in self.all_clone_radio + self.all_init_radio:
            if radio.isChecked():
                return id_

        assert False

#--------------------------------------------------
class PageAddProjectScmCloneBase(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.feedback = QtWidgets.QLabel( '' )

        self.grid_layout = wb_dialog_bases.WbGridLayout()
        self.setLayout( self.grid_layout )

        self.url = QtWidgets.QLineEdit( '' )
        self.url.textChanged.connect( self._fieldsChanged )

    def nextId( self ):
        return self.wizard().page_id_folder

    def _fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        if not self.isValidUrl( self.url, T_('Fill in a repository URL') ):
            return False

        if not self.isCompleteScmSpecific():
            return False

        self.feedback.setText( '' )
        return True

    def isCompleteScmSpecific( self ):
        raise NotImplementedError()

    def isValidUrl( self, url_ctrl, fill_in_msg ):
        url = url_ctrl.text().strip()

        if ':' not in url or '/' not in url:
            self.feedback.setText( fill_in_msg )
            return False

        result = urllib.parse.urlparse( url )
        scheme = result.scheme.lower()
        all_supported_schemes = self.allSupportedSchemes()
        if scheme not in all_supported_schemes:
            self.feedback.setText( T_('Scheme %(scheme)s is not supported. Use one of %(all_supported_schemes)s') %
                                    {'scheme': scheme
                                    ,'all_supported_schemes': ', '.join( all_supported_schemes )} )
            return False

        if result.netloc == '' or result.path == '':
            self.feedback.setText( fill_in_msg )
            return False

        return True

    def validatePage( self ):
        w = self.wizard()
        w.setScmType( self.getScmType() )
        w.setAction( w.action_clone )
        w.setScmUrl( self.url.text().strip() )

        self.validatePageScmSpecific()

        return True

    def validatePageScmSpecific( self ):
        raise NotImplementedError()

    def getScmType( self ):
        raise NotImplementedError()

#------------------------------------------------------------
class PageAddProjectScmInitBase(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.grid_layout = wb_dialog_bases.WbGridLayout()
        self.setLayout( self.grid_layout )

        self.project_folder = QtWidgets.QLineEdit()
        self.project_folder.textChanged.connect( self.__fieldsChanged )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.feedback = QtWidgets.QLabel( '' )

        self.grid_layout.addRow( T_('Project folder'), self.project_folder, self.browse_button )
        self.grid_layout.addRow( '', self.feedback )

    def nextId( self ):
        return self.wizard().page_id_name

    def initializePage( self ):
        self.project_folder.setText( str( self.wizard().getProjectFolder() ) )

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        if not self.isValidPath():
            return False

        return True

    def isValidPath( self ):
        path =  self.project_folder.text().strip()
        if path == '':
            self.feedback.setText( T_('Fill in the project folder') )
            return False

        path = pathlib.Path( path )

        if path.exists():
            self.feedback.setText( T_('%s already exists pick another folder name') % (path,) )
            return False

        else:
            if path.parent.exists():
                self.feedback.setText( T_('%s will be created') % (path,) )
                return True

            else:
                self.feedback.setText( T_('%s cannot be used as it does not exist') % (path.parent,) )
                return False

    def validatePage( self ):
        w = self.wizard()
        w.setScmType( self.getScmType() )
        w.setAction( w.action_init )
        w.setProjectFolder( self.project_folder.text().strip() )

        return True

    def getScmType( self ):
        raise NotImplementedError()

    def __pickDirectory( self ):
        w = self.wizard()
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

#------------------------------------------------------------
class PageAddProjectBrowseExisting(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Browse for the SCM repository working copy') )

        self.feedback = QtWidgets.QLabel( '' )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.project_folder = QtWidgets.QLineEdit( '' )
        self.project_folder.textChanged.connect( self.__fieldsChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('SCM Working Copy') ), 0, 0 )
        layout.addWidget( self.project_folder, 0, 1 )
        layout.addWidget( self.browse_button, 0, 2 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return self.wizard().page_id_name

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        path =  self.project_folder.text().strip()
        if path == '':
            return False

        w = self.wizard()

        path = pathlib.Path( path )

        scm_type = w.detectScmTypeForFolder( path )
        if scm_type is None:
            self.feedback.setText( T_('%s is not a project folder') % (path,) )
            return False

        if path in w.all_existing_project_paths:
            self.feedback.setText( T_('Project folder %s has already been added') % (path,) )
            return False

        w.setScmType( scm_type )

        self.feedback.setText( '' )
        return True

    def validatePage( self ):
        w = self.wizard()
        w.setAction( w.action_add_existing )
        w.setProjectFolder( self.project_folder.text() )

        return True

    def __pickDirectory( self ):
        w = self.wizard()
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

class PageAddProjectScanForExisting(QtWidgets.QWizardPage):
    foundRepository = QtCore.pyqtSignal( [str, str] )
    scannedOneMoreFolder = QtCore.pyqtSignal()
    scanComplete = QtCore.pyqtSignal()

    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Project') )
        self.setSubTitle( T_('Pick from the available projects') )

        self.feedback = QtWidgets.QLabel( T_('Scanning for projects...') )

        # QQQ maybe use a table to allow for SCM and PATH columns?
        self.wc_list = QtWidgets.QListWidget()
        self.wc_list.setSelectionMode( self.wc_list.SingleSelection )
        self.wc_list.setSortingEnabled( True )
        self.wc_list.itemSelectionChanged.connect( self.__selectionChanged )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( self.feedback )
        layout.addWidget( self.wc_list )

        self.setLayout( layout )

        self.thread = None

        self.foundRepository.connect( self.__foundRepository, type=QtCore.Qt.QueuedConnection )
        self.scannedOneMoreFolder.connect( self.__setFeedback, type=QtCore.Qt.QueuedConnection )
        self.scanComplete.connect( self.__scanCompleted, type=QtCore.Qt.QueuedConnection )

        self.__all_labels_to_scm_info = {}

    def nextId( self ):
        return self.wizard().page_id_name

    def freeResources( self ):
        if self.thread is None:
            return

        self.thread.stop_scan = True
        self.thread.wait()
        self.thread = None

    def initializePage( self ):
        if self.wc_list.count() != 0:
            return

        self.thread = ScanForScmRepositoriesThread( self, self.wizard(), self.wizard().project_default_parent_folder )
        self.thread.start()

    def __foundRepository( self, scm_type, project_path ):
        project_path = pathlib.Path( project_path )
        if project_path not in self.wizard().all_existing_project_paths:
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

        self.feedback.setText( '%s %s %s' % (prefix, fmt1 % args, fmt2 % args) )

    def __selectionChanged( self ):
        self.completeChanged.emit()

    def __scanCompleted( self ):
        self.completeChanged.emit()

        self.__setFeedback( complete=True )

    def isComplete( self ):
        if self.thread is None or not self.thread.isRunning():
            self.feedback.setText( '' )

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
    def __init__( self, page, wizard, project_default_parent_folder ):
        super().__init__()

        self.page = page
        self.wizard = wizard
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
                        scm_type = self.wizard.detectScmTypeForFolder( path )
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
class PageAddProjectFolder(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setSubTitle( T_('Project folder') )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.project_folder = QtWidgets.QLineEdit()
        self.project_folder.textChanged.connect( self._fieldsChanged )

        self.feedback = QtWidgets.QLabel( '' )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Project folder') ), 0, 0 )
        layout.addWidget( self.project_folder, 0, 1 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return self.wizard().page_id_name

    def _fieldsChanged( self, text ):
        self.completeChanged.emit()

    def initializePage( self ):
        w = self.wizard()
        if w.getAction() == w.action_init:
            self.project_folder.setText( str( w.getProjectFolder() ) )

        else:
            name = w.getScmUrl().split('/')[-1]
            # qqq breaks OO - factory function?
            if name.endswith( '.git' ):
                name = name[:-len('.git')]
            folder = w.getProjectFolder() / name
            self.project_folder.setText( str( folder ) )

    def isComplete( self ):
        if not self.isValidPath():
            return False

        return True

    def isValidPath( self ):
        path =  self.project_folder.text().strip()
        if path == '':
            self.feedback.setText( T_('Fill in the project folder') )
            return False

        path = pathlib.Path( path )

        if path.exists():
            self.feedback.setText( T_('%s already exists pick another folder name') % (path,) )
            return False

        else:
            if path.parent.exists():
                self.feedback.setText( T_('%s will be created') % (path,) )
                return True

            else:
                self.feedback.setText( T_('%s cannot be used as it does not exist') % (path.parent,) )
                return False

    def validatePage( self ):
        self.wizard().setProjectFolder( self.project_folder.text().strip() )

        return True

    def __pickDirectory( self ):
        w = self.wizard()
        w.setProjectFolder( self.project_folder.text() )
        if w.pickProjectFolder( self ):
            self.project_folder.setText( str( w.getProjectFolder() ) )

#------------------------------------------------------------
class PageAddProjectName(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setSubTitle( T_('Name the project') )

        self.feedback = QtWidgets.QLabel( '' )

        self.name = QtWidgets.QLineEdit( '' )
        self.name.textChanged.connect( self.__nameChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Project name') ), 0, 0 )
        layout.addWidget( self.name, 0, 1 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return -1

    def initializePage( self ):
        w = self.wizard()

        factory = w.getScmFactory()
        self.setTitle( T_('Add %s Project') % (factory.scmPresentationShortName(),) )

        project_folder = w.getProjectFolder()

        self.name.setText( project_folder.name )

    def __nameChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        name = self.name.text().strip()

        if name.lower() in self.wizard().all_existing_project_names:
            self.feedback.setText( T_('Project name %s is already in use') % (name,) )
            return False

        return name != ''

    def validatePage( self ):
        self.wizard().setProjectName( self.name.text().strip() )

        return True

#------------------------------------------------------------
class ProjectSettingsDialog(wb_dialog_bases.WbDialog):
    def __init__( self, app, parent, prefs_project, scm_project ):
        self.app = app
        self.prefs_project = prefs_project
        self.scm_project= scm_project

        self.old_project_name = prefs_project.name

        prefs = self.app.prefs

        self.all_other_existing_project_names = set()

        for prefs_project in prefs.getAllProjects():
            if self.old_project_name != prefs_project.name:
                self.all_other_existing_project_names.add( prefs_project.name.lower() )

        super().__init__( parent )

        self.name = wb_dialog_bases.WbLineEdit( self.prefs_project.name, case_blind=True, strip=True )

        f = self.app.getScmFactory( self.prefs_project.scm_type )

        self.setWindowTitle( T_('Project settings for %s') % (self.prefs_project.name,) )

        self.addNamedDivider( T_('General') )
        self.addRow( T_('Name:'), self.name )
        self.addRow( T_('SCM Type:'), f.scmPresentationLongName() )
        self.addRow( T_('Path:'), str(self.prefs_project.path) )
        self.scmSpecificAddRows()
        self.addButtons()

        self.ok_button.setEnabled( False )
        self.name.textChanged.connect( self.enableOkButton )

        em = self.app.fontMetrics().width( 'm' )
        self.setMinimumWidth( 60*em )

    def scmSpecificLineEdit( self, initial_value, case_blind=False, strip=True ):
        widget = wb_dialog_bases.WbLineEdit( initial_value, case_blind, strip )
        widget.textChanged.connect( self.enableOkButton )
        return widget

    def scmSpecificCheckBox( self, title, initial_value ):
        widget = wb_dialog_bases.WbCheckBox( title, initial_value )
        widget.stateChanged.connect( self.enableOkButton )
        return widget

    def scmSpecificAddRows( self ):
        pass

    def __nameValid( self ):
        name = self.name.text().strip().lower()
        return name != '' and name not in self.all_other_existing_project_names

    def enableOkButton( self, arg=None ):
        self.ok_button.setEnabled( self.__nameValid() and (self.name.hasChanged() or self.scmSpecificEnableOkButton()) )

    def scmSpecificEnableOkButton( self ):
        return False

    def updateProject( self ):
        prefs = self.app.prefs

        if self.name.hasChanged():
            # remove under the old name
            prefs.delProject( self.old_project_name )

            # add back in under the updated name
            self.prefs_project.name = self.name.text().strip()
            prefs.addProject( self.prefs_project )

        self.scmSpecificUpdateProject()

    def scmSpecificUpdateProject( self ):
        pass


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
