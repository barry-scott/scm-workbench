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

class UpdateProject():
    pass

scm_folder_detection = [('.git', 'git'), ('.hg', 'hg'), ('.svn', 'svn'), ('_svn', 'svn')]

scm_presentation_names = {
    'git': 'Git',
     'hg': 'Murcurial (hg)',
    'svn': 'Subversion (svn)'
    }

def detectScmTypeForFolder( folder ):
    for special_folder, scm in scm_folder_detection:
        scm_folder = folder / special_folder
        try:
            if scm_folder.is_dir():
                return scm

        except PermissionError:
            # ignore folders that cannot be accessed
            pass

    return None

class WbScmAddProjectWizard(QtWidgets.QWizard):
    page_id_start = 1
    page_id_browse_existing = 2
    page_id_scan_for_existing = 3
    page_id_git_clone = 4
    page_id_name = 5

    def __init__( self, app ):
        self.app = app
        super().__init__()

        self.page_start = PageAddProjectStart()
        self.page_browse_existing = PageAddProjectBrowseExisting()
        self.page_scan_for_existing = PageAddProjectScanForExisting()
        self.page_git_clone = PageAddProjectGitClone()
        self.page_name = PageAddProjectName()

        self.setPage( self.page_id_git_clone, self.page_git_clone )
        self.setPage( self.page_id_scan_for_existing, self.page_scan_for_existing )
        self.setPage( self.page_id_start, self.page_start )
        self.setPage( self.page_id_browse_existing, self.page_browse_existing )
        self.setPage( self.page_id_name, self.page_name )

        self.all_existing_project_names = set()
        self.all_existing_project_paths = set()

        if self.app is not None:
            prefs = self.app.prefs

            for project in prefs.getAllProjects():
                self.all_existing_project_names.add( project.name )
                self.all_existing_project_paths.add( project.path )

        if sys.platform == 'win32':
            self.home = pathlib.Path( os.environ['USERPROFILE'] )

        else:
            self.home = pathlib.Path( os.environ['HOME'] )

        self.scm_type = None
        self.wc_path = None
        self.scm_url = None
        self.name = None

    def closeEvent( self, event ):
        # tell pages with resources to cleanup
        self.page_scan_for_existing.freeResources()

        super().closeEvent( event )

    def setScmUrl( self, scm_url ):
        self.scm_url = scm_url

    def getScmUrl( self ):
        return self.scm_url

    def setScmType( self, scm_type ):
        self.scm_type = scm_type

    def getScmType( self ):
        return self.scm_type

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
        file_browser.setFilter( QtCore.QDir.Hidden | QtCore.QDir.Dirs )

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

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Where is the SCM Project?') )

        self.radio_git_clone = QtWidgets.QRadioButton( T_('Clone Git repository') )
        #self.radio_hg_clone = QtWidgets.QRadioButton( T_('Clone Murcurial (hg) repository') )
        #self.radio_svn_clone = QtWidgets.QRadioButton( T_('Checkout Subversion (svn) repository') )
        self.radio_browse_existing = QtWidgets.QRadioButton( T_('Browse for existing SCM repository') )
        self.radio_scan_for_existing = QtWidgets.QRadioButton( T_('Scan for existing SCM repositories') )

        self.radio_git_clone.setChecked( True )
        self.radio_browse_existing.setChecked( False )
        self.radio_scan_for_existing.setChecked( False )

        self.grp_show = QtWidgets.QButtonGroup()
        self.grp_show.addButton( self.radio_git_clone )
        #self.grp_show.addButton( self.radio_hg_clone )
        #self.grp_show.addButton( self.radio_svn_clone )
        self.grp_show.addButton( self.radio_browse_existing )
        self.grp_show.addButton( self.radio_scan_for_existing )

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget( self.radio_git_clone )
        layout.addWidget( self.radio_browse_existing )
        layout.addWidget( self.radio_scan_for_existing )

        self.setLayout( layout )

    def nextId( self ):
        if self.radio_git_clone.isChecked():
            return WbScmAddProjectWizard.page_id_git_clone

        elif self.radio_browse_existing.isChecked():
            return WbScmAddProjectWizard.page_id_browse_existing

        elif self.radio_scan_for_existing.isChecked():
            return WbScmAddProjectWizard.page_id_scan_for_existing

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
        return WbScmAddProjectWizard.page_id_name

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
        w.setScmUrl( self.url.text().strip() )
        w.setWcPath( pathlib.Path( self.wc_path.text().strip() ) )

        return True


