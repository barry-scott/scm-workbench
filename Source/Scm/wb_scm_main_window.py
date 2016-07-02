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
import wb_scm_table_view
import wb_scm_tree_model
import wb_scm_project_dialogs
import wb_scm_progress

import wb_shell_commands
import wb_logging
import wb_main_window
import wb_preferences
import wb_tracked_qwidget

class WbScmMainWindow(wb_main_window.WbMainWindow):
    def __init__( self, app, all_ui_components ):
        self.table_view = None

        super().__init__( app, wb_scm_images, app._debugMainWindow )

        # need to fix up how this gets translated
        title = T_( ' '.join( self.app.app_name_parts ) )

        win_prefs = self.app.prefs.main_window

        self.setWindowTitle( title )
        self.setWindowIcon( wb_scm_images.getQIcon( 'wb.png' ) )

        # models and views
        self.__ui_active_scm_type = None

        # on Qt on macOS table will trigger selectionChanged that needs tree_model
        self.table_view = wb_scm_table_view.WbScmTableView( self.app, self )
        self.__setupTreeViewAndModel()

        self.all_ui_components = all_ui_components
        for scm_type in self.all_ui_components:
            self.all_ui_components[ scm_type ].setMainWindow( self )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.setupStatusBar( self.statusBar() )

        self.__setupTreeContextMenu()
        self.__setupTableContextMenu()

        # tell all scm ui to hide all compoents
        for scm_type in self.all_ui_components:
            self.all_ui_components[ scm_type ].setTopWindow( self )
            self.all_ui_components[ scm_type ].hideUiComponents()

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

        self.filter_text.textChanged.connect( self.table_view.table_sortfilter.setFilterText )

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

        self.tree_view.setFocus()

        # set splitter position
        tree_size_ratio = 0.3
        width = sum( self.h_split.sizes() )
        tree_width = int( width * tree_size_ratio )
        table_width = width - tree_width
        self.h_split.setSizes( [tree_width, table_width] )

        self.updateActionEnabledStates()

        self.log.debug( 'Debug messages are enabled' )

        self.timer_init = None

    def __setupTreeViewAndModel( self ):
        self._debug( '__setupTreeViewAndModel' )

        self.tree_model = wb_scm_tree_model.WbScmTreeModel( self.app, self.table_view.table_model )

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
        self.table_view.table_sortfilter.invalidate()

        if self.commit_dialog is not None:
            self.commit_dialog.updateTableView()

        # enabled states will have changed
        self.updateActionEnabledStates()

    def updateActionEnabledStates( self ):
        # can be called during __init__ on macOS version
        if self.table_view is None or self.table_view.table_model is None:
            return

        self.updateEnableStates()

    def setupMenuBar( self, mb ):
        # --- setup common menus
        m = mb.addMenu( T_('&File') )
        self._addMenu( m, T_('&Preferences…'), self.appActionPreferences, role=QtWidgets.QAction.PreferencesRole )
        self._addMenu( m, T_('E&xit'), self.close, role=QtWidgets.QAction.QuitRole )

        m = mb.addMenu( T_('&View') )
        tv = self.table_view
        self._addMenu( m, T_('Show Controlled and Changed files'), tv.setShowControlledAndChangedFiles, checker=tv.checkerShowControlledAndChangedFiles )
        self._addMenu( m, T_('Show Controlled and Not Changed files'), tv.setShowControlledAndNotChangedFiles, checker=tv.checkerShowControlledAndNotChangedFiles )
        self._addMenu( m, T_('Show Uncontrolled files'), tv.setShowUncontrolledFiles, checker=tv.checkerShowUncontrolledFiles )
        self._addMenu( m, T_('Show Ignored files'), tv.setShowIgnoredFiles, checker=tv.checkerShowIgnoredFiles )

        m.addSeparator()

        self.diff_group = QtWidgets.QActionGroup( self )
        self.diff_group.setExclusive( True )
        self._addMenu( m, T_('Unified diff'), self.setDiffUnified, checker=self.checkerDiffUnified, group=self.diff_group )
        self._addMenu( m, T_('Side by side diff'), self.setDiffSideBySide, checker=self.checkerDiffSideBySide, group=self.diff_group )

        m = mb.addMenu( T_('F&older Actions') )
        self._addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        m = mb.addMenu( T_('File &Actions') )
        self._addMenu( m, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

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
            self._addMenu( m, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
            self._addMenu( m, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

            self.all_ui_components[ scm_type ].setupTableContextMenu( m, self._addMenu )

    def setupToolBar( self ):
        # --- setup scm_type specific tool bars
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupToolBarAtLeft for %r' % (scm_type,) )
            self.all_ui_components[ scm_type ].setupToolBarAtLeft( self._addToolBar, self._addTool )

        # --- setup common toolbars
        t = self.tool_bar_tree = self._addToolBar( T_('tree') )
        self._addTool( t, T_('Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addTool( t, T_('File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        t = self.tool_bar_table = self._addToolBar( T_('table') )
        self._addTool( t, T_('Edit'), self.table_view.tableActionEdit, self.table_view.enablerTableFilesExists, 'toolbar_images/edit.png' )
        self._addTool( t, T_('Open'), self.table_view.tableActionOpen, self.table_view.enablerTableFilesExists, 'toolbar_images/open.png' )

        # --- setup scm_type specific tool bars
        for scm_type in self.all_ui_components:
            self._debug( 'calling setupToolBarAtRight for %r' % (scm_type,) )
            self.all_ui_components[ scm_type ].setupToolBarAtRight( self._addToolBar, self._addTool )

    def setupStatusBar( self, s ):
        self.status_general = QtWidgets.QLabel()
        self.status_progress = QtWidgets.QLabel()
        self.status_action = QtWidgets.QLabel()

        self.status_progress.setFrameStyle( QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken )
        self.status_action.setFrameStyle( QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken )

        s.addWidget( self.status_general, 1 )
        s.addWidget( self.status_progress, 1 )
        s.addWidget( self.status_action, 1 )

        self.setStatusGeneral()
        self.setStatusAction()

        self.progress = wb_scm_progress.WbScmProgress( self.status_progress )

    def setStatusGeneral( self, msg=None ):
        if msg is None:
            msg = T_('Work bench')

        self.status_general.setText( msg )

    def setStatusAction( self, msg=None ):
        if msg is None:
            msg = T_('Ready')

        self.status_action.setText( msg )

    #------------------------------------------------------------
    #
    #   Accessors for main window held state
    #
    #------------------------------------------------------------
    def isScmTypeActive( self, scm_type ):
        return self.__ui_active_scm_type == scm_type

    def selectedScmProjectTreeNode( self ):
        if self.tree_model is None:
            return None

        return self.tree_model.selectedScmProjectTreeNode()

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerFolderExists( self ):
        scm_project_tree_node = self.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return False

        return scm_project_tree_node.absolutePath() is not None

    def enablerIsProject( self ):
        scm_project_tree_node = self.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return False

        return scm_project_tree_node.relativePath() == pathlib.Path( '.' )

    def scmFocusWidget( self ):
        if self.tree_view.hasFocus():
            return 'tree'

        elif( self.table_view.hasFocus()
        or self.filter_text.hasFocus() ):
            return 'table'

        else:
            return None

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
        self.table_view.table_sortfilter.invalidate()

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

        box = QtWidgets.QMessageBox( 
            QtWidgets.QMessageBox.Information,
            T_('About %s') % (' '.join( self.app.app_name_parts ),),
            '\n'.join( all_about_info ),
            QtWidgets.QMessageBox.Close,
            parent=self )
        box.exec_()

    def errorMessage( self, title, message ):
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Critical,
            title,
            message,
            QtWidgets.QMessageBox.Close,
            parent=self )
        box.exec_()

    def closeEvent( self, event ):
        self.appActionClose( close=False )

    def appActionClose( self, close=True ):
        self._debug( 'appActionClose()' )
        scm_project_tree_node = self.selectedScmProjectTreeNode()

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
        project_name = self.tree_view.selectedProject().projectName()

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
    def setDiffUnified( self ):
        self.app.prefs.view.setDiffUnified()

    def setDiffSideBySide( self ):
        self.app.prefs.view.setDiffSideBySide()

    def checkerDiffUnified( self ):
        return self.app.prefs.view.isDiffUnified()

    def checkerDiffSideBySide( self ):
        return self.app.prefs.view.isDiffSideBySide()

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def treeContextMenu( self, pos ):
        self._debug( 'treeContextMenu( %r )' % (pos,) )
        global_pos = self.tree_view.viewport().mapToGlobal( pos )

        if self.__ui_active_scm_type is not None:
            self.all_ui_components[ self.__ui_active_scm_type ].getTreeContextMenu().exec_( global_pos )

    def treeSelectionChanged( self, selected, deselected ):
        self.tree_model.selectionChanged( selected, deselected )

        self.filter_text.clear()

        scm_project = self.table_view.selectedScmProject()
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

        folder = self.table_view.selectedAbsoluteFolder()
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
        folder_path = self.table_view.selectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.CommandShell( self.app, folder_path )

    def treeActionFileBrowse( self ):
        folder_path = self.table_view.selectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.FileBrowser( self.app, folder_path )

    #------------------------------------------------------------
    #
    # table actions
    #
    #------------------------------------------------------------
    def callTreeOrTableFunction( self, fn_tree, fn_table, default=None ):
        if self.tree_view.hasFocus():
            return fn_tree()

        elif( self.table_view.hasFocus()
        or self.filter_text.hasFocus() ):
            return fn_table()

        # else in logWidget so ignore
        return default

    def tableSelectedAbsoluteFiles( self ):
        tree_node = self.selectedScmProjectTreeNode()
        root = tree_node.project.path()
        return [root / filename for filename in self.tableSelectedFiles()]
