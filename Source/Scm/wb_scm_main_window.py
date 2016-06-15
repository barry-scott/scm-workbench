'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_main_window.py

    Based on code from pysvn WorkBench

'''
import sys
import os
import time
import pathlib
import difflib

# On OS X the packager missing this import
import sip

ellipsis = '…'

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_scm_version
import wb_scm_images
import wb_scm_preferences
import wb_scm_preferences_dialog

import wb_scm_tree_model

import wb_scm_table_model
import wb_scm_project_dialogs

import wb_shell_commands
import wb_logging
import wb_main_window
import wb_preferences
import wb_tracked_qwidget

class WbScmMainWindow(wb_main_window.WbMainWindow):
    def __init__( self, app, all_ui_components ):
        super().__init__( app, wb_scm_images, app._debugMainWindow )

        self.all_ui_components = all_ui_components
        for scm_type in self.all_ui_components:
            self.all_ui_components[ scm_type ].setMainWindow( self )

        # need to fix up how this gets translated
        title = T_( ' '.join( self.app.app_name_parts ) )

        win_prefs = self.app.prefs.main_window

        self.setWindowTitle( title )
        self.setWindowIcon( wb_scm_images.getQIcon( 'wb.png' ) )

        # models and views
        self.__ui_active_scm_type = None

        # short cut keys in the table view
        self.table_keys_edit = ['\r', 'e', 'E']
        self.table_keys_open = ['o', 'O']

        self.all_table_keys = []
        self.all_table_keys.extend( self.table_keys_edit )
        self.all_table_keys.extend( self.table_keys_open )

        # on Qt on macOS table will tigger selectionChanged that needs tree_model
        self.tree_model = None
        self.__setupTableViewAndModel()
        self.__setupTreeViewAndModel()

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.setupStatusBar( self.statusBar() )

        self.__setupTreeContextMenu()
        self.__setupTableContextMenu()

        geometry = win_prefs.geometry
        if geometry is not None:
            geometry = QtCore.QByteArray( geometry.encode('utf-8') )
            self.restoreGeometry( QtCore.QByteArray.fromHex( geometry ) )

        else:
            self.resize( 800, 600 )

        # the singleton commit dialog
        self.commit_dialog = None

        # window major widgets
        self.__log = wb_logging.WbLog( self.app )


        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setClearButtonEnabled( True )
        self.filter_text.setMaxLength( 256 )
        self.filter_text.setPlaceholderText( T_('Filter  by name') )

        self.filter_text.textChanged.connect( self.table_sortfilter.setFilterText )

        self.branch_text = QtWidgets.QLineEdit()
        self.branch_text.setReadOnly( True )

        self.folder_text = QtWidgets.QLineEdit()
        self.folder_text.setReadOnly( True )

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )

        self.setCentralWidget( self.v_split )

        self.h_split = QtWidgets.QSplitter( self.v_split )
        self.h_split.setOrientation( QtCore.Qt.Horizontal )

        self.v_split_table = QtWidgets.QSplitter()
        self.v_split_table.setOrientation( QtCore.Qt.Vertical )

        self.h_filter_widget = QtWidgets.QWidget( self.v_split )
        self.h_filter_layout = QtWidgets.QGridLayout()

        row = 0
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ), row, 0 )
        self.h_filter_layout.addWidget( self.filter_text, row, 1, 1, 3 )

        row += 1
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Branch:') ), row, 0 )
        self.h_filter_layout.addWidget( self.branch_text, row, 1 )

        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Path:') ), row, 2 )
        self.h_filter_layout.addWidget( self.folder_text, row, 3 )

        self.h_filter_layout.setColumnStretch( 1, 1 )
        self.h_filter_layout.setColumnStretch( 3, 2 )

        self.h_filter_widget.setLayout( self.h_filter_layout )

        self.v_table_widget = QtWidgets.QWidget( self.v_split )
        self.v_table_layout = QtWidgets.QVBoxLayout()
        self.v_table_layout.addWidget( self.h_filter_widget )
        self.v_table_layout.addWidget( self.table_view )

        self.v_table_widget.setLayout( self.v_table_layout )

        self.h_split.addWidget( self.tree_view )
        self.h_split.addWidget( self.v_table_widget )

        self.v_split.addWidget( self.h_split )
        self.v_split.addWidget( self.__log.logWidget() )

        # setup selection on the tree
        selection_model = self.tree_view.selectionModel()
        selection_model.selectionChanged.connect( self.treeSelectionChanged )

        # select the first project
        bookmark = self.app.prefs.last_position_bookmark
        if bookmark is not None:
            index = self.tree_model.indexFromBookmark( bookmark )

        else:
            index = self.tree_model.getFirstProjectIndex()

        if index is not None:
            self._debug( 'Selecting project in tree' )
            selection_model.select( index,
                        selection_model.Clear |
                        selection_model.Select |
                        selection_model.Current )

            self.tree_view.scrollTo( index )

        # timer used to wait for focus to be set after app is activated
        self.timer_update_enable_states = QtCore.QTimer()
        self.timer_update_enable_states.timeout.connect( self.updateActionEnabledStates )
        self.timer_update_enable_states.setSingleShot( True )

        # The rest of init has to be done after the widgets are rendered
        self.timer_init = QtCore.QTimer()
        self.timer_init.timeout.connect( self.completeStatupInitialisation )
        self.timer_init.setSingleShot( True )
        self.timer_init.start( 0 )

    def completeStatupInitialisation( self ):
        self._debug( 'completeStatupInitialisation()' )

        # set splitter position
        tree_size_ratio = 0.3
        width = sum( self.h_split.sizes() )
        tree_width = int( width * tree_size_ratio )
        table_width = width - tree_width
        self.h_split.setSizes( [tree_width, table_width] )

        self.updateActionEnabledStates()

        self.log.debug( 'Debug messages are enabled' )

        self.timer_init = None

    def setStatusText( self, text ):
        self.status_message.setText( text )

    def __setupTableViewAndModel( self ):
        self._debug( '__setupTableViewAndModel' )

        self.table_model = wb_scm_table_model.WbScmTableModel( self.app )

        self.table_sortfilter = wb_scm_table_model.WbScmTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )
        self.table_sortfilter.setDynamicSortFilter( False )

        self.table_sort_column = self.table_model.col_status
        self.table_sort_order = QtCore.Qt.AscendingOrder

        self.table_view = WbTableView( self, self.all_table_keys, self.tableKeyHandler )

        self._debug( '__setupTableViewAndModel view a' )

        # setModel triggers a selectionChanged event
        self.table_view.setModel( self.table_sortfilter )

        self._debug( '__setupTableViewAndModel view b' )

        # allow Tab/Shift-Tab to move between tree/filter/table and log widgets
        self.table_view.setTabKeyNavigation( False )

        # set sort params
        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )
        # and enable to apply
        self.table_view.setSortingEnabled( True )

        # always select a whole row
        self.table_view.setSelectionBehavior( self.table_view.SelectRows )
        self.table_view.doubleClicked.connect( self.tableDoubleClicked )

        # connect up signals
        self.table_view.horizontalHeader().sectionClicked.connect( self.tableHeaderClicked )
        self.table_view.customContextMenuRequested.connect( self.tableContextMenu )
        self.table_view.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

        # size columns
        char_width = 10
        self.table_view.setColumnWidth( self.table_model.col_staged, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_status, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_name, char_width*32 )
        self.table_view.setColumnWidth( self.table_model.col_date, char_width*16 )
        self.table_view.setColumnWidth( self.table_model.col_type, char_width*6 )

        self._debug( '__setupTableViewAndModel Done' )

    def __setupTreeViewAndModel( self ):
        self._debug( '__setupTreeViewAndModel' )

        self.tree_model = wb_scm_tree_model.WbScmTreeModel( self.app, self.table_model )

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel( self.tree_model )
        self.tree_view.setExpandsOnDoubleClick( True )

        # connect up signals
        self.tree_view.customContextMenuRequested.connect( self.treeContextMenu )
        self.tree_view.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

    def updateTableView( self ):
        # load in the latest status
        self.tree_model.refreshTree()

        # sort filter is now invalid
        self.table_sortfilter.invalidate()

        # enabled states will have changed
        self.updateActionEnabledStates()

    def updateActionEnabledStates( self ):
        # can be called during __init__ on macOS version
        if self.tree_model is None:
            return

        self.updateEnableStates()

        if self.commit_dialog is not None:
            scm_project = self._treeSelectedScmProject()
            self.commit_dialog.setStatus(
                    scm_project.getReportStagedFiles(),
                    scm_project.getReportUntrackedFiles() )

    def setupMenuBar( self, mb ):
        # --- setup common menus
        m = mb.addMenu( T_('&File') )
        self._addMenu( m, T_('&Preferences…'), self.appActionPreferences, role=QtWidgets.QAction.PreferencesRole )
        self._addMenu( m, T_('E&xit'), self.close, role=QtWidgets.QAction.QuitRole )

        m = mb.addMenu( T_('&View') )
        self._addMenu( m, T_('Show Controlled files'), self.table_sortfilter.setShowControllerFiles, checker=self.checkerShowControllerFiles )
        self._addMenu( m, T_('Show Uncontrolled files'), self.table_sortfilter.setShowUncontrolledFiles, checker=self.checkerShowUncontrolledFiles )
        self._addMenu( m, T_('Show Ignored files'), self.table_sortfilter.setShowIgnoredFiles, checker=self.checkerShowIgnoredFiles )
        self._addMenu( m, T_('Show Only changed files'), self.table_sortfilter.setShowOnlyChangedFiles, checker=self.checkerShowOnlyChangedFiles )

        m = mb.addMenu( T_('F&older Actions') )
        self._addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        m = mb.addMenu( T_('File &Actions') )
        self._addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        # --- setup scm_type specific menus
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupMenuBar for %r' % (scm_type,) )
            self.all_ui_components[ scm_type ].setupMenuBar( mb, self._addMenu )

        # --- setup menus less used common menus
        m = mb.addMenu( T_('&Project') )
        self._addMenu( m, T_('Add…'), self.projectActionAdd )
        self._addMenu( m, T_('Settings…'), self.projectActionSettings, self.enablerIsProject )
        self._addMenu( m, T_('Delete'), self.projectActionDelete, self.enablerIsProject )

        m = mb.addMenu( T_('&Help' ) )
        self._addMenu( m, T_("&About…"), self.appActionAbout, role=QtWidgets.QAction.AboutRole )

    def __setupTreeContextMenu( self ):
        self._debug( '__setupTreeContextMenu' )
        # --- setup scm_type specific menu
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupTreeContextMenu for %r' % (scm_type,) )

            m = QtWidgets.QMenu( self )
            m.addSection( T_('Folder Actions') )
            self._addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
            self._addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

            self.all_ui_components[ scm_type ].setupTreeContextMenu( m, self._addMenu )

    def __setupTableContextMenu( self ):
        self._debug( '__setupTableContextMenu' )

        # --- setup scm_type specific menu
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupTableContextMenu for %r' % (scm_type,) )

            m = QtWidgets.QMenu( self )

            m.addSection( T_('File Actions') )
            self._addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
            self._addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

            self.all_ui_components[ scm_type ].setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup common toolbars
        t = self.tool_bar_tree = self._addToolBar( T_('tree') )
        self._addTool( t, T_('Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addTool( t, T_('File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        t = self.tool_bar_table = self._addToolBar( T_('table') )
        self._addTool( t, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self._addTool( t, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )


        # --- setup scm_type specific tool bars
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupToolBar for %r' % (scm_type,) )
            self.all_ui_components[ scm_type ].setupToolBar( self._addToolBar, self._addTool )

    def setupStatusBar( self, s ):
        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerFolderExists( self, cache ):
        key = 'enablerFolderExists'
        if key not in cache:
            cache[ key ] = self._treeSelectedAbsoluteFolder()

        return cache[ key ] is not None

    def enablerIsProject( self, cache ):
        key = 'enablerIsProject'
        if key not in cache:
            cache[ key ] = self._treeSelectedRelativeFolder() == pathlib.Path( '.' )

        return cache[ key ]

    def enablerFilesExists( self, cache ):
        key = 'enablerFilesExists'
        if key not in cache:
            cache[ key ] = self._tableSelectedExistingFiles()

        return len( cache[ key ] ) > 0

    def _enablerFocusWidget( self, cache ):
        key = '_enablerFocusWidget'
        if key not in cache:
            if self.tree_view.hasFocus():
                cache[ key ] = 'tree'

            elif( self.table_view.hasFocus()
            or self.filter_text.hasFocus() ):
                cache[ key ] = 'table'

            else:
                cache[ key ] = None

        return cache[ key ]

    def _enablerTableSelectedStatus( self, cache ):
        key = '_enablerTableSelectedStatus'
        if key not in cache:
            cache[ key ] = self._tableSelectedStatus()

        return cache[ key ]


    #------------------------------------------------------------
    #
    #   Event handlers
    #
    #------------------------------------------------------------
    def appActiveHandler( self ):
        self._debug( 'appActiveHandler()' )

        # update the selected projects data
        self.tree_model.refreshTree()

        # sort filter is now invalid
        self.table_sortfilter.invalidate()

        # enabled states will have changed
        self.timer_update_enable_states.start( 0 )

    #------------------------------------------------------------
    #
    # app actions
    #
    #------------------------------------------------------------
    def appActionPreferences( self ):
        pref_dialog = wb_scm_preferences_dialog.WbScmPreferencesDialog( self.app, self )
        if pref_dialog.exec_():
            pref_dialog.savePreferences()
            self.app.writePreferences()

    def appActionAbout( self ):
        from PyQt5 import Qt
        all_about_info = []
        all_about_info.append( "%s %d.%d.%d-%d" %
                                (' '.join( self.app.app_name_parts )
                                ,wb_scm_version.major, wb_scm_version.minor
                                ,wb_scm_version.patch, wb_scm_version.build) )
        all_about_info.append( 'Python %d.%d.%d %s %d' %
                                (sys.version_info.major
                                ,sys.version_info.minor
                                ,sys.version_info.micro
                                ,sys.version_info.releaselevel
                                ,sys.version_info.serial) )
        all_about_info.append( 'PyQt %s, Qt %s' % (Qt.PYQT_VERSION_STR, QtCore.QT_VERSION_STR) )
        all_about_info.append( T_('Copyright Barry Scott (c) 2016-%s. All rights reserved') % (wb_scm_version.year,) )

        QtWidgets.QMessageBox.information( self,
            T_('About %s') % (' '.join( self.app.app_name_parts ),),
            '\n'.join( all_about_info ) )

    def closeEvent( self, event ):
        self.appActionClose( close=False )

    def appActionClose( self, close=True ):
        self._debug( 'appActionClose()' )
        scm_project_tree_node = self.tree_model.selectedScmProjectTreeNode()

        if scm_project_tree_node is not None:
            prefs = self.app.prefs
            bookmark = wb_preferences.Bookmark(
                        'last position',
                        scm_project_tree_node.project.projectName(),
                        scm_project_tree_node.relativePath() )

            prefs.last_position_bookmark = bookmark

        else:
            prefs.last_position_bookmark = None

        win_prefs = self.app.prefs.main_window
        win_prefs.geometry = self.saveGeometry().toHex().data()

        self.app.writePreferences()

        # close all open modeless windows
        wb_tracked_qwidget.closeAllWindows()

        if close:
            self.close()


    #------------------------------------------------------------
    #
    # project actions
    #
    #------------------------------------------------------------
    def projectActionAdd( self ):
        wiz = wb_scm_project_dialogs.WbScmAddProjectWizard( self.app )
        if wiz.exec_():
            if wiz.getScmUrl() is None:
                prefs = self.app.prefs
                project = wb_preferences.Project( wiz.name, wiz.getScmType(), wiz.getWcPath() )
                prefs.addProject( project )

                self.app.writePreferences()

                self.tree_model.addProject( project )
                index = self.tree_model.indexFromProject( project )

                selection_model = self.tree_view.selectionModel()
                selection_model.select( index,
                            selection_model.Clear |
                            selection_model.Select |
                            selection_model.Current )

                self.tree_view.scrollTo( index )

    def projectActionDelete( self ):
        project_name = self.__treeSelectedProjectName()

        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Delete Project')
        message = T_('Are you sure you wish to delete project %s') % (project_name,)

        rc = QtWidgets.QMessageBox.question( self, title, message, defaultButton=default_button )
        if rc == QtWidgets.QMessageBox.Yes:
            # remove from preferences
            self.app.prefs.delProject( project_name )
            self.app.writePreferences()

            # remove from the tree model
            self.tree_model.delProject( project_name )

            # setup on a new selection
            index = self.tree_model.getFirstProjectIndex()

            if index is not None:
                selection_model = self.tree_view.selectionModel()
                selection_model.select( index,
                            selection_model.Clear |
                            selection_model.Select |
                            selection_model.Current )

            self.tree_view.scrollTo( index )

    def projectActionSettings( self ):
        pass

    #------------------------------------------------------------
    #
    # view actions
    #
    #------------------------------------------------------------
    def checkerShowControllerFiles( self, cache ):
        key = 'checkerShowControllerFiles'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def checkerShowUncontrolledFiles( self, cache ):
        key = 'checkerShowUncontrolledFiles'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def checkerShowIgnoredFiles( self, cache ):
        key = 'checkerShowIgnoredFiles'
        if key not in cache:
            cache[ key ] = False

        return cache[ key ]

    def checkerShowOnlyChangedFiles( self, cache ):
        key = 'checkerShowOnlyChangedFiles'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def _treeSelectedScmProjectName( self ):
        # only correct if called when the top of the tree is selected
        # which is ensured by the enablers
        project_tree_node = self.tree_model.selectedScmProjectTreeNode()
        if project_tree_node is None:
            return None

        return project_tree_node.name

    def _treeSelectedScmProject( self ):
        scm_project_tree_node = self.tree_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        return scm_project_tree_node.project

    def _treeSelectedAbsoluteFolder( self ):
        scm_project_tree_node = self.tree_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        folder_path = scm_project_tree_node.absolutePath()

        if not folder_path.exists():
            return None

        return folder_path

    def _treeSelectedRelativeFolder( self ):
        scm_project_tree_node = self.tree_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        return scm_project_tree_node.relativePath()

    def treeContextMenu( self, pos ):
        self._debug( 'treeContextMenu( %r )' % (pos,) )
        global_pos = self.tree_view.viewport().mapToGlobal( pos )

        if self.__ui_active_scm_type is not None:
            self.all_ui_components[ self.__ui_active_scm_type ].getTreeContextMenu().exec_( global_pos )

    def treeSelectionChanged( self, selected, deselected ):
        self.tree_model.selectionChanged( selected, deselected )

        self.filter_text.clear()

        scm_project = self._treeSelectedScmProject()
        if self.__ui_active_scm_type != scm_project.scmType():
            if self.__ui_active_scm_type is not None:
                self._debug( 'treeSelectionChanged hiding UI for %s' % (self.__ui_active_scm_type,) )
                self.all_ui_components[ self.__ui_active_scm_type ].hideUiComponents()


            self._debug( 'treeSelectionChanged showing UI for %s' % (scm_project.scmType(),) )
            self.__ui_active_scm_type = scm_project.scmType()
            self.all_ui_components[ self.__ui_active_scm_type ].showUiComponents()

        if scm_project is None:
            self.branch_text.clear()

        else:
            self.branch_text.setText( scm_project.getBranchName() )

        self.updateActionEnabledStates()

        folder = self._treeSelectedAbsoluteFolder()
        if folder is None:                                                          
             self.folder_text.clear()

        else:
            try:
                # try to convert to ~ form
                folder = folder.relative_to( pathlib.Path( os.environ['HOME'] ) )
                folder = '~/%s' % (folder,)

            except ValueError:
                folder = str( folder )

            self.folder_text.setText( folder )

    def treeActionShell( self ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.CommandShell( self.app, folder_path )

    def treeActionFileBrowse( self ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.FileBrowser( self.app, folder_path )

    #------------------------------------------------------------
    #
    # table actions
    #
    #------------------------------------------------------------
    def _callTreeOrTableFunction( self, fn_tree, fn_table ):
        if self.tree_view.hasFocus():
            fn_tree()

        elif( self.table_view.hasFocus()
        or self.filter_text.hasFocus() ):
            fn_table()

        # else in logWidget so ignore

    def _tableSelectedFiles( self ):
        return [index.data( QtCore.Qt.UserRole ).name
                    for index in self.table_view.selectedIndexes()
                    if index.column() == 0]

    def _tableSelectedExistingFiles( self ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_filenames = [folder_path / name for name in self._tableSelectedFiles()]
        all_existing_filenames = [filename for filename in all_filenames if filename.exists()]
        return all_existing_filenames

    def _tableSelectedWithStatus( self, with_status, without_status ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return False

        all_names = self._tableSelectedFiles()
        if len(all_names) == 0:
            return False

        scm_project = self._treeSelectedScmProject()

        relative_folder = self._treeSelectedRelativeFolder()

        for name in all_names:
            status = scm_project.getStatus( relative_folder / name )
            if (status&with_status) == 0:
                return False

            if (status&without_status) != 0:
                return False

        return True

    def _tableSelectedStatus( self ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_names = self._tableSelectedFiles()
        if len(all_names) == 0:
            return []

        scm_project = self._treeSelectedScmProject()

        relative_folder = self._treeSelectedRelativeFolder()

        return [scm_project.getFileState( relative_folder / name ) for name in all_names]

    def _tableActionViewRepo( self, are_you_sure_function, execute_function ):
        folder_path = self._treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        all_names = self._tableSelectedFiles()
        if len(all_names) == 0:
            return
        scm_project = self._treeSelectedScmProject()

        relative_folder = self._treeSelectedRelativeFolder()

        all_filenames = [relative_folder / name for name in all_names]

        if not are_you_sure_function( all_filenames ):
            return False

        for filename in all_filenames:
            execute_function( scm_project, filename )

        return True

    def tableKeyHandler( self, key ):
        if key in self.table_keys_edit:
            self.tableActionEdit()

        elif key in self.table_keys_open:
            self.tableActionOpen()

    def tableContextMenu( self, pos ):
        self._debug( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.table_view.viewport().mapToGlobal( pos )

        if self.__ui_active_scm_type is not None:
            self.all_ui_components[ self.__ui_active_scm_type ].getTableContextMenu().exec_( global_pos )

    def tableHeaderClicked( self, column ):
        if column == self.table_sort_column:
            if self.table_sort_order == QtCore.Qt.DescendingOrder:
                self.table_sort_order = QtCore.Qt.AscendingOrder
            else:
                self.table_sort_order = QtCore.Qt.DescendingOrder

        else:
            self.table_sort_column = column
            self.table_sort_order = QtCore.Qt.AscendingOrder

        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )

    def tableDoubleClicked( self, index ):
        self.tableActionEdit()

    def tableActionOpen( self ):
        all_filenames = self._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.ShellOpen( self.app, self._treeSelectedAbsoluteFolder(), all_filenames )

    def tableActionEdit( self ):
        all_filenames = self._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.EditFile( self.app, self._treeSelectedAbsoluteFolder(), all_filenames )

class WbTableView(QtWidgets.QTableView):
    def __init__( self, main_window, all_keys, key_handler ):
        self.main_window = main_window
        self.all_keys = all_keys
        self.key_handler = key_handler

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbTableView.selectionChanged()' )

        self.main_window.updateActionEnabledStates()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def keyPressEvent( self, event ):
        text = event.text()
        if text != '' and text in self.all_keys:
            self.key_handler( text )

        else:
            super().keyPressEvent( event )

    def keyReleaseEvent( self, event ):
        text = event.text()

        if text != '' and text in self.all_keys:
            return

        else:
            super().keyReleaseEvent( event )
