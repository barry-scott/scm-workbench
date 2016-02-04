'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_main_window.py

    Based on code from git WorkBench

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

#
#   QFileSystemModel uses columns 0-3
#
class WbGitFilesystemModel(QtWidgets.QFileSystemModel):
    def __init__( self ):
        super().__init__()

    custom_column_position = 4
    custom_column_count = 1

    def columnCount( self, parent=None ):
        print( 'qqq: columnCount( %r )' % (parent,) )
        return super().columnCount( parent ) + self.custom_column_count

    def data_( self, index, role ):
        result = self._data( index, role )
        print( 'qqq: data => %r' % (result,) )

    def data( self, index, role ):
        print( 'qqq: data column %d role %d' % (index.column(), role) )
        if( index.isValid()
        and index.column() >= self.custom_column_position
        and index.column() < (self.custom_column_position + self.custom_column_count) ):
            if role == QtCore.Qt.DisplayRole:
                return 'Barry'

            elif role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignLeft

            else:
                return None

        return super().data( index, role )

    def headerData( self, section, orientantion, role ):
        print( 'headerData( %r, %r, %r )' % (section, orientantion, role) )

        if( section >= self.custom_column_position
        and section < (self.custom_column_position + self.custom_column_count) ):
            if role == QtCore.Qt.DisplayRole:
                return 'Header'

            elif role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignLeft

            else:
                return None

        elif( section >= self.custom_column_position
        and section >= (self.custom_column_position + self.custom_column_count) ):
            section += self.custom_column_count

        return super().headerData( section, orientantion, role )

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

        if win_prefs.frame_position is not None:
            self.move( win_prefs.frame_position )

        self.resize( *win_prefs.getFrameSize() )

        # window major widgets
        self.log_view = QtWidgets.QLabel( 'Hello World')

        self.tree_view = QtWidgets.QTreeView()
        self.list_view = QtWidgets.QListView()

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter( self )
        self.v_split.setOrientation( QtCore.Qt.Vertical )
        self.setCentralWidget( self.v_split )

        self.h_split = QtWidgets.QSplitter( self.v_split )
        self.h_split.setOrientation( QtCore.Qt.Horizontal )

        self.h_split.addWidget( self.tree_view )
        self.h_split.addWidget( self.list_view )

        self.v_split.addWidget( self.h_split )
        self.v_split.addWidget( self.log_view )

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath( '/user/barry/wc/git' )

        self.tree_view.setModel( self.model )
        self.tree_view.setRootIndex( self.model.index( '/user/barry/wc/git' ) )

        self.list_view.setModel( self.model )
        self.list_view.setRootIndex( self.model.index( '/user/barry/wc/git' ) )

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

    def moveEvent( self, event ):
        self.app.prefs.getWindow().frame_position = event.pos()

    def resizeEvent( self, event ):
        self.app.prefs.getWindow().frame_size = event.size()

    def onActPreferences( self ):
        pref_dialog = wb_git_preferences_dialog.PreferencesDialog( self, self.app )
        rc = pref_dialog.exec_()
        if rc == QtWidgets.QDialog.Accepted:
            self.app.writePreferences()
            self.emacs_panel.newPreferences()
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
