'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_project_dialogs.py

'''
import sys
import os
import pathlib
import urllib.parse

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class UpdateProject():
    pass

class WbGitAddProjectWizard(QtWidgets.QWizard):
    page_start = 1
    page_browse_existing = 2
    page_scan_for_existing = 3
    page_git_clone = 4
    page_name = 5

    def __init__( self, app ):
        self.app = app
        super().__init__()

        self.setPage( self.page_start, PageAddProjectStart() )
        self.setPage( self.page_browse_existing, PageAddProjectBrowseExisting() )
        self.setPage( self.page_scan_for_existing, PageAddProjectScanForExisting() )
        self.setPage( self.page_git_clone, PageAddProjectGitClone() )
        self.setPage( self.page_name, PageAddProjectName() )

        self.all_existing_project_names = set()
        self.all_existing_project_paths = set()

        if self.app is not None:
            prefs = self.app.prefs.getProjects()

            for project in prefs.getProjectList():
                self.all_existing_project_names.add( project.name )
                self.all_existing_project_paths.add( project.path )

        if sys.platform == 'win32':
            self.home = pathlib.Path( os.environ['USERPROFILE'] )

        else:
            self.home = pathlib.Path( os.environ['HOME'] )

        self.wc_path = None
        self.git_url = None
        self.name = None

    def setGitUrl( self, git_url ):
        self.git_url = git_url

    def getGitUrl( self ):
        return self.git_url

    def setWcPath( self, wc_path ):
        self.wc_path = wc_path

    def getWcPath( self ):
        return self.wc_path

    def setProjectName( self, name ):
        self.name = name

    def pickWcPath( self, parent ):
        path = self.wc_path
        if path == '':
            path = self.home

        path = pathlib.Path( path )
        if not path.exists():
            path = self.home

        if not path.is_dir():
            path = path.parent

        if not path.is_dir():
            path = self.home

        file_browser = QtWidgets.QFileDialog( parent )
        file_browser.setFileMode( file_browser.Directory )
        #
        # When ShowDirsOnly is True QFileDialog show a number of
        # bugs:
        # 1. folder double click edits folder name
        # 2. setDirectory does not work, always starts in $HOME
        #
        file_browser.setOption( file_browser.ShowDirsOnly, False )
        file_browser.setOption( file_browser.ReadOnly, True )
        file_browser.setViewMode( file_browser.Detail )
        file_browser.setDirectory( str( path ) )
        file_browser.selectFile( str( path ) )

        if file_browser.exec_():
            all_directories = file_browser.selectedFiles()
            assert len(all_directories) == 1
            self.wc_path = pathlib.Path( all_directories[0] )
            return True

        return False

class PageAddProjectStart(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Where is the Git Project?') )

        self.radio_git_clone = QtWidgets.QRadioButton( T_('Clone Git repository') )
        self.radio_browse_existing = QtWidgets.QRadioButton( T_('Browse for Git repository') )
        self.radio_scan_for_existing = QtWidgets.QRadioButton( T_('Scan for Git repositories') )

        self.radio_git_clone.setChecked( True )
        self.radio_browse_existing.setChecked( False )
        self.radio_scan_for_existing.setChecked( False )

        self.grp_show = QtWidgets.QButtonGroup()
        self.grp_show.addButton( self.radio_git_clone )
        self.grp_show.addButton( self.radio_browse_existing )
        self.grp_show.addButton( self.radio_scan_for_existing )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( self.radio_git_clone )
        layout.addWidget( self.radio_browse_existing )
        layout.addWidget( self.radio_scan_for_existing )

        self.setLayout( layout )

    def nextId( self ):
        if self.radio_git_clone.isChecked():
            return WbGitAddProjectWizard.page_git_clone

        elif self.radio_browse_existing.isChecked():
            return WbGitAddProjectWizard.page_browse_existing

        elif self.radio_scan_for_existing.isChecked():
            return WbGitAddProjectWizard.page_scan_for_existing

        assert False

class PageAddProjectGitClone(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Clone Git repository') )

        self.url = QtWidgets.QLineEdit( '' )
        self.url.textChanged.connect( self.__fieldsChanged )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.wc_path = QtWidgets.QLineEdit()
        self.wc_path.textChanged.connect( self.__fieldsChanged )

        self.feedback = QtWidgets.QLabel( '' )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Git URL') ), 0, 0 )
        layout.addWidget( self.url, 0, 1 )
        layout.addWidget( QtWidgets.QLabel( T_('Git Working Copy') ), 1, 0 )
        layout.addWidget( self.wc_path, 1, 1 )
        layout.addWidget( self.browse_button, 1, 2 )
        layout.addWidget( self.feedback, 2, 1 )

        self.setLayout( layout )

    def initializePage( self ):
        self.wc_path.setText( str( self.wizard().home ) )

    def nextId( self ):
        return WbGitAddProjectWizard.page_name

    def __pickDirectory( self ):
        w = self.wizard()
        w.setWcPath( self.wc_path.text() )
        if w.pickWcPath( self ):
            self.wc_path.setText( str( w.getWcPath() ) )

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        url = self.url.text().strip()
        if ':' not in url or '/' not in url:
            self.feedback.setText( T_('Fill in a Git HTTPS URL') )
            return False

        result = urllib.parse.urlparse( url )
        if result.scheme.lower() != 'https':
            self.feedback.setText( T_('Use an https: URL') )
            return False

        if result.netloc == '' or result.path == '':
            self.feedback.setText( T_('Fill in a Git HTTPS URL') )
            return False

        path =  self.wc_path.text().strip()
        if path == '':
            self.feedback.setText( T_('Fill in the Git Working Copy') )
            return False

        path = pathlib.Path( path )

        if not path.is_dir():
            self.feedback.setText( T_('%s is not a directory') % (path,) )
            return False

        is_empty = True
        for filenme in path.iterdir():
            is_empty = False
            break

        if not is_empty:
            self.feedback.setText( T_('%s is not an empty directory') % (path,) )
            return False

        self.feedback.setText( '' )
        return True

    def validatePage( self ):
        w = self.wizard()
        w.setGitUrl( self.url.text().strip() )
        w.setWcPath( pathlib.Path( self.wc_path.text().strip() ) )

        return True


class PageAddProjectBrowseExisting(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Browse for the Git repository working copy') )

        self.feedback = QtWidgets.QLabel( '' )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.wc_path = QtWidgets.QLineEdit( '' )
        self.wc_path.textChanged.connect( self.__fieldsChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Git Working Copy') ), 0, 0 )
        layout.addWidget( self.wc_path, 0, 1 )
        layout.addWidget( self.browse_button, 0, 2 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return WbGitAddProjectWizard.page_name

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        path =  self.wc_path.text().strip()
        if path == '':
            return False

        path = pathlib.Path( path )

        git_path = path / '.git'
        if not git_path.exists():
            self.feedback.setText( T_('%s is not a Git repository') % (path,) )
            return False

        if str(path) in self.wizard().all_existing_project_paths:
            self.feedback.setText( T_('Git repository %s has already been added') % (path,) )
            return False

        self.feedback.setText( '' )
        return True

    def validatePage( self ):
        self.wizard().setWcPath( pathlib.Path( self.wc_path.text().strip() ) )

        return True

    def __pickDirectory( self ):
        w = self.wizard()
        w.setWcPath( self.wc_path.text() )
        if w.pickWcPath( self ):
            self.wc_path.setText( str( w.getWcPath() ) )

class PageAddProjectScanForExisting(QtWidgets.QWizardPage):
    addGitProject = QtCore.pyqtSignal( [str] )
    scanComplete = QtCore.pyqtSignal()

    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Pick from the available Git repositories') )

        self.feedback = QtWidgets.QLabel( T_('Scanning for Git repositories...') )

        self.wc_list = QtWidgets.QListWidget()
        self.wc_list.setSelectionMode( self.wc_list.SingleSelection )
        self.wc_list.setSortingEnabled( True )
        self.wc_list.itemSelectionChanged.connect( self.__selectionChanged )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( self.feedback )
        layout.addWidget( self.wc_list )

        self.setLayout( layout )

        self.thread = None

        self.addGitProject.connect( self.__addGitProject, type=QtCore.Qt.QueuedConnection )
        self.scanComplete.connect( self.__scanCompleted, type=QtCore.Qt.QueuedConnection )

    def initializePage( self ):
        if self.wc_list.count() != 0:
            return

        self.thread = ScanForGitRepositoriesThread( self, self.wizard().home )
        self.thread.start()

    def __addGitProject( self, project_path ):
        project_path = pathlib.Path( project_path )
        if project_path not in self.wizard().all_existing_project_paths:
            QtWidgets.QListWidgetItem( str( project_path ), self.wc_list )

    def __selectionChanged( self ):
        self.completeChanged.emit()

    def __scanCompleted( self ):
        self.completeChanged.emit()
        self.feedback.setText( 'Scan Complete' )

    def isComplete( self ):
        if self.thread is None:
            return False

        if self.thread.isRunning():
            return False

        self.feedback.setText( '' )

        all_selected_items = self.wc_list.selectedItems()
        return len(all_selected_items) == 1

    def nextId( self ):
        return WbGitAddProjectWizard.page_name

    def validatePage( self ):
        all_selected_items = self.wc_list.selectedItems()

        self.wizard().setWcPath( pathlib.Path( all_selected_items[0].text() ) )

        return True

class ScanForGitRepositoriesThread(QtCore.QThread):
    def __init__( self, wizard, home ):
        self.wizard = wizard
        self.home = home
        super().__init__()

    def run( self ):
        for git_folder in self.home.glob( '**/.git' ):
            self.wizard.addGitProject.emit( str( git_folder.parent ) )

        self.wizard.scanComplete.emit()

class PageAddProjectName(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Git Project') )
        self.setSubTitle( T_('Name the project') )

        self.feedback = QtWidgets.QLabel( '' )

        self.name = QtWidgets.QLineEdit( '' )
        self.name.textChanged.connect( self.__nameChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('Project name') ), 0, 0 )
        layout.addWidget( self.name, 0, 1 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def initializePage( self ):
        wc_path = self.wizard().getWcPath()

        self.name.setText( wc_path.name )

    def __nameChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        name = self.name.text().strip()

        if name in self.wizard().all_existing_project_names:
            self.feedback.setText( T_('Project name %s is already in use') % (name,) )
            return False

        return name != ''

    def nextId( self ):
        return -1

    def validatePage( self ):
        self.wizard().setProjectName( self.name.text().strip() )

        return True

if __name__ == '__main__':
    def T_(s):
        return s

    app = QtWidgets.QApplication( ['foo'] )

    wiz = WbGitAddProjectWizard( None )
    if wiz.exec_():
        print( 'url', wiz.git_url )
        print( 'name', wiz.name )
        print( 'path', wiz.wc_path )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del wiz
    del app