class PageAddProjectBrowseExisting(QtWidgets.QWizardPage):
    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add SCM Project') )
        self.setSubTitle( T_('Browse for the SCM repository working copy') )

        self.feedback = QtWidgets.QLabel( '' )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickDirectory )

        self.wc_path = QtWidgets.QLineEdit( '' )
        self.wc_path.textChanged.connect( self.__fieldsChanged )

        layout = QtWidgets.QGridLayout()
        layout.addWidget( QtWidgets.QLabel( T_('SCM Working Copy') ), 0, 0 )
        layout.addWidget( self.wc_path, 0, 1 )
        layout.addWidget( self.browse_button, 0, 2 )
        layout.addWidget( self.feedback, 1, 1 )

        self.setLayout( layout )

    def nextId( self ):
        return WbScmAddProjectWizard.page_id_name

    def __fieldsChanged( self, text ):
        self.completeChanged.emit()

    def isComplete( self ):
        path =  self.wc_path.text().strip()
        if path == '':
            return False

        path = pathlib.Path( path )

        scm_type = detectScmTypeForFolder( path )
        if scm_type is None:
            self.feedback.setText( T_('%s is not a SCM folder') % (path,) )
            return False

        if path in self.wizard().all_existing_project_paths:
            self.feedback.setText( T_('SCM folder %s has already been added') % (path,) )
            return False

        self.wizard().setScmType( scm_type )

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
    foundRepository = QtCore.pyqtSignal( [str, str] )
    scannedOneMoreFolder = QtCore.pyqtSignal()
    scanComplete = QtCore.pyqtSignal()

    def __init__( self ):
        super().__init__()

        self.setTitle( T_('Add Scm Project') )
        self.setSubTitle( T_('Pick from the available Scm repositories') )

        self.feedback = QtWidgets.QLabel( T_('Scanning for Scm repositories...') )

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

    def freeResources( self ):
        if self.thread is None:
            return

        self.thread.stop_scan = True
        self.thread.wait()
        self.thread = None

    def initializePage( self ):
        if self.wc_list.count() != 0:
            return

        self.thread = ScanForScmRepositoriesThread( self, self.wizard().home )
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

        fmt1 = S_( 'Found 1 repos.',
                  'Found %(found)d repos.',
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

    def nextId( self ):
        return WbScmAddProjectWizard.page_id_name

    def validatePage( self ):
        all_selected_items = self.wc_list.selectedItems()

        label = all_selected_items[0].text()
        scm_type, project_path = self.__all_labels_to_scm_info[ label ]
        self.wizard().setScmType( scm_type )
        self.wizard().setWcPath( project_path )

        self.freeResources()

        return True

class ScanForScmRepositoriesThread(QtCore.QThread):
    def __init__( self, wizard, home ):
        super().__init__()

        self.wizard = wizard
        self.home = home

        self.num_folders_scanned = 0
        self.num_scm_repos_found = 0

        self.stop_scan = False

        self.folders_to_scan = [self.home]

    def run( self ):
        while len(self.folders_to_scan) > 0:
            if self.stop_scan:
                return

            self.wizard.scannedOneMoreFolder.emit()

            folder = self.folders_to_scan.pop( 0 )
            self.num_folders_scanned += 1

            try:
                for path in folder.iterdir():
                    if self.stop_scan:
                        return

                    if path.is_dir():
                        scm_type = detectScmTypeForFolder( path )
                        if scm_type is not None:
                            self.num_scm_repos_found += 1
                            self.wizard.foundRepository.emit( scm_type, str(path) )

                        else:
                            self.folders_to_scan.append( path )

            except PermissionError:
                # iterdir or is_dir can raise PermissionError
                # is the folder is inaccessable
                pass

        self.wizard.scanComplete.emit()

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

    def initializePage( self ):
        scm_name = scm_presentation_names[ self.wizard().getScmType() ]
        self.setTitle( T_('Add %s Project') % (scm_name,) )

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

    def S_(s, p, n):
        if n == 1:
            return s
        else:
            return p

    app = QtWidgets.QApplication( ['foo'] )

    wiz = WbScmAddProjectWizard( None )
    if wiz.exec_():
        print( 'url', wiz.scm_url )
        print( 'name', wiz.name )
        print( 'path', wiz.wc_path )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del wiz
    del app
