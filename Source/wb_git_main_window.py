'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_main_window.py

    Based on code from pysvn WorkBench

'''
import sys
import os


# On OS X the packager missing this import
import sip

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

#import be_ids
import wb_git_version
#import wb_git_images
#import wb_git_preferences_dialog

import wb_git_config

import wb_git_tree_model
import wb_git_table_model

import wb_shell_commands

class WbGitMainWindow(QtWidgets.QMainWindow):
    def __init__( self, app ):
        self.app = app
        self.log = self.app.log

        self.__all_actions = {}

        title = T_("GIT Workbench")

        win_prefs = self.app.prefs.getWindow()

        super().__init__()
        self.setWindowTitle( title )
        #self.setWindowIcon( wb_git_images.getIcon( 'wb_git.png' ) )

        self.__setupMenuBar()
        self.__setupToolBar()
        self.__setupStatusBar()

        if win_prefs.getFramePosition() is not None:
            self.move( *win_prefs.getFramePosition() )

        self.resize( *win_prefs.getFrameSize() )

        # models
        self.table_model = wb_git_table_model.WbGitTableModel( self.app )
        self.tree_model = wb_git_tree_model.WbGitTreeModel( self.app, self.table_model )

        self.table_sortfilter = wb_git_table_model.WbGitTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )

        self.table_sort_column = self.table_model.col_cache
        self.table_sort_order = QtCore.Qt.AscendingOrder

        # window major widgets
        self.log_view = QtWidgets.QLabel( 'Log view: Hello World')

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel( self.tree_model )

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel( self.table_sortfilter )
        # set sort params
        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )
        # and enable to apply
        self.table_view.setSortingEnabled( True )
        # always select a whole row
        self.table_view.setSelectionBehavior( self.table_view.SelectRows )

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter( self )
        self.v_split.setOrientation( QtCore.Qt.Vertical )
        self.setCentralWidget( self.v_split )

        self.h_split = QtWidgets.QSplitter( self.v_split )
        self.h_split.setOrientation( QtCore.Qt.Horizontal )

        self.h_split.addWidget( self.tree_view )
        self.h_split.addWidget( self.table_view )

        self.v_split.addWidget( self.h_split )
        self.v_split.addWidget( self.log_view )

        selection_model = self.tree_view.selectionModel()
        selection_model.selectionChanged.connect( self.tree_model.selectionChanged )

        # connect up signals
        self.table_view.horizontalHeader().sectionClicked.connect( self.tableHeaderClicked )
        self.table_view.customContextMenuRequested.connect( self.tableContextMenu )
        self.table_view.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

        # size columns
        char_width = 10
        self.table_view.setColumnWidth( self.table_model.col_cache, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_working, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_name, char_width*32 )
        self.table_view.setColumnWidth( self.table_model.col_date, char_width*16 )
        self.table_view.setColumnWidth( self.table_model.col_type, char_width*6 )

        # select the first project
        index = self.tree_model.getFirstProjectIndex()

        selection_model = self.tree_view.selectionModel()
        selection_model.select( index,
                    selection_model.Clear |
                    selection_model.Select |
                    selection_model.Current )

        # The rest of init has to be done after the widgets are rendered
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect( self.completeStatupInitialisation )
        self.timer.setSingleShot( True )
        self.timer.start( 0 )

    def completeStatupInitialisation( self ):
        # set splitter position
        tree_size_ratio = 0.3
        width = sum( self.h_split.sizes() )
        tree_width = int( width * tree_size_ratio )
        table_width = width - tree_width
        self.h_split.setSizes( [tree_width, table_width] )

    def __setupMenuBar( self ):
        mb = self.menuBar()

        menu_file = mb.addMenu( T_('&File') )
        act_exit = menu_file.addAction( T_('E&xit') )
        act_exit.triggered.connect( self.appActionClose )

        menu_help = mb.addMenu( T_('&Help' ) )
        act = menu_help.addAction( T_("&About...") )
        act.triggered.connect( self.appActionAbout )

    def __setupToolBar( self ):
        style = self.style()

        self.tool_bar_tree = self.addToolBar( T_('tree') )
        self.act_shell = self.tool_bar_tree.addAction( T_('Shell') )
        self.act_shell.triggered.connect( self.treeActionShell )

        self.act_file_browser = self.tool_bar_tree.addAction( 
            style.standardIcon( QtWidgets.QStyle.SP_DirOpenIcon ),
            T_('File Browser') )
        self.act_file_browser.triggered.connect( self.treeActionFileBrowse )

        self.tool_bar_table = self.addToolBar( T_('table') )
        self.act_edit = self.tool_bar_table.addAction( T_('Edit') )
        self.act_edit.triggered.connect( self.tableActionEdit )

        self.act_open = self.tool_bar_table.addAction( T_('Open') )
        self.act_open.triggered.connect( self.tableActionOpen )

    def __setupStatusBar( self ):
        s = self.statusBar()

        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

    #------------------------------------------------------------
    #
    #   Event handlers
    #
    #------------------------------------------------------------
    def tableContextMenu( self, pos ):
        selection_model = self.table_view.selectionModel()
        print( [(index.row(), index.column()) for index in selection_model.selectedRows()] )

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

    def moveEvent( self, event ):
        self.app.prefs.getWindow().setFramePosition( event.pos().x(), event.pos().y() )

    def resizeEvent( self, event ):
        self.app.prefs.getWindow().setFrameSize( event.size().width(), event.size().height() )

    def closeEvent( self, event ):
        self.app.writePreferences()

    def appActiveHandler( self ):
        # update the selected projects data
        self.tree_model.appActiveHandler()

    #------------------------------------------------------------
    #
    # app actions
    #
    #------------------------------------------------------------
    def appActionPreferences( self ):
        pref_dialog = wb_git_preferences_dialog.PreferencesDialog( self, self.app )
        rc = pref_dialog.exec_()
        if rc == QtWidgets.QDialog.Accepted:
            self.app.writePreferences()
            self.newPreferences()

    def appActionAbout( self ):
        from PyQt5 import Qt
        all_about_info = []
        all_about_info.append( T_("GIT Workbench %d.%d.%d-%d") %
                                (wb_git_version.major, wb_git_version.minor
                                ,wb_git_version.patch, wb_git_version.build) )
        all_about_info.append( 'Python %d.%d.%d %s %d' %
                                (sys.version_info.major
                                ,sys.version_info.minor
                                ,sys.version_info.micro
                                ,sys.version_info.releaselevel
                                ,sys.version_info.serial) )
        all_about_info.append( 'PyQt %s, Qt %s' % (Qt.PYQT_VERSION_STR, QtCore.QT_VERSION_STR) )
        all_about_info.append( T_('Copyright Barry Scott (c) 2016-%s. All rights reserved') % (wb_git_version.year,) )

        QtWidgets.QMessageBox.information( self, T_("About GIT Workbench"), '\n'.join( all_about_info ) )

    def appActionClose( self ):
        # QQQ: do shutdown actions before closing
        self.close()

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def __treeSelectedFolder( self ):
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()
        if git_project_tree_node is None:
            return None

        folder_path =  git_project_tree_node.path()

        if not folder_path.exists():
            return None

        return folder_path

    def treeActionShell( self ):
        folder_path = self.__treeSelectedFolder()
        if folder_path is None:
            return

        wb_shell_commands.CommandShell( self.app, folder_path )

    def treeActionFileBrowse( self ):
        folder_path = self.__treeSelectedFolder()
        if folder_path is None:
            return

        wb_shell_commands.FileBrowser( self.app, folder_path )

    #------------------------------------------------------------
    #
    # table actions
    #
    #------------------------------------------------------------
    def __tableSelectedFiles( self ):
        return [index.data( QtCore.Qt.UserRole ).name
                    for index in self.table_view.selectedIndexes()
                    if index.column() == 0]

    def tableActionOpen( self ):
        folder_path = self.__treeSelectedFolder()
        if folder_path is None:
            return

        all_filenames = self.__tableSelectedFiles()
        if len(all_filenames) == 0:
            return

        wb_shell_commands.ShellOpen( self.app, folder_path, [str(folder_path / name) for name in all_filenames] )

    def tableActionEdit( self ):
        folder_path = self.__treeSelectedFolder()
        if folder_path is None:
            return

        all_filenames = self.__tableSelectedFiles()
        if len(all_filenames) == 0:
            return

        wb_shell_commands.EditFile( self.app, folder_path, [str(folder_path / name) for name in all_filenames] )
