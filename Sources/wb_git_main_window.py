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
        self.__setupStatusBar()

        if win_prefs.getFramePosition() is not None:
            self.move( *win_prefs.getFramePosition() )

        self.resize( *win_prefs.getFrameSize() )

        # models
        self.table_model = wb_git_table_model.WbGitTableModel( self.app )
        self.tree_model = wb_git_tree_model.WbGitTreeModel( self.app, self.table_model )

        self.table_sortfilter = wb_git_table_model.WbGitTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )

        self.table_sort_column = self.table_model.col_name
        self.table_sort_order = QtCore.Qt.AscendingOrder

        # window major widgets
        self.log_view = QtWidgets.QLabel( 'Hello World')

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel( self.tree_model )

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel( self.table_sortfilter )
        # set sort params
        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )
        # and enable to apply
        self.table_view.setSortingEnabled( True )

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

        # select the first project
        selection_model.select( self.tree_model.createIndex( 0, 0 ), selection_model.ClearAndSelect )

        # connect up signals
        self.table_view.horizontalHeader().sectionClicked.connect( self.tableHeaderClicked )

        # size columns
        char_width = 10
        self.table_view.setColumnWidth( self.table_model.col_name, char_width*32 )
        self.table_view.setColumnWidth( self.table_model.col_date, char_width*16 )
        self.table_view.setColumnWidth( self.table_model.col_type, char_width*6 )

    def __setupMenuBar( self ):
        mb = self.menuBar()

        menu_file = mb.addMenu( T_('&File') )
        act_exit = menu_file.addAction( T_('E&xit') )
        act_exit.triggered.connect( self.close )

        menu_help = mb.addMenu( T_('&Help' ) )
        act = menu_help.addAction( T_("&About...") )
        act.triggered.connect( self.onActAbout )

    def __setupToolBar( self ):
        pass

    def __setupStatusBar( self ):
        s = self.statusBar()

        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

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

    def onActPreferences( self ):
        pref_dialog = wb_git_preferences_dialog.PreferencesDialog( self, self.app )
        rc = pref_dialog.exec_()
        if rc == QtWidgets.QDialog.Accepted:
            self.app.writePreferences()
            self.newPreferences()

    def onActAbout( self ):
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
